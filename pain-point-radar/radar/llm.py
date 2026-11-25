"""Optional: ask Claude to synthesise each top area's complaints into crisp,
product-ready problem statements. Needs `pip install anthropic` and an
ANTHROPIC_API_KEY (or `ant auth login`). Costs roughly a few cents per area.
"""
from __future__ import annotations

import json
import sys

MODEL = "claude-opus-5-5"

SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["summary", "pain_points"],
    "properties": {
        "summary": {"type": "string"},
        "pain_points": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["problem", "who", "trigger", "root_cause_hypothesis", "severity",
                             "share_of_quotes", "evidence", "opportunity"],
                "properties": {
                    "problem": {"type": "string"},
                    "who": {"type": "string"},
                    "trigger": {"type": "string"},
                    "root_cause_hypothesis": {"type": "string"},
                    "severity": {"type": "integer"},
                    "share_of_quotes": {"type": "integer"},
                    "evidence": {"type": "array", "items": {"type": "string"}},
                    "opportunity": {"type": "string"},
                },
            },
        },
    },
}

PROMPT = """You are helping a product manager find problems worth solving at {company}.
Below are {n} negative user comments that our keyword tagger filed under the area "{area}".
Some may be mis-tagged; ignore those.

Group them into 2-5 distinct, specific pain points. For each one give:
- problem: one sentence in the user's terms ("I paid but the order never got confirmed"), not a category name
- who: which kind of user hits it (new vs repeat, COD vs prepaid, etc.) if the comments show it, else "unclear"
- trigger: the moment in the journey where it happens
- root_cause_hypothesis: your best guess at the operational or product cause, marked as a hypothesis
- severity: 1 (annoyance) to 5 (lost money / lost trust / churn)
- share_of_quotes: roughly what percent of these comments describe this pain point
- evidence: 2-3 short verbatim quotes from the comments
- opportunity: a "How might we..." question a PM could take into discovery
Also write a 2-sentence summary of the area. Only use what the comments say; do not invent facts.

Comments:
{comments}"""


def deep_dive(df, summary, top_k=5, per_area=60):
    try:
        import anthropic
    except ImportError:
        print("  [warn] pip install anthropic to use --llm", file=sys.stderr)
        return summary
    client = anthropic.Anthropic()
    neg = df[df["label"] == "negative"]
    for area in summary["areas"][:top_k]:
        sub = neg[neg["areas"].map(lambda l, a=area["area"]: a in l)]
        sub = sub.sort_values("likes", ascending=False).head(per_area)
        if len(sub) < 5:
            continue
        comments = "\n".join(f"- {t[:600]}" for t in sub["text"])
        print(f"  Claude: analysing '{area['area']}' ({len(sub)} comments)")
        try:
            resp = client.beta.messages.create(
                model=MODEL,
                max_tokens=16000,
                betas=["server-side-fallback-2026-07-01"],
                fallbacks="default",  # retry on a fallback model if the request is declined
                output_config={"effort": "medium",
                               "format": {"type": "json_schema", "schema": SCHEMA}},
                messages=[{"role": "user", "content": PROMPT.format(
                    company=summary["company"], n=len(sub), area=area["area"], comments=comments)}],
            )
        except anthropic.AuthenticationError:
            print("  [warn] Claude auth failed - set ANTHROPIC_API_KEY or run `ant auth login`", file=sys.stderr)
            return summary
        except anthropic.RateLimitError:
            print("  [warn] rate limited by Claude API; skipping remaining areas", file=sys.stderr)
            return summary
        except anthropic.APIStatusError as e:
            print(f"  [warn] Claude API error {e.status_code}: {e.message}", file=sys.stderr)
            continue
        except anthropic.APIConnectionError as e:
            print(f"  [warn] could not reach Claude API: {e}", file=sys.stderr)
            return summary
        if resp.stop_reason in ("refusal", "max_tokens"):
            print(f"  [warn] Claude stopped early ({resp.stop_reason}) on '{area['area']}'", file=sys.stderr)
            continue
        text = "".join(b.text for b in resp.content if b.type == "text")
        try:
            area["llm"] = json.loads(text)
        except json.JSONDecodeError:
            print(f"  [warn] could not parse Claude output for '{area['area']}'", file=sys.stderr)
    return summary
