"""pain-point-radar CLI.

  python -m radar analyze "Nykaa" --sector beauty,ecommerce --competitors Purplle,Myntra,Tira
  python -m radar compare out/nykaa/summary.json out/purplle/summary.json
"""
from __future__ import annotations

import argparse
import json
import os
import re

from . import analyze as A
from . import report as R
from . import sources as S
from . import taxonomy as T


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def cmd_analyze(a):
    out = a.out or os.path.join("out", slug(a.company))
    os.makedirs(out, exist_ok=True)
    query = a.query or a.company
    want = set(a.sources.split(","))
    recs = []

    print(f"Collecting feedback for {a.company} ...")
    if "play" in want:
        pid = a.play_id or S.resolve_play_id(a.company, a.country)
        if pid:
            got = S.play_store(pid, count=a.max_reviews, country=a.country)
            print(f"  Play Store: {len(got)}"); recs += got
    if "appstore" in want:
        aid = a.appstore_id or S.resolve_app_store_id(a.company, a.country)
        if aid:
            got = S.app_store(aid, country=a.country)
            print(f"  App Store: {len(got)}"); recs += got
    if "reddit" in want:
        subs = a.subreddits.split(",") if a.subreddits else None
        got = S.reddit(query, subreddits=subs)
        print(f"  Reddit: {len(got)}"); recs += got
    if "hn" in want:
        got = S.hackernews(query)
        print(f"  Hacker News: {len(got)}"); recs += got
    for path in a.csv or []:
        got = S.from_csv(path)
        print(f"  CSV {path}: {len(got)}"); recs += got

    with open(os.path.join(out, "raw.json"), "w", encoding="utf-8") as f:
        json.dump(recs, f, ensure_ascii=False, default=str)

    print("Analysing ...")
    df = A.prepare(recs, a.company)
    df = A.score_sentiment(df)
    df = A.tag(df, T.build(a.sector))
    summary = A.run(df, a.company, competitors=[c.strip() for c in (a.competitors or "").split(",") if c.strip()],
                    recent_days=a.recent_days)
    if a.llm:
        from . import llm
        summary = llm.deep_dive(df, summary, top_k=a.llm_areas)

    df.assign(areas=df["areas"].map("; ".join)).to_csv(os.path.join(out, "feedback_tagged.csv"), index=False)
    R.write_json(summary, os.path.join(out, "summary.json"))
    R.render(summary, os.path.join(out, "report.html"))

    print(f"\n{a.company}: {summary['n']} items · {summary['pct_negative']}% negative · net {summary['net_sentiment']:+}")
    print("Top opportunity areas:")
    for x in summary["areas"][:6]:
        print(f"  {x['opportunity']:>3}  {x['area']:<34} {x['pct_of_all_complaints']:>5}% of complaints  "
              f"momentum {x['momentum']}x")
    print(f"\nReport: {os.path.join(out, 'report.html')}")


def cmd_compare(a):
    sums = []
    for p in a.summaries:
        with open(p, encoding="utf-8") as f:
            sums.append(json.load(f))
    R.render_compare(sums, a.out)
    print(f"Comparison: {a.out}")


def main():
    p = argparse.ArgumentParser(prog="radar", description="Quantify user pain points from public feedback.")
    sp = p.add_subparsers(dest="cmd", required=True)

    an = sp.add_parser("analyze", help="collect + analyse feedback for one company")
    an.add_argument("company", help='e.g. "Nykaa"')
    an.add_argument("--query", help="search term for forums if different from company name")
    an.add_argument("--sources", default="play,appstore,reddit,hn",
                    help="comma list from: play,appstore,reddit,hn (default: all)")
    an.add_argument("--play-id", help="Play Store package, e.g. com.fsn.nykaa (auto-resolved if omitted)")
    an.add_argument("--appstore-id", help="App Store numeric id (auto-resolved if omitted)")
    an.add_argument("--country", default="in", help="store country code (default: in)")
    an.add_argument("--max-reviews", type=int, default=2000, help="Play Store reviews to fetch (default 2000)")
    an.add_argument("--subreddits", help="limit Reddit to these, e.g. india,IndianSkincareAddicts")
    an.add_argument("--csv", action="append", help="extra feedback CSV (repeatable): Trustpilot, X, tickets, NPS...")
    an.add_argument("--sector", help=f"add sector pack(s): {','.join(T.SECTOR_PACKS)}")
    an.add_argument("--competitors", help="comma list of rivals to track mentions of")
    an.add_argument("--recent-days", type=int, default=30, help="window for momentum (default 30)")
    an.add_argument("--llm", action="store_true", help="use Claude to write problem statements for top areas")
    an.add_argument("--llm-areas", type=int, default=5)
    an.add_argument("--out", help="output folder (default out/<company>)")
    an.set_defaults(fn=cmd_analyze)

    cp = sp.add_parser("compare", help="side-by-side complaint mix for several analysed companies")
    cp.add_argument("summaries", nargs="+")
    cp.add_argument("--out", default="out/compare.html")
    cp.set_defaults(fn=cmd_compare)

    a = p.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
