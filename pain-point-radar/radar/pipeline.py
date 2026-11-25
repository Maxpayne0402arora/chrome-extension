"""Collect -> analyse -> save, shared by the CLI and the web app."""
from __future__ import annotations

import json
import os
import re
from datetime import datetime

import pandas as pd

from . import analyze as A
from . import report as R
from . import sources as S
from . import taxonomy as T

OUT = os.environ.get("RADAR_OUT", "out")

# Starting points for popular brands. Anything else works too: the app IDs are
# auto-resolved from the name. Check the log to confirm the right app was picked.
PRESETS = {
    "Nykaa": {"play_id": "com.fsn.nykaa", "sector": "beauty,ecommerce", "competitors": "Purplle,Myntra,Tira,Sugar,Amazon"},
    "Flipkart": {"play_id": "com.flipkart.android", "sector": "ecommerce", "competitors": "Amazon,Meesho,Myntra,Ajio"},
    "Amazon India": {"play_id": "in.amazon.mShop.android.shopping", "query": "Amazon India", "sector": "ecommerce",
                     "competitors": "Flipkart,Meesho,Myntra"},
    "Myntra": {"play_id": "com.myntra.android", "sector": "ecommerce", "competitors": "Ajio,Flipkart,Nykaa Fashion,Amazon"},
    "Meesho": {"play_id": "com.meesho.supply", "sector": "ecommerce", "competitors": "Flipkart,Amazon,Shopsy"},
    "Purplle": {"play_id": "com.manash.purplle", "sector": "beauty,ecommerce", "competitors": "Nykaa,Myntra,Tira"},
    "Swiggy": {"play_id": "in.swiggy.android", "sector": "food_delivery", "competitors": "Zomato,Zepto,Blinkit"},
    "Zomato": {"play_id": "com.application.zomato", "sector": "food_delivery", "competitors": "Swiggy,Zepto"},
    "Blinkit": {"play_id": "com.grofers.customerapp", "sector": "food_delivery,ecommerce",
                "competitors": "Zepto,Swiggy Instamart,BigBasket"},
    "Zepto": {"play_id": "com.zeptoconsumerapp", "sector": "food_delivery,ecommerce",
              "competitors": "Blinkit,Swiggy Instamart,BigBasket"},
    "Paytm": {"play_id": "net.one97.paytm", "sector": "fintech", "competitors": "PhonePe,Google Pay,CRED"},
    "PhonePe": {"play_id": "com.phonepe.app", "sector": "fintech", "competitors": "Paytm,Google Pay,CRED"},
    "Google": {"query": "Google", "sources": "reddit,hn", "sector": "tech", "competitors": "Bing,ChatGPT,Perplexity,DuckDuckGo"},
}

DEFAULTS = {"sources": "play,appstore,reddit,hn", "country": "in", "max_reviews": 2000, "recent_days": 30}


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def params_for(brand, **overrides):
    p = dict(DEFAULTS)
    preset = next((v for k, v in PRESETS.items() if k.lower() == brand.strip().lower()), {})
    p.update(preset)
    p.update({k: v for k, v in overrides.items() if v not in (None, "", [])})
    p["brand"] = brand.strip()
    return p


def collect(p, log=print):
    S.LOG = log
    want = set(str(p.get("sources", "")).split(","))
    query = p.get("query") or p["brand"]
    recs = []
    if "play" in want:
        pid = p.get("play_id") or S.resolve_play_id(p["brand"], p["country"])
        if pid:
            log(f"Fetching Play Store reviews for {pid} ...")
            got = S.play_store(pid, count=int(p["max_reviews"]), country=p["country"])
            log(f"  Play Store: {len(got)} reviews"); recs += got
    if "appstore" in want:
        aid = p.get("appstore_id") or S.resolve_app_store_id(p["brand"], p["country"])
        if aid:
            log(f"Fetching App Store reviews for {aid} ...")
            got = S.app_store(aid, country=p["country"])
            log(f"  App Store: {len(got)} reviews"); recs += got
    if "reddit" in want:
        log(f"Searching Reddit for '{query}' ...")
        subs = [x.strip() for x in str(p.get("subreddits") or "").split(",") if x.strip()] or None
        got = S.reddit(query, subreddits=subs)
        log(f"  Reddit: {len(got)} posts and comments"); recs += got
    if "hn" in want:
        log(f"Searching Hacker News for '{query}' ...")
        got = S.hackernews(query)
        log(f"  Hacker News: {len(got)} comments"); recs += got
    for path in p.get("csv") or []:
        got = S.from_csv(path)
        log(f"  CSV {os.path.basename(path)}: {len(got)} rows"); recs += got
    return recs


def build(recs, p):
    df = A.prepare(recs, p.get("match_name") or p["brand"].split()[0])
    df = A.score_sentiment(df)
    df = A.tag(df, T.build(p.get("sector")))
    comps = [c.strip() for c in str(p.get("competitors") or "").split(",") if c.strip()]
    summary = A.run(df, p["brand"], competitors=comps, recent_days=int(p.get("recent_days", 30)))
    return df, summary


def save(df, summary, p):
    d = os.path.join(OUT, slug(p["brand"]))
    os.makedirs(d, exist_ok=True)
    df.to_pickle(os.path.join(d, "feedback.pkl"))
    df.assign(areas=df["areas"].map("; ".join)).to_csv(os.path.join(d, "feedback_tagged.csv"), index=False)
    R.write_json(summary, os.path.join(d, "summary.json"))
    R.render(summary, os.path.join(d, "report.html"))
    meta = {k: v for k, v in p.items() if k != "csv"}
    meta["analysed_at"] = datetime.now().isoformat(timespec="seconds")
    with open(os.path.join(d, "meta.json"), "w") as f:
        json.dump(meta, f, indent=2)
    return d


def load(brand_slug):
    d = os.path.join(OUT, brand_slug)
    df = pd.read_pickle(os.path.join(d, "feedback.pkl"))
    with open(os.path.join(d, "summary.json"), encoding="utf-8") as f:
        summary = json.load(f)
    meta = {}
    if os.path.exists(os.path.join(d, "meta.json")):
        with open(os.path.join(d, "meta.json")) as f:
            meta = json.load(f)
    return df, summary, meta


def list_brands():
    if not os.path.isdir(OUT):
        return []
    out = []
    for s in sorted(os.listdir(OUT)):
        sp = os.path.join(OUT, s, "summary.json")
        if os.path.exists(sp) and os.path.exists(os.path.join(OUT, s, "feedback.pkl")):
            with open(sp, encoding="utf-8") as f:
                sm = json.load(f)
            meta = {}
            mp = os.path.join(OUT, s, "meta.json")
            if os.path.exists(mp):
                with open(mp) as f:
                    meta = json.load(f)
            out.append({"slug": s, "brand": sm["company"], "n": sm["n"], "pct_negative": sm["pct_negative"],
                        "avg_rating": sm["avg_rating"], "top_area": sm["areas"][0]["area"] if sm["areas"] else None,
                        "analysed_at": meta.get("analysed_at")})
    return sorted(out, key=lambda x: x.get("analysed_at") or "", reverse=True)
