"""Collectors for public user feedback.

Every collector returns a list of dicts with the same shape (see ``_rec``) so the
analysis layer never needs to know where a piece of feedback came from.
Collectors fail soft: a blocked or rate-limited source logs a warning and
returns what it has, so one bad source never kills a run.
"""
from __future__ import annotations

import csv
import sys
import time
from datetime import datetime, timezone

import requests

UA = "Mozilla/5.0 (pain-point-radar; research script)"
HTTP = requests.Session()
HTTP.headers.update({"User-Agent": UA})


LOG = print  # the web server swaps this for a per-job logger


def log(msg: str) -> None:
    LOG(msg)


def warn(msg: str) -> None:
    LOG(f"  [warn] {msg}")


def _rec(source, text, *, id=None, date=None, rating=None, title="", likes=0,
         version=None, url=None, channel=None):
    return {
        "source": source,            # play_store | app_store | reddit | hackernews | csv:<name>
        "channel": channel or source,  # finer grain, e.g. r/india
        "id": str(id) if id is not None else None,
        "date": date,                # ISO date string (YYYY-MM-DD) or None
        "rating": rating,            # 1-5 or None
        "title": title or "",
        "text": (text or "").strip(),
        "likes": int(likes or 0),    # helpful votes / upvotes = how many people agree
        "version": version,
        "url": url,
    }


def _iso(ts) -> str | None:
    if ts is None or ts == "":
        return None
    if isinstance(ts, (int, float)):
        return datetime.fromtimestamp(ts, tz=timezone.utc).date().isoformat()
    if isinstance(ts, datetime):
        return ts.date().isoformat()
    s = str(ts)
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ",
                "%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(s, fmt).date().isoformat()
        except ValueError:
            pass
    return s[:10] if len(s) >= 10 and s[4] == "-" else None


# --------------------------------------------------------------------------- Google Play
def resolve_play_id(company: str, country: str) -> str | None:
    try:
        from google_play_scraper import search
        hits = search(company, n_hits=5, lang="en", country=country)
        for h in hits:
            if h.get("appId"):
                log(f"  Play Store: resolved '{company}' -> {h['appId']} ({h.get('title')})")
                return h["appId"]
    except Exception as e:  # noqa: BLE001
        warn(f"Play Store search failed: {e}")
    return None


def play_store(app_id: str, count: int = 2000, country: str = "in", lang: str = "en"):
    try:
        from google_play_scraper import Sort, reviews
    except ImportError:
        warn("google-play-scraper not installed; skipping Play Store")
        return []
    out, token = [], None
    while len(out) < count:
        try:
            batch, token = reviews(app_id, lang=lang, country=country, sort=Sort.NEWEST,
                                   count=min(200, count - len(out)), continuation_token=token)
        except Exception as e:  # noqa: BLE001
            warn(f"Play Store fetch stopped after {len(out)} reviews: {e}")
            break
        if not batch:
            break
        for r in batch:
            out.append(_rec("play_store", r.get("content"), id=r.get("reviewId"),
                            date=_iso(r.get("at")), rating=r.get("score"),
                            likes=r.get("thumbsUpCount"), version=r.get("reviewCreatedVersion")
                            or r.get("appVersion"),
                            url=f"https://play.google.com/store/apps/details?id={app_id}"))
        if token is None:
            break
        time.sleep(0.5)
    return out


# --------------------------------------------------------------------------- Apple App Store
def resolve_app_store_id(company: str, country: str) -> str | None:
    try:
        r = HTTP.get("https://itunes.apple.com/search", timeout=20,
                     params={"term": company, "entity": "software", "country": country, "limit": 5})
        r.raise_for_status()
        res = r.json().get("results", [])
        if res:
            log(f"  App Store: resolved '{company}' -> {res[0]['trackId']} ({res[0].get('trackName')})")
            return str(res[0]["trackId"])
    except Exception as e:  # noqa: BLE001
        warn(f"App Store search failed: {e}")
    return None


def app_store(app_id: str, country: str = "in", pages: int = 10):
    """Apple's public RSS feed: up to 10 pages x 50 most-recent reviews."""
    out = []
    for page in range(1, pages + 1):
        url = (f"https://itunes.apple.com/{country}/rss/customerreviews/page={page}"
               f"/id={app_id}/sortby=mostrecent/json")
        try:
            r = HTTP.get(url, timeout=20)
            r.raise_for_status()
            entries = r.json().get("feed", {}).get("entry", [])
        except Exception as e:  # noqa: BLE001
            warn(f"App Store page {page} failed: {e}")
            break
        if isinstance(entries, dict):
            entries = [entries]
        entries = [e for e in entries if "im:rating" in e]  # first entry can be app metadata
        if not entries:
            break
        for e in entries:
            out.append(_rec("app_store", e.get("content", {}).get("label"),
                            id=e.get("id", {}).get("label"),
                            date=_iso(e.get("updated", {}).get("label")),
                            rating=int(e["im:rating"]["label"]),
                            title=e.get("title", {}).get("label"),
                            likes=int(e.get("im:voteSum", {}).get("label", 0) or 0),
                            version=e.get("im:version", {}).get("label"),
                            url=f"https://apps.apple.com/{country}/app/id{app_id}"))
        time.sleep(0.5)
    return out


# --------------------------------------------------------------------------- Reddit
def reddit(query: str, limit: int = 100, subreddits: list[str] | None = None,
           comments_per_post: int = 30, timeframe: str = "year"):
    """Reddit public JSON search (posts) + top comments on the most-discussed posts.

    Reddit throttles anonymous clients; if you get 403/429s, register a free
    "script" app and swap this for PRAW.
    """
    out, posts = [], []
    targets = [f"r/{s}" for s in subreddits] if subreddits else [None]
    for t in targets:
        base = f"https://www.reddit.com/{t}/search.json" if t else "https://www.reddit.com/search.json"
        params = {"q": query, "limit": min(limit, 100), "sort": "relevance", "t": timeframe}
        if t:
            params["restrict_sr"] = "on"
        try:
            r = HTTP.get(base, params=params, timeout=20)
            r.raise_for_status()
            posts += [c["data"] for c in r.json()["data"]["children"]]
        except Exception as e:  # noqa: BLE001
            warn(f"Reddit search ({t or 'all'}) failed: {e}")
        time.sleep(1.0)

    seen = set()
    for p in posts:
        if p["id"] in seen:
            continue
        seen.add(p["id"])
        out.append(_rec("reddit", p.get("selftext") or p.get("title"), id=p["id"],
                        title=p.get("title"), date=_iso(p.get("created_utc")),
                        likes=p.get("score"), channel=f"r/{p.get('subreddit')}",
                        url="https://www.reddit.com" + p.get("permalink", "")))

    for p in sorted(posts, key=lambda x: x.get("num_comments", 0), reverse=True)[:15]:
        try:
            r = HTTP.get(f"https://www.reddit.com{p['permalink']}.json",
                         params={"limit": comments_per_post, "sort": "top"}, timeout=20)
            r.raise_for_status()
            for c in r.json()[1]["data"]["children"]:
                d = c.get("data", {})
                if c.get("kind") != "t1" or not d.get("body"):
                    continue
                out.append(_rec("reddit", d["body"], id=d.get("id"),
                                date=_iso(d.get("created_utc")), likes=d.get("score"),
                                channel=f"r/{p.get('subreddit')}",
                                url="https://www.reddit.com" + d.get("permalink", "")))
        except Exception as e:  # noqa: BLE001
            warn(f"Reddit comments failed for {p.get('id')}: {e}")
        time.sleep(1.0)
    return out


# --------------------------------------------------------------------------- Hacker News
def hackernews(query: str, limit: int = 300):
    """HN via the free Algolia API - best for developer/tech products (Google, Stripe...)."""
    out, page = [], 0
    while len(out) < limit:
        try:
            r = HTTP.get("https://hn.algolia.com/api/v1/search", timeout=20,
                         params={"query": query, "tags": "comment", "hitsPerPage": 100, "page": page})
            r.raise_for_status()
            hits = r.json().get("hits", [])
        except Exception as e:  # noqa: BLE001
            warn(f"Hacker News fetch failed: {e}")
            break
        if not hits:
            break
        for h in hits:
            out.append(_rec("hackernews", h.get("comment_text"), id=h.get("objectID"),
                            date=_iso(h.get("created_at")),
                            likes=h.get("points") or 0,
                            url=f"https://news.ycombinator.com/item?id={h.get('objectID')}"))
        page += 1
    return out[:limit]


# --------------------------------------------------------------------------- CSV import
TEXT_COLS = ("text", "review", "content", "body", "comment", "feedback", "message", "review_text")
DATE_COLS = ("date", "at", "created_at", "timestamp", "review_date", "time")
RATING_COLS = ("rating", "score", "stars", "star_rating")
TITLE_COLS = ("title", "subject", "headline")


def from_csv(path: str, name: str | None = None):
    """Import anything you exported by hand: Trustpilot, MouthShut, X/Twitter,
    support tickets, NPS verbatims, survey answers, call notes...
    Needs at least a text-like column; date/rating/title/source are optional."""
    name = name or path.rsplit("/", 1)[-1].rsplit(".", 1)[0]
    out = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        return out
    cols = {c.lower().strip(): c for c in rows[0].keys()}
    pick = lambda opts: next((cols[o] for o in opts if o in cols), None)  # noqa: E731
    tc, dc, rc, ti = pick(TEXT_COLS), pick(DATE_COLS), pick(RATING_COLS), pick(TITLE_COLS)
    sc = cols.get("source")
    if not tc:
        raise SystemExit(f"{path}: no text column found (expected one of {TEXT_COLS})")
    for i, row in enumerate(rows):
        rating = None
        if rc and row.get(rc):
            try:
                rating = float(row[rc])
            except ValueError:
                pass
        src = (row.get(sc) or "").strip() if sc else ""
        out.append(_rec(f"csv:{src or name}", row.get(tc), id=f"{name}-{i}",
                        date=_iso(row.get(dc)) if dc else None, rating=rating,
                        title=row.get(ti, "") if ti else "", url=row.get(cols.get("url", ""), None)))
    return out
