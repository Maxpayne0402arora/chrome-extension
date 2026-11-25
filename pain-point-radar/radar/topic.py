"""Zoom into one topic (e.g. "Customer support", or your own keywords) and
break it down into what users actually talk about."""
from __future__ import annotations

import math
import re

import pandas as pd

from . import taxonomy as T
from .analyze import STOP_EXTRA, _compile, _momentum, _quotes


def keyword_regex(keywords):
    """'refund, money back, call back' -> regex matching any of them (word-start, any suffix)."""
    parts = [k.strip() for k in keywords if k.strip()]
    if not parts:
        return None
    return re.compile("|".join(rf"\b{re.escape(p)}\w*" for p in parts), re.I)


def topic_mask(df, topic, keywords=None):
    if keywords:
        rx = keyword_regex(keywords)
        return df["text"].map(lambda t: bool(rx.search(t)))
    return df["areas"].map(lambda l: topic in l)


def subtheme_regexes(topic, extra=None):
    subs = {k: _compile(v) for k, v in T.SUBTOPICS.get(topic, {}).items()}
    for name, kws in (extra or {}).items():
        rx = keyword_regex(kws)
        if rx:
            subs[name] = rx
    return subs


def _stop(company):
    from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS
    return list(ENGLISH_STOP_WORDS | STOP_EXTRA | set(company.lower().split()))


def _collapse(rows, key="phrase", top_n=20):
    kept = []
    for r in rows:
        if any(r[key] in k[key] or k[key] in r[key] for k in kept):
            continue
        kept.append(r)
        if len(kept) == top_n:
            break
    return kept


def most_talked_about(sub, company, top_n=20, exclude=None):
    """Phrases (2-3 words) mentioned by the most distinct users within the topic.

    Phrases that only restate the topic (e.g. "customer care" inside Customer
    support) are dropped, and phrases that come from the same reviews (e.g.
    "team called hour" / "called hour fixed") are merged so each row is a
    distinct thing users say.
    """
    from sklearn.feature_extraction.text import CountVectorizer
    if len(sub) < 5:
        return []
    vec = CountVectorizer(ngram_range=(2, 3), stop_words=_stop(company), binary=True,
                          min_df=min(3, max(2, len(sub) // 50)), token_pattern=r"(?u)\b[a-zA-Z][a-zA-Z]+\b")
    try:
        X = vec.fit_transform(sub["text"]).tocsc()
    except ValueError:
        return []
    vocab = vec.get_feature_names_out()
    counts = X.sum(axis=0).A1
    neg = (sub["label"] == "negative").to_numpy()
    order = sorted(range(len(vocab)), key=lambda i: (-counts[i], -len(vocab[i])))
    kept, kept_docs = [], []
    for i in order:
        ph = vocab[i]
        if exclude is not None and exclude.fullmatch(ph):
            continue
        docs = set(X[:, i].indices)
        if any(len(docs & k) / len(docs | k) >= 0.6 for k in kept_docs):
            continue
        n_neg = int(neg[list(docs)].sum())
        kept.append({"phrase": ph, "mentions": int(counts[i]), "pct_of_topic": round(100 * counts[i] / len(sub), 1),
                     "pct_negative": round(100 * n_neg / counts[i], 1)})
        kept_docs.append(docs)
        if len(kept) == top_n:
            break
    return kept


def drivers(sub, company, top_n=12):
    """What separates angry from happy users *inside* this topic (log-odds)."""
    from sklearn.feature_extraction.text import CountVectorizer
    neg = sub.loc[sub["label"] == "negative", "text"]
    pos = sub.loc[sub["label"] == "positive", "text"]
    if len(neg) < 8 or len(pos) < 8:
        return {"pain": [], "delight": []}
    vec = CountVectorizer(ngram_range=(1, 3), stop_words=_stop(company), min_df=2, binary=True,
                          token_pattern=r"(?u)\b[a-zA-Z][a-zA-Z]+\b")
    try:
        X = vec.fit_transform(pd.concat([neg, pos]))
    except ValueError:
        return {"pain": [], "delight": []}
    vocab = vec.get_feature_names_out()
    a = X[: len(neg)].sum(axis=0).A1 + 0.5
    b = X[len(neg):].sum(axis=0).A1 + 0.5
    la, lb = math.log(a.sum()), math.log(b.sum())
    z = [((math.log(x) - la) - (math.log(y) - lb)) / math.sqrt(1 / x + 1 / y) for x, y in zip(a, b)]
    rows = [{"phrase": v, "z": round(zz, 1), "neg": int(x - 0.5), "pos": int(y - 0.5)}
            for v, zz, x, y in zip(vocab, z, a, b)]
    pain = [r for r in sorted(rows, key=lambda r: -r["z"]) if r["neg"] >= 3 and r["z"] > 1.5]
    delight = [r for r in sorted(rows, key=lambda r: r["z"]) if r["pos"] >= 3 and r["z"] < -1.5]
    return {"pain": _collapse(pain, top_n=top_n), "delight": _collapse(delight, top_n=top_n)}


def deep_dive(df, company, topic, keywords=None, extra_subthemes=None, recent_days=30):
    mask = topic_mask(df, topic, keywords)
    sub = df[mask]
    neg_all = df[df["label"] == "negative"]
    n_neg_all = max(len(neg_all), 1)
    out = {"topic": topic, "custom": bool(keywords), "keywords": keywords or [], "mentions": int(len(sub)),
           "brand_n": int(len(df)), "brand_pct_negative": round(100 * (df["label"] == "negative").mean(), 1)}
    if sub.empty:
        return out
    sneg = sub[sub["label"] == "negative"]
    overall_rating = df["rating"].mean()
    out.update({
        "pct_of_all_feedback": round(100 * len(sub) / len(df), 1),
        "pct_of_all_complaints": round(100 * len(sneg) / n_neg_all, 1),
        "pct_negative": round(100 * len(sneg) / len(sub), 1),
        "net_sentiment": round(100 * ((sub["label"] == "positive").mean() - (sub["label"] == "negative").mean()), 1),
        "avg_rating": None if sub["rating"].isna().all() else round(float(sub["rating"].mean()), 2),
        "rating_drag": None if sub["rating"].isna().all() else round(float(sub["rating"].mean() - overall_rating), 2),
        "momentum": round(_momentum(sneg["date"], neg_all["date"], recent_days), 2),
        "churn_mentions": int(sneg["churn_signal"].sum()),
    })

    # Sub-themes: curated buckets for this topic (+ any the user defined).
    subs = subtheme_regexes(topic, extra_subthemes)
    hits = {k: sub["text"].map(lambda t, r=r: bool(r.search(t))) for k, r in subs.items()}
    rows = []
    for k, m in hits.items():
        s = sub[m]
        if s.empty:
            continue
        sn = s[s["label"] == "negative"]
        rows.append({"name": k, "mentions": int(len(s)), "pct_of_topic": round(100 * len(s) / len(sub), 1),
                     "pct_negative": round(100 * len(sn) / len(s), 1),
                     "avg_rating": None if s["rating"].isna().all() else round(float(s["rating"].mean()), 2),
                     "momentum": round(_momentum(sn["date"], sneg["date"], recent_days), 2),
                     "quote": (_quotes(sn, 1) or _quotes(s, 1) or [None])[0]})
    rows.sort(key=lambda r: -r["mentions"])
    if hits:
        any_hit = pd.concat(hits.values(), axis=1).any(axis=1)
        out["unclassified_pct"] = round(100 * (~any_hit).mean(), 1)
    out["subthemes"] = rows

    exclude = keyword_regex(keywords) if keywords else (
        _compile(T.CORE.get(topic, []) + [p for pk in T.SECTOR_PACKS.values() for p in pk.get(topic, [])]) or None)
    out["phrases"] = most_talked_about(sub, company, exclude=exclude)
    out["drivers"] = drivers(sub, company)

    # What else is going on when people raise this topic (root-cause hints).
    co = {}
    for lst in sub["areas"]:
        for a in lst:
            if a != topic:
                co[a] = co.get(a, 0) + 1
    out["co_mentions"] = [{"area": a, "pct_of_topic": round(100 * c / len(sub), 1)}
                          for a, c in sorted(co.items(), key=lambda x: -x[1])[:8]]

    d = df.dropna(subset=["date"])
    if not d.empty:
        months = d["date"].dt.to_period("M")
        tot = d.groupby(months).size()
        dm = mask.loc[d.index]
        ts = d[dm].groupby(months[dm])
        tl = pd.DataFrame({"n": ts.size(), "neg_rate": ts.apply(lambda x: (x["label"] == "negative").mean() * 100)})
        tl["share"] = 100 * tl["n"] / tot.reindex(tl.index)
        out["timeline"] = [{"month": str(k), "n": int(r.n), "neg_rate": round(float(r.neg_rate), 1),
                            "share": round(float(r.share), 1)} for k, r in tl.tail(18).iterrows()]
    out["sources"] = [{"source": k, "n": int(len(x)), "pct_negative": round(100 * (x["label"] == "negative").mean(), 1)}
                      for k, x in sub.groupby("source")]
    return out


def filter_feedback(df, topic=None, keywords=None, subtheme=None, extra_subthemes=None, phrase=None, q=None,
                    sentiment=None, source=None, sort="helpful", limit=30, offset=0):
    d = df
    if topic or keywords:
        d = d[topic_mask(d, topic, keywords)]
    if subtheme:
        rx = subtheme_regexes(topic, extra_subthemes).get(subtheme)
        if rx is not None:
            d = d[d["text"].map(lambda t: bool(rx.search(t)))]
    for term in (phrase, q):
        if term:
            rx = re.compile(r"\b" + r"\W+".join(map(re.escape, term.split())), re.I)
            d = d[d["text"].map(lambda t, rx=rx: bool(rx.search(t)))]
    if sentiment:
        d = d[d["label"] == sentiment]
    if source:
        d = d[d["source"] == source]
    key = {"helpful": (["likes", "sentiment"], [False, True]), "recent": (["date"], [False]),
           "negative": (["sentiment"], [True]), "positive": (["sentiment"], [False])}.get(sort, (["likes"], [False]))
    d = d.sort_values(key[0], ascending=key[1], na_position="last")
    page = d.iloc[offset: offset + limit]
    items = [{"text": r.text, "source": r.source, "label": str(r.label),
              "rating": None if pd.isna(r.rating) else int(r.rating), "likes": int(r.likes),
              "date": None if pd.isna(r.date) else r.date.date().isoformat(), "url": r.url,
              "version": r.version if isinstance(r.version, str) else None, "areas": r.areas}
             for r in page.itertuples()]
    return {"total": int(len(d)), "items": items}
