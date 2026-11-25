"""Turn raw feedback into quantified pain points.

The key output is the per-area table with an *Opportunity score*:

    opportunity = complaint share  x  severity  x  momentum  x  reach

* complaint share  - % of all negative feedback that mentions the area (how common)
* severity         - mean negativity of those complaints, 0..1 (how painful)
* momentum         - recent share / earlier share, clipped to 0.5..2 (getting worse?)
* reach            - 1 + log10(1 + mean helpful votes) (how many others agree)

Scores are normalised so the top area = 100. It is a ranking aid, not truth:
read the quotes before you believe a number.
"""
from __future__ import annotations

import math
import re
from collections import Counter
from datetime import date, timedelta

import pandas as pd

from . import taxonomy as T

try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    _VADER = SentimentIntensityAnalyzer()
except ImportError:  # pragma: no cover
    _VADER = None

NEG, POS = -0.15, 0.15


def _compile(patterns):
    return re.compile("|".join(f"(?:{p})" for p in patterns), re.I)


def prepare(records, company: str, require_mention_sources=("reddit", "hackernews")):
    df = pd.DataFrame(records)
    if df.empty:
        raise SystemExit("No feedback collected - check app IDs / network / CSV paths.")
    df["text"] = df["title"].fillna("").str.cat(df["text"].fillna(""), sep=". ").str.strip(". ")
    df["text"] = df["text"].str.replace(r"<[^>]+>", " ", regex=True).str.replace(r"\s+", " ", regex=True)
    df = df[df["text"].str.len() >= 12]
    df = df.drop_duplicates(subset=["source", "id", "text"])
    # Forum results are noisy: keep only posts that actually name the company.
    name_re = re.compile(re.escape(company), re.I)
    forum = df["source"].isin(require_mention_sources)
    df = df[~forum | df["text"].str.contains(name_re)]
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["rating"] = pd.to_numeric(df["rating"], errors="coerce")
    df["likes"] = pd.to_numeric(df["likes"], errors="coerce").fillna(0).clip(lower=0)
    return df.reset_index(drop=True)


def score_sentiment(df):
    if _VADER is None:
        raise SystemExit("pip install vaderSentiment")
    text_score = df["text"].map(lambda t: _VADER.polarity_scores(t)["compound"])
    star_score = (df["rating"] - 3) / 2  # 1★ -> -1, 5★ -> +1
    # Stars are the user's own verdict - trust them more than a lexicon when present.
    df["sentiment"] = (0.35 * text_score + 0.65 * star_score).where(star_score.notna(), text_score).round(3)
    df["label"] = pd.cut(df["sentiment"], [-1.01, NEG, POS, 1.01], labels=["negative", "neutral", "positive"])
    return df


def tag(df, tax):
    regs = {area: _compile(p) for area, p in tax.items()}
    df["areas"] = df["text"].map(lambda t: [a for a, r in regs.items() if r.search(t)])
    churn, fr = _compile(T.CHURN), _compile(T.FEATURE_REQUEST)
    df["churn_signal"] = df["text"].map(lambda t: bool(churn.search(t)))
    df["feature_request"] = df["text"].map(lambda t: bool(fr.search(t)))
    return df


def _momentum(sub_dates, all_neg_dates, recent_days):
    if all_neg_dates.isna().all():
        return 1.0
    end = all_neg_dates.max()
    cut = end - pd.Timedelta(days=recent_days)
    tot_recent = (all_neg_dates > cut).sum()
    tot_old = (all_neg_dates <= cut).sum()
    if tot_recent < 10 or tot_old < 10:
        return 1.0
    r = (sub_dates > cut).sum() / tot_recent
    o = (sub_dates <= cut).sum() / tot_old
    if o == 0:
        return 2.0 if r > 0 else 1.0
    return float(min(2.0, max(0.5, r / o)))


def _quotes(sub, n=4):
    if sub.empty:
        return []
    s = sub.assign(_len=sub["text"].str.len().clip(upper=400))
    s = s[(s["_len"] >= 40)] if (s["_len"] >= 40).any() else s
    s = s.drop_duplicates(subset="text").sort_values(["likes", "sentiment"], ascending=[False, True]).head(n)
    return [{"text": r.text[:500], "source": r.source, "rating": None if pd.isna(r.rating) else int(r.rating),
             "likes": int(r.likes), "date": None if pd.isna(r.date) else r.date.date().isoformat(), "url": r.url}
            for r in s.itertuples()]


def area_table(df, recent_days=30):
    neg = df[df["label"] == "negative"]
    n_neg = max(len(neg), 1)
    overall_rating = df["rating"].mean()
    rows = []
    areas = sorted({a for lst in df["areas"] for a in lst})
    for a in areas:
        mask = df["areas"].map(lambda l, a=a: a in l)
        sub, sub_neg = df[mask], neg[neg["areas"].map(lambda l, a=a: a in l)]
        if len(sub) < 3:
            continue
        share = len(sub_neg) / n_neg
        severity = float(-sub_neg["sentiment"].mean()) if len(sub_neg) else 0.0
        momentum = _momentum(sub_neg["date"], neg["date"], recent_days)
        reach = 1 + math.log10(1 + float(sub_neg["likes"].mean() if len(sub_neg) else 0))
        rows.append({
            "area": a,
            "mentions": int(len(sub)),
            "negative_mentions": int(len(sub_neg)),
            "pct_of_all_complaints": round(100 * share, 1),
            "negative_rate": round(100 * len(sub_neg) / len(sub), 1),
            "severity": round(severity, 3),
            "momentum": round(momentum, 2),
            "reach": round(reach, 2),
            "avg_rating": None if sub["rating"].isna().all() else round(float(sub["rating"].mean()), 2),
            "rating_drag": None if sub["rating"].isna().all() or pd.isna(overall_rating)
            else round(float(sub["rating"].mean() - overall_rating), 2),
            "churn_mentions": int(sub_neg["churn_signal"].sum()),
            "raw_score": share * severity * momentum * reach,
            "quotes": _quotes(sub_neg),
        })
    t = pd.DataFrame(rows)
    if t.empty:
        return t
    top = t["raw_score"].max() or 1
    t["opportunity"] = (100 * t["raw_score"] / top).round(0).astype(int)
    return t.drop(columns="raw_score").sort_values("opportunity", ascending=False).reset_index(drop=True)


STOP_EXTRA = {"app", "apps", "good", "nice", "bad", "worst", "best", "please", "use", "using", "just", "like",
              "really", "dont", "don", "didn", "doesn", "im", "ve", "ll", "time", "one", "also", "even", "get", "got"}


def emerging_phrases(df, company, top_n=25):
    """Phrases that are much more common in negative than in positive feedback
    (weighted log-odds with a uniform prior, Monroe et al. 2008). Surfaces
    complaints your taxonomy has no bucket for yet."""
    from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS, CountVectorizer

    neg = df.loc[df["label"] == "negative", "text"]
    rest = df.loc[df["label"] != "negative", "text"]
    if len(neg) < 20 or len(rest) < 20:
        return []
    stop = list(ENGLISH_STOP_WORDS | STOP_EXTRA | set(company.lower().split()))
    vec = CountVectorizer(ngram_range=(2, 3), stop_words=stop, min_df=3, token_pattern=r"(?u)\b[a-zA-Z][a-zA-Z]+\b")
    try:
        X = vec.fit_transform(pd.concat([neg, rest]))
    except ValueError:
        return []
    vocab = vec.get_feature_names_out()
    a = X[: len(neg)].sum(axis=0).A1 + 0.5
    b = X[len(neg):].sum(axis=0).A1 + 0.5
    na, nb = a.sum(), b.sum()
    delta = (pd.Series(a).apply(math.log) - math.log(na)) - (pd.Series(b).apply(math.log) - math.log(nb))
    var = 1 / a + 1 / b
    z = delta / var ** 0.5
    out = pd.DataFrame({"phrase": vocab, "z": z, "neg_count": (a - 0.5).astype(int)})
    out = out[out["neg_count"] >= 3].sort_values(["z", "neg_count"], ascending=False)
    kept = []
    for r in out.itertuples():  # drop "keeps crashing" if "keeps crashing latest" already shown
        if any(r.phrase in k.phrase or k.phrase in r.phrase for k in kept):
            continue
        kept.append(r)
        if len(kept) == top_n:
            break
    out = pd.DataFrame(kept) if kept else out.head(0)
    return [{"phrase": r.phrase, "neg_count": int(r.neg_count), "z": round(float(r.z), 1)} for r in out.itertuples()]


def by_month(df):
    d = df.dropna(subset=["date"])
    if d.empty:
        return []
    g = d.groupby(d["date"].dt.to_period("M"))
    out = pd.DataFrame({
        "n": g.size(),
        "neg_rate": g.apply(lambda x: (x["label"] == "negative").mean() * 100),
        "avg_sentiment": g["sentiment"].mean(),
        "avg_rating": g["rating"].mean(),
    }).tail(18)
    return [{"month": str(k), "n": int(r.n), "neg_rate": round(float(r.neg_rate), 1),
             "avg_sentiment": round(float(r.avg_sentiment), 3),
             "avg_rating": None if pd.isna(r.avg_rating) else round(float(r.avg_rating), 2)}
            for k, r in out.iterrows()]


def by_version(df, min_n=15):
    d = df.dropna(subset=["version"])
    d = d[d["source"].isin(["play_store", "app_store"])]
    if d.empty:
        return []
    g = d.groupby(["source", "version"])
    t = pd.DataFrame({"n": g.size(), "neg_rate": g.apply(lambda x: (x["label"] == "negative").mean() * 100),
                      "avg_rating": g["rating"].mean(), "first_seen": g["date"].min()}).reset_index()
    t = t[t["n"] >= min_n].sort_values("first_seen", ascending=False).head(12)
    return [{"source": r.source, "version": r.version, "n": int(r.n), "neg_rate": round(float(r.neg_rate), 1),
             "avg_rating": None if pd.isna(r.avg_rating) else round(float(r.avg_rating), 2)}
            for r in t.itertuples()]


def by_source(df):
    g = df.groupby("source")
    return [{"source": k, "n": int(len(x)), "neg_rate": round(float((x["label"] == "negative").mean() * 100), 1),
             "avg_rating": None if x["rating"].isna().all() else round(float(x["rating"].mean()), 2)}
            for k, x in g]


def competitor_mentions(df, competitors):
    if not competitors:
        return []
    out = []
    for c in competitors:
        m = df["text"].str.contains(re.compile(rf"\b{re.escape(c)}\b", re.I))
        sub = df[m]
        if len(sub):
            out.append({"competitor": c, "mentions": int(len(sub)),
                        "in_churn_context": int(sub["churn_signal"].sum()),
                        "quotes": _quotes(sub[sub["churn_signal"]] if sub["churn_signal"].any() else sub, 2)})
    return sorted(out, key=lambda x: -x["mentions"])


def run(df, company, competitors=None, recent_days=30):
    neg = df[df["label"] == "negative"]
    untagged_neg = neg[neg["areas"].map(len) == 0]
    summary = {
        "company": company,
        "generated": date.today().isoformat(),
        "n": int(len(df)),
        "date_range": [None if df["date"].isna().all() else df["date"].min().date().isoformat(),
                       None if df["date"].isna().all() else df["date"].max().date().isoformat()],
        "avg_rating": None if df["rating"].isna().all() else round(float(df["rating"].mean()), 2),
        "pct_negative": round(100 * (df["label"] == "negative").mean(), 1),
        "pct_positive": round(100 * (df["label"] == "positive").mean(), 1),
        "net_sentiment": round(100 * ((df["label"] == "positive").mean() - (df["label"] == "negative").mean()), 1),
        "pct_complaints_untagged": round(100 * len(untagged_neg) / max(len(neg), 1), 1),
        "churn_signals": int(df["churn_signal"].sum()),
        "sources": by_source(df),
        "areas": area_table(df, recent_days).to_dict("records"),
        "timeline": by_month(df),
        "versions": by_version(df),
        "emerging": emerging_phrases(df, company),
        "feature_requests": _quotes(df[df["feature_request"]], 12),
        "churn_quotes": _quotes(df[df["churn_signal"] & (df["label"] == "negative")], 8),
        "untagged_quotes": _quotes(untagged_neg, 8),
        "competitors": competitor_mentions(df, competitors or []),
    }
    return summary
