"""Self-contained HTML report (no external assets) - open it in any browser,
email it, or drop it in a doc."""
from __future__ import annotations

import html
import json

CSS = """
:root{--bg:#f7f7f5;--surface:#ffffff;--ink:#191919;--ink2:#666666;--rule:#e4e4e0;--grid:#ececea;
--blue:#257de0;--red:#ec4647;--mid:#d9d9d6;--chip:#f0f0ee}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#111111;--surface:#191919;--ink:#efefef;
--ink2:#9c9c9c;--rule:#2e2e2e;--grid:#262626;--blue:#338ced;--red:#eb6263;--mid:#383838;--chip:#242424}}
:root[data-theme=dark]{--bg:#111111;--surface:#191919;--ink:#efefef;--ink2:#9c9c9c;--rule:#2e2e2e;--grid:#262626;
--blue:#338ced;--red:#eb6263;--mid:#383838;--chip:#242424}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);
font:15px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Inter,Roboto,sans-serif}
main{max-width:1080px;margin:0 auto;padding:32px 16px 64px}
h1{font-size:28px;margin:0 0 4px;letter-spacing:-.01em}h2{font-size:18px;margin:40px 0 6px}
.sub{color:var(--ink2);margin:0 0 12px;font-size:14px}
.card{background:var(--surface);border:1px solid var(--rule);border-radius:10px;padding:18px 20px;margin-top:12px}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin-top:20px}
.tile{background:var(--surface);border:1px solid var(--rule);border-radius:10px;padding:14px 16px}
.tile b{display:block;font-size:26px;font-variant-numeric:tabular-nums;letter-spacing:-.01em}
.tile span{color:var(--ink2);font-size:13px}
table{width:100%;border-collapse:collapse;font-size:14px}th{text-align:left;color:var(--ink2);font-weight:500;
font-size:12px;text-transform:uppercase;letter-spacing:.04em;padding:6px 8px;border-bottom:1px solid var(--rule)}
td{padding:9px 8px;border-bottom:1px solid var(--grid);vertical-align:top;font-variant-numeric:tabular-nums}
td.num,th.num{text-align:right;white-space:nowrap}
.bar{height:10px;background:var(--grid);border-radius:4px;min-width:90px}
.bar i{display:block;height:100%;background:var(--blue);border-radius:4px}
.split{display:flex;height:12px;gap:2px;border-radius:4px;overflow:hidden}
.split i{display:block;height:100%}
.legend{display:flex;gap:16px;font-size:13px;color:var(--ink2);margin:8px 0}
.legend i{display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:6px;vertical-align:-1px}
details{margin-top:6px}summary{cursor:pointer;color:var(--ink2);font-size:13px}
blockquote{margin:8px 0;padding:8px 12px;border-left:3px solid var(--rule);background:var(--chip);border-radius:0 6px 6px 0;font-size:14px}
blockquote small{display:block;color:var(--ink2);margin-top:4px;font-size:12px}
.chips{display:flex;flex-wrap:wrap;gap:6px}.chip{background:var(--chip);border:1px solid var(--rule);
border-radius:999px;padding:3px 10px;font-size:13px}.chip em{color:var(--ink2);font-style:normal;margin-left:6px}
.pp{border-top:1px solid var(--grid);padding:10px 0}.pp:first-child{border-top:0}.pp b{font-size:15px}
.meta{color:var(--ink2);font-size:13px}.note{color:var(--ink2);font-size:13px;margin-top:10px}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:12px}@media(max-width:760px){.grid2{grid-template-columns:1fr}
.hide-sm{display:none}}
.tip{position:fixed;pointer-events:none;background:var(--ink);color:var(--surface);padding:6px 9px;border-radius:6px;
font-size:12px;display:none;z-index:9}
.scroll{overflow-x:auto}
svg text{fill:var(--ink2);font-size:11px}
"""

JS = """
const tip=document.querySelector('.tip');
document.querySelectorAll('[data-tip]').forEach(el=>{
 el.addEventListener('mousemove',e=>{tip.style.display='block';tip.textContent=el.dataset.tip;
  tip.style.left=Math.min(e.clientX+12,innerWidth-220)+'px';tip.style.top=(e.clientY+12)+'px'});
 el.addEventListener('mouseleave',()=>tip.style.display='none');});
"""


def e(x):
    return html.escape("" if x is None else str(x))


def _quote(q):
    bits = [q.get("source")]
    if q.get("rating"):
        bits.append(f"{q['rating']}★")
    if q.get("likes"):
        bits.append(f"{q['likes']} found helpful")
    if q.get("date"):
        bits.append(q["date"])
    link = f' · <a href="{e(q["url"])}" target="_blank" rel="noopener">source</a>' if q.get("url") else ""
    return f"<blockquote>{e(q['text'])}<small>{e(' · '.join(map(str, bits)))}{link}</small></blockquote>"


def _timeline_svg(tl):
    if len(tl) < 2:
        return "<p class='meta'>Not enough dated feedback for a trend.</p>"
    W, H, L, R, T, B = 1000, 220, 40, 10, 12, 28
    ymax = max(50, max(p["neg_rate"] for p in tl) * 1.15)
    xs = [L + i * (W - L - R) / (len(tl) - 1) for i in range(len(tl))]
    y = lambda v: T + (H - T - B) * (1 - v / ymax)  # noqa: E731
    grid = "".join(f'<line x1="{L}" x2="{W-R}" y1="{y(v):.1f}" y2="{y(v):.1f}" stroke="var(--grid)"/>'
                   f'<text x="{L-6}" y="{y(v)+4:.1f}" text-anchor="end">{v}%</text>'
                   for v in range(0, int(ymax) + 1, 25))
    pts = " ".join(f"{x:.1f},{y(p['neg_rate']):.1f}" for x, p in zip(xs, tl))
    step = max(1, len(tl) // 8)
    anchor = lambda i: "start" if i == 0 else "end" if i == len(tl) - 1 else "middle"  # noqa: E731
    labels = "".join(f'<text x="{x:.1f}" y="{H-8}" text-anchor="{anchor(i)}">{p["month"]}</text>'
                     for i, (x, p) in enumerate(zip(xs, tl)) if i % step == 0 or i == len(tl) - 1)
    dots = "".join(
        f'<circle cx="{x:.1f}" cy="{y(p["neg_rate"]):.1f}" r="4" fill="var(--blue)" stroke="var(--surface)" stroke-width="2"/>'
        f'<rect x="{x-14:.1f}" y="0" width="28" height="{H}" fill="transparent" '
        f'data-tip="{p["month"]}: {p["neg_rate"]}% negative of {p["n"]}'
        f'{"" if p["avg_rating"] is None else f", avg {p["avg_rating"]}★"}"/>'
        for x, p in zip(xs, tl))
    return (f'<svg viewBox="0 0 {W} {H}" width="100%" role="img" aria-label="Share of negative feedback by month">'
            f'{grid}<polyline points="{pts}" fill="none" stroke="var(--blue)" stroke-width="2" stroke-linejoin="round"/>'
            f'{dots}{labels}</svg>')


def _llm_block(llm):
    if not llm:
        return ""
    pps = "".join(
        f"<div class='pp'><b>{e(p['problem'])}</b>"
        f"<div class='meta'>Severity {e(p['severity'])}/5 · ~{e(p['share_of_quotes'])}% of comments · "
        f"Who: {e(p['who'])} · When: {e(p['trigger'])}</div>"
        f"<div>Likely cause (hypothesis): {e(p['root_cause_hypothesis'])}</div>"
        f"<div><b style='font-size:14px'>{e(p['opportunity'])}</b></div>"
        + "".join(f"<blockquote>{e(q)}</blockquote>" for q in p.get("evidence", [])[:2]) + "</div>"
        for p in llm.get("pain_points", []))
    return f"<p>{e(llm.get('summary'))}</p>{pps}"


def render(s, path):
    areas = s["areas"]
    tiles = [
        (f"{s['n']:,}", "pieces of feedback"),
        (f"{s['avg_rating']}★" if s["avg_rating"] else "–", "average rating"),
        (f"{s['pct_negative']}%", "negative"),
        (f"{s['net_sentiment']:+}", "net sentiment (pos − neg)"),
        (f"{s['churn_signals']:,}", "churn / switching signals"),
    ]
    tiles_html = "".join(f"<div class='tile'><b>{v}</b><span>{k}</span></div>" for v, k in tiles)

    pos, neg = s["pct_positive"], s["pct_negative"]
    split = (f"<div class='split' data-tip='{neg}% negative · {round(100-pos-neg,1)}% neutral · {pos}% positive'>"
             f"<i style='width:{neg}%;background:var(--red)'></i><i style='width:{100-pos-neg}%;background:var(--mid)'></i>"
             f"<i style='width:{pos}%;background:var(--blue)'></i></div>"
             "<div class='legend'><span><i style='background:var(--red)'></i>Negative</span>"
             "<span><i style='background:var(--mid)'></i>Neutral</span><span><i style='background:var(--blue)'></i>Positive</span></div>")

    rows = ""
    for a in areas:
        drag = "" if a["rating_drag"] is None else f"{a['rating_drag']:+.2f}"
        rows += (f"<tr><td><b>{e(a['area'])}</b></td>"
                 f"<td style='width:22%'><div class='bar' data-tip='Opportunity {a['opportunity']}/100'>"
                 f"<i style='width:{a['opportunity']}%'></i></div></td><td class='num'>{a['opportunity']}</td>"
                 f"<td class='num'>{a['pct_of_all_complaints']}%</td><td class='num hide-sm'>{a['negative_rate']}%</td>"
                 f"<td class='num hide-sm'>{a['severity']:.2f}</td><td class='num hide-sm'>{a['momentum']}×</td>"
                 f"<td class='num hide-sm'>{drag}</td></tr>")

    deep = ""
    for a in areas[:8]:
        deep += (f"<div class='card'><b>{e(a['area'])}</b> <span class='meta'>· {a['negative_mentions']} complaints · "
                 f"{a['pct_of_all_complaints']}% of all complaints · {a['churn_mentions']} with churn language</span>"
                 f"{_llm_block(a.get('llm'))}"
                 f"<details{' open' if not a.get('llm') else ''}><summary>Most-agreed-with complaints</summary>"
                 + "".join(_quote(q) for q in a["quotes"]) + "</details></div>")

    src = "".join(f"<tr><td>{e(x['source'])}</td><td class='num'>{x['n']:,}</td><td class='num'>{x['neg_rate']}%</td>"
                  f"<td class='num'>{x['avg_rating'] or '–'}</td></tr>" for x in s["sources"])
    ver = "".join(f"<tr><td>{e(v['source'])}</td><td>{e(v['version'])}</td><td class='num'>{v['n']}</td>"
                  f"<td class='num'>{v['neg_rate']}%</td><td class='num'>{v['avg_rating'] or '–'}</td></tr>"
                  for v in s["versions"])
    emerging = "".join(f"<span class='chip' data-tip='z = {p['z']} (higher = more specific to complaints)'>"
                       f"{e(p['phrase'])}<em>{p['neg_count']}</em></span>" for p in s["emerging"])
    comps = "".join(f"<tr><td>{e(c['competitor'])}</td><td class='num'>{c['mentions']}</td>"
                    f"<td class='num'>{c['in_churn_context']}</td></tr>" for c in s["competitors"])

    dr = s["date_range"]
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{e(s['company'])} Pain Points</title>
<style>{CSS}</style></head><body><main>
<h1>{e(s['company'])}: user pain-point radar</h1>
<p class="sub">{s['n']:,} public reviews & posts · {e(dr[0] or '?')} to {e(dr[1] or '?')} · generated {e(s['generated'])}</p>
<div class="tiles">{tiles_html}</div>
<div class="card">{split}</div>

<h2>Where to go after: opportunity ranking</h2>
<p class="sub">Opportunity = share of complaints × severity × momentum × reach, top area = 100.
"Rating drag" = how far reviews mentioning the area sit below the overall average.</p>
<div class="card scroll"><table><thead><tr><th>Area</th><th colspan="2">Opportunity</th><th class="num">% of complaints</th>
<th class="num hide-sm">Neg. rate</th><th class="num hide-sm">Severity</th><th class="num hide-sm">Momentum</th>
<th class="num hide-sm">Rating drag</th></tr></thead><tbody>{rows}</tbody></table>
<p class="note">{s['pct_complaints_untagged']}% of complaints matched no area. See "Emerging themes" and
"Unfiled complaints" below, then add keywords to <code>radar/taxonomy.py</code>.</p></div>

<h2>Is it getting worse? Share of negative feedback by month</h2>
<div class="card">{_timeline_svg(s['timeline'])}</div>

<h2>Pain points in users' own words</h2>
{deep}

<h2>Emerging themes</h2>
<p class="sub">Phrases far more common in complaints than in praise. Count = negative mentions.</p>
<div class="card chips">{emerging or "<span class='meta'>Not enough data.</span>"}</div>

<div class="grid2">
<div><h2>Unmet needs (feature requests)</h2><div class="card">{''.join(_quote(q) for q in s['feature_requests'][:6]) or "<span class='meta'>None detected.</span>"}</div></div>
<div><h2>Why people leave (churn language)</h2><div class="card">{''.join(_quote(q) for q in s['churn_quotes'][:6]) or "<span class='meta'>None detected.</span>"}</div></div>
</div>

<div class="grid2">
<div><h2>By source</h2><div class="card scroll"><table><thead><tr><th>Source</th><th class="num">N</th><th class="num">Neg.</th><th class="num">Avg ★</th></tr></thead><tbody>{src}</tbody></table></div></div>
<div><h2>By app version</h2><div class="card scroll">{'<table><thead><tr><th>Store</th><th>Version</th><th class="num">N</th><th class="num">Neg.</th><th class="num">Avg ★</th></tr></thead><tbody>' + ver + '</tbody></table>' if ver else "<span class='meta'>No version data.</span>"}</div></div>
</div>

{'<h2>Competitors mentioned</h2><div class="card scroll"><table><thead><tr><th>Competitor</th><th class="num">Mentions</th><th class="num">In churn context</th></tr></thead><tbody>' + comps + '</tbody></table></div>' if comps else ''}

<h2>Unfiled complaints</h2><p class="sub">Negative feedback the taxonomy didn't catch. Read these for blind spots.</p>
<div class="card">{''.join(_quote(q) for q in s['untagged_quotes']) or "<span class='meta'>None.</span>"}</div>

<p class="note">Method: sentiment = VADER text score blended with star rating (65% stars when present).
Areas = keyword taxonomy. Forum posts kept only if they name the company. Public feedback over-represents
angry and very happy users, so treat percentages as relative signals, not population estimates.</p>
</main><div class="tip"></div><script>{JS}</script></body></html>"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(page)


def render_compare(summaries, path):
    """Side-by-side matrix: % of each company's complaints per area."""
    areas = sorted({a["area"] for s in summaries for a in s["areas"]})
    by = [{a["area"]: a for a in s["areas"]} for s in summaries]
    head = "".join(f"<th class='num'>{e(s['company'])}</th>" for s in summaries)
    rows = ""
    for ar in sorted(areas, key=lambda x: -max(b.get(x, {}).get("pct_of_all_complaints", 0) for b in by)):
        cells = ""
        for b in by:
            v = b.get(ar, {}).get("pct_of_all_complaints")
            if v is None:
                cells += "<td class='num meta'>–</td>"
            else:
                alpha = min(1, v / 40)
                cells += (f"<td class='num' style='background:color-mix(in srgb,var(--red) {int(alpha*45)}%,transparent)'"
                          f" data-tip='{v}% of complaints'>{v}%</td>")
        rows += f"<tr><td>{e(ar)}</td>{cells}</tr>"
    kpis = "".join(f"<tr><td>{e(s['company'])}</td><td class='num'>{s['n']:,}</td><td class='num'>{s['avg_rating'] or '–'}</td>"
                   f"<td class='num'>{s['pct_negative']}%</td><td class='num'>{s['net_sentiment']:+}</td></tr>" for s in summaries)
    title = " vs ".join(s["company"] for s in summaries)
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Competitor Pain Comparison</title>
<style>{CSS}</style></head><body><main><h1>{e(title)}</h1>
<p class="sub">Share of each company's complaints that mention an area. Where a rival is weak, users feel the gap.</p>
<div class="card scroll"><table><thead><tr><th>Company</th><th class="num">N</th><th class="num">Avg ★</th>
<th class="num">Negative</th><th class="num">Net</th></tr></thead><tbody>{kpis}</tbody></table></div>
<h2>Complaint mix by area</h2><div class="card scroll"><table><thead><tr><th>Area</th>{head}</tr></thead>
<tbody>{rows}</tbody></table></div></main><div class="tip"></div><script>{JS}</script></body></html>"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(page)


def write_json(s, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(s, f, indent=2, ensure_ascii=False, default=str)
