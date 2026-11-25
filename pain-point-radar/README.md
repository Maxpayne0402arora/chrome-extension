# Pain-Point Radar

Pull public feedback about any company (Nykaa, Flipkart, Google…), score sentiment,
and **rank which parts of the business hurt users the most**, so you know where to
point your product thinking.

```
Play Store ─┐
App Store  ─┤                ┌─ sentiment (VADER text score + star rating)
Reddit     ─┼─► normalise ──►├─ tag by business area (taxonomy.py)
HackerNews ─┤   + dedupe     ├─ opportunity score per area
Your CSVs  ─┘                ├─ trend, app-version regressions, emerging phrases
                             ├─ churn language, feature requests, competitor mentions
                             └─ (optional) Claude writes problem statements + "How might we…"
                                   ▼
                     report.html · summary.json · feedback_tagged.csv
```

## Quick start

```bash
cd pain-point-radar
pip install -r requirements.txt
python -m radar analyze "Nykaa" --sector beauty,ecommerce --competitors Purplle,Myntra,Tira
open out/nykaa/report.html
```

More examples:

```bash
# Pin the app IDs if auto-resolve picks the wrong app
python -m radar analyze "Flipkart" --play-id com.flipkart.android --appstore-id 742044692 \
  --sector ecommerce --competitors Amazon,Meesho,Myntra

# Tech company: forums matter more than app stores
python -m radar analyze "Google Search" --query "google search" --sources reddit,hn --sector tech

# Add feedback you exported by hand (Trustpilot, X, MouthShut, support tickets, NPS…)
python -m radar analyze "Nykaa" --csv trustpilot.csv --csv twitter.csv

# Have Claude turn the top 5 areas into crisp problem statements (needs ANTHROPIC_API_KEY)
pip install anthropic
python -m radar analyze "Nykaa" --sector beauty,ecommerce --llm

# Benchmark rivals side by side
python -m radar analyze "Purplle" --sector beauty,ecommerce
python -m radar compare out/nykaa/summary.json out/purplle/summary.json
```

CSV import needs a text column (`text`/`review`/`content`/`body`/`comment`/`feedback`);
`date`, `rating`, `title`, `source`, `url` are optional.

## How to read the report

| Metric | Meaning | Why it matters |
|---|---|---|
| **% of complaints** | Share of all negative feedback that mentions the area | How common the pain is |
| **Severity** | Mean negativity of those complaints (0–1) | How much it hurts |
| **Momentum** | Last 30 days' share ÷ earlier share (0.5×–2×) | Is it getting worse? |
| **Reach** | Based on helpful votes/upvotes | How many others agree |
| **Opportunity** | Share × Severity × Momentum × Reach, top = 100 | Where to go after first |
| **Rating drag** | Avg ★ of reviews mentioning the area minus overall avg | Its cost to the store rating |
| **Churn language** | "uninstalled", "switched to X", "never again"… | Pain that costs the company customers |

Then: **Emerging themes** shows phrases that come up far more in complaints than in
praise, which catches what the taxonomy misses. **Unfiled complaints** lists negative
feedback with no area. Read both and add keywords to `radar/taxonomy.py`. Tuning that
file to the company's domain matters more than anything else you can change.

Sector packs: `ecommerce`, `beauty`, `food_delivery`, `fintech`, `tech` (combine with commas).

## Caveats

- Public feedback over-represents angry and delighted users. Treat numbers as *relative*
  (area A vs area B, this month vs last), not as population estimates.
- VADER is an English lexicon. Hinglish and other languages get scored mostly from stars.
  For forums without stars, use `--llm` or spot-check the quotes.
- Reddit throttles anonymous scraping. If you get 403/429s, create a free "script" app and use PRAW.
- Respect each site's terms. For sites that forbid scraping (Trustpilot, X, Glassdoor…),
  export or copy the text by hand and use `--csv`.

---

# Playbook: what else to analyse

Sentiment tells you *how* people feel. These analyses tell you *what to build*.
The ones marked ✅ are built into the tool.

### 1. Size the problem
- ✅ **Opportunity ranking by area**: frequency × severity × trend × reach.
- ✅ **Rating drag**: which area pulls the star rating down the most. This is a revenue lever, since rating drives install conversion.
- **Impact × Satisfaction gap** (Ulwick's Opportunity Algorithm): survey 30–50 users on how
  important each job is and how satisfied they are with it, then score `importance + max(importance − satisfaction, 0)`.
  Use the radar to pick which jobs go on the survey.

### 2. Find the moment it breaks
- **Journey-stage mapping**: re-bucket areas into Discover → Evaluate → Buy → Wait → Receive → Use → Return/Support.
  Most marketplaces bleed in *Wait* and *Return*, not *Discover*.
- ✅ **App-version regressions**: % negative by release, which catches bad updates within days.
- ✅ **Trend over time**: spot spikes, then line them up with sales events, price changes and outages.

### 3. Understand who hurts
- **Segment the complaints**: COD vs prepaid, metro vs tier-2/3, new vs loyal (look for "been using for 5 years"),
  Android vs iOS (already split by source in the report).
- **Jobs-to-be-Done coding**: rewrite the top 100 complaints as "When ___, I want to ___, so I can ___".
  `--llm` gives you a first draft.

### 4. Measure intent, not just mood
- ✅ **Churn and switching language**, plus **who users are leaving for** (`--competitors`).
- ✅ **Feature requests / unmet needs** ("please add", "wish there was").
- **Workarounds**: "I have to screenshot…", "I use Google to search Nykaa". A workaround is a validated
  need that users are already paying for in effort.

### 5. Benchmark the gap
- ✅ **Competitor complaint mix** (`compare`): if 30% of Nykaa's complaints are about authenticity
  but only 8% of a rival's, that gap is a position you can own.
- **Praise mining on rivals**: run the radar on a competitor and read its *positive* reviews. That shows
  what "good" looks like to the same users.

### 6. Check if the company is fixing it
- **Developer-response rate**: Play/App Store reviews show whether the company replies and how fast.
  Frequent pain with no reply is neglected ground.
- **Persistence**: an area that ranks in the top 3 for 12+ months is structural (logistics, policy), not a bug.
  That makes it harder to fix and more defensible once you do.

### 7. Then validate it offline
The radar finds hypotheses. Before building, run 5–8 user interviews per top pain point and look for
**frequency** (weekly or yearly?), **cost** (money, time, embarrassment) and **current alternatives**.

---

# Where to find public feedback

| Source | Best for | How to get it |
|---|---|---|
| ✅ **Google Play** | Volume, versions, Android / Bharat users | built in (`google-play-scraper`) |
| ✅ **Apple App Store** | Higher-spend, metro users | built in (public RSS, last ~500 reviews) |
| ✅ **Reddit** | Honest long-form stories. In India try r/india, r/IndianSkincareAddicts, r/IndianFashionAddicts, r/developersIndia, r/CreditCardsIndia, r/LegalAdviceIndia | built in (public JSON) or PRAW |
| ✅ **Hacker News** | Tech/dev products (Google, Stripe, Vercel) | built in (Algolia API) |
| **X / Twitter** | Real-time escalations: people @-ing `@NykaaCare`, `@flipkartsupport` | X API (paid) or manual export → `--csv` |
| **Consumer complaint portals** | Serious money/legal pain: National Consumer Helpline (consumerhelpline.gov.in), ConsumerComplaints.in, voxya | manual → `--csv` |
| **Review sites** | Trustpilot, MouthShut (popular in India), Sitejabber, G2/Capterra for B2B | export / copy → `--csv` |
| **YouTube comments** | Unboxings, "Nykaa haul", "Flipkart fake product" videos | YouTube Data API (free quota) → `--csv` |
| **Quora** | "Is Nykaa genuine?" type trust questions | manual → `--csv` |
| **Facebook groups / Telegram / WhatsApp communities** | Niche segments (skincare, deal hunters) | manual, and respect group rules |
| **Instagram comments** | Beauty/fashion brand posts | manual → `--csv` |
| **Glassdoor / AmbitionBox** | *Employee* pain, which often predicts customer pain (ops, support staffing) | manual → `--csv` |
| **Google Maps reviews** | Offline stores, dark stores, warehouses (Nykaa Luxe stores, Flipkart hubs) | Places API → `--csv` |
| **Community forums** | Google Product Forums / Support Community, Apple Discussions | manual → `--csv` |
| **Chrome Web Store / extension reviews** | Browser-extension products | manual → `--csv` |
| **Downdetector** | Outage frequency and timing | manual |
| **News and RBI/SEBI/regulator notices** | Policy-level pain (fintech, insurance) | manual |
| **Your own data (once you have users)** | Support tickets, NPS verbatims, sales-call notes, churn surveys | export → `--csv` |
