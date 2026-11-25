"""pain-point-radar

  python -m radar serve                                   # web app at http://localhost:8765
  python -m radar analyze "Nykaa"                         # command-line run
  python -m radar topic nykaa "Customer support"          # zoom into a topic
  python -m radar topic nykaa "Delivery promise" --keywords "delivery date,promised,eta"
  python -m radar compare out/nykaa/summary.json out/purplle/summary.json
"""
from __future__ import annotations

import argparse
import json
import os

from . import pipeline as P
from . import report as R
from . import taxonomy as T


def cmd_analyze(a):
    params = P.params_for(a.company, sources=a.sources, play_id=a.play_id, appstore_id=a.appstore_id,
                          country=a.country, max_reviews=a.max_reviews, sector=a.sector, competitors=a.competitors,
                          subreddits=a.subreddits, query=a.query, recent_days=a.recent_days, csv=a.csv)
    if a.out:
        P.OUT = a.out
    print(f"Collecting feedback for {a.company} ...")
    recs = P.collect(params)
    print("Analysing ...")
    df, summary = P.build(recs, params)
    if a.llm:
        from . import llm
        summary = llm.deep_dive(df, summary, top_k=a.llm_areas)
    d = P.save(df, summary, params)

    print(f"\n{a.company}: {summary['n']} items · {summary['pct_negative']}% negative · net {summary['net_sentiment']:+}")
    print("Top opportunity areas:")
    for x in summary["areas"][:6]:
        print(f"  {x['opportunity']:>3}  {x['area']:<34} {x['pct_of_all_complaints']:>5}% of complaints  "
              f"momentum {x['momentum']}x")
    print(f"\nReport: {os.path.join(d, 'report.html')}")
    print(f"Explore interactively: python -m radar serve")


def cmd_topic(a):
    from . import topic as TP
    if a.out:
        P.OUT = a.out
    df, summary, meta = P.load(P.slug(a.brand))
    kws = [k.strip() for k in a.keywords.split(",")] if a.keywords else None
    d = TP.deep_dive(df, summary["company"], a.topic, kws, recent_days=int(meta.get("recent_days", 30)))
    if a.json:
        print(json.dumps(d, indent=2, default=str))
        return
    if not d["mentions"]:
        print("No feedback mentions this topic.")
        return
    print(f"\n{summary['company']} / {a.topic}: {d['mentions']} mentions ({d['pct_of_all_feedback']}% of feedback), "
          f"{d['pct_negative']}% negative (brand: {d['brand_pct_negative']}%), momentum {d['momentum']}x")
    if d.get("subthemes"):
        print("\nSub-themes:")
        for s in d["subthemes"]:
            print(f"  {s['pct_of_topic']:>5}%  {s['name']:<34} {s['pct_negative']}% negative")
    print("\nMost talked-about phrases:")
    for p in d["phrases"][:12]:
        print(f"  {p['mentions']:>5}  {p['phrase']:<34} {p['pct_negative']}% negative")
    if d["drivers"]["pain"]:
        print("\nWhat makes it bad: " + ", ".join(p["phrase"] for p in d["drivers"]["pain"][:10]))
    if d["co_mentions"]:
        print("Mentioned alongside: " + ", ".join(f"{c['area']} ({c['pct_of_topic']}%)" for c in d["co_mentions"][:5]))


def cmd_compare(a):
    sums = []
    for p in a.summaries:
        with open(p, encoding="utf-8") as f:
            sums.append(json.load(f))
    R.render_compare(sums, a.out)
    print(f"Comparison: {a.out}")


def cmd_serve(a):
    from . import server
    if a.out:
        P.OUT = a.out
    server.serve(a.port, open_browser=not a.no_browser)


def main():
    p = argparse.ArgumentParser(prog="radar", description="Quantify user pain points from public feedback.")
    sp = p.add_subparsers(dest="cmd", required=True)

    sv = sp.add_parser("serve", help="start the web app")
    sv.add_argument("--port", type=int, default=8765)
    sv.add_argument("--no-browser", action="store_true")
    sv.add_argument("--out", help="data folder (default ./out)")
    sv.set_defaults(fn=cmd_serve)

    an = sp.add_parser("analyze", help="collect + analyse feedback for one company")
    an.add_argument("company", help='e.g. "Nykaa"')
    an.add_argument("--query", help="search term for forums if different from company name")
    an.add_argument("--sources", help="comma list from: play,appstore,reddit,hn (default: all)")
    an.add_argument("--play-id", help="Play Store package, e.g. com.fsn.nykaa (auto-resolved if omitted)")
    an.add_argument("--appstore-id", help="App Store numeric id (auto-resolved if omitted)")
    an.add_argument("--country", help="store country code (default: in)")
    an.add_argument("--max-reviews", type=int, help="Play Store reviews to fetch (default 2000)")
    an.add_argument("--subreddits", help="limit Reddit to these, e.g. india,IndianSkincareAddicts")
    an.add_argument("--csv", action="append", help="extra feedback CSV (repeatable): Trustpilot, X, tickets, NPS...")
    an.add_argument("--sector", help=f"add sector pack(s): {','.join(T.SECTOR_PACKS)}")
    an.add_argument("--competitors", help="comma list of rivals to track mentions of")
    an.add_argument("--recent-days", type=int, help="window for momentum (default 30)")
    an.add_argument("--llm", action="store_true", help="use Claude to write problem statements for top areas")
    an.add_argument("--llm-areas", type=int, default=5)
    an.add_argument("--out", help="data folder (default ./out)")
    an.set_defaults(fn=cmd_analyze)

    tp = sp.add_parser("topic", help="deep-dive one topic for an analysed brand")
    tp.add_argument("brand")
    tp.add_argument("topic", help='e.g. "Customer support", or a name for your own keywords')
    tp.add_argument("--keywords", help="define the topic by your own comma-separated keywords")
    tp.add_argument("--json", action="store_true")
    tp.add_argument("--out", help="data folder (default ./out)")
    tp.set_defaults(fn=cmd_topic)

    cp = sp.add_parser("compare", help="static side-by-side complaint mix for several analysed brands")
    cp.add_argument("summaries", nargs="+")
    cp.add_argument("--out", default="out/compare.html")
    cp.set_defaults(fn=cmd_compare)

    a = p.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
