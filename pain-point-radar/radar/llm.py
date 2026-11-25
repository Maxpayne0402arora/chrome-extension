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


class LLMError(Exception):
    pass


def available():
    try:
        import anthropic  # noqa: F401
        return True
    except ImportError:
        return False


def analyse_texts(company, area, texts):
    """Send up to ~60 complaints to Claude and get structured pain points back."""
    try:
        import anthropic
    except ImportError as e:
        raise LLMError("pip install anthropic to use Claude") from e
    client = anthropic.Anthropic()
    comments = "\n".join(f"- {t[:600]}" for t in texts)
    try:
        resp = client.beta.messages.create(
            model=MODEL,
            max_tokens=16000,
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",  # retry on a fallback model if the request is declined
            output_config={"effort": "medium", "format": {"type": "json_schema", "schema": SCHEMA}},
            messages=[{"role": "user", "content": PROMPT.format(
                company=company, n=len(texts), area=area, comments=comments)}],
        )
    except anthropic.AuthenticationError as e:
        raise LLMError("Claude auth failed: set ANTHROPIC_API_KEY or run `ant auth login`") from e
    except anthropic.RateLimitError as e:
        raise LLMError("Rate limited by the Claude API; try again in a minute") from e
    except anthropic.APIStatusError as e:
        raise LLMError(f"Claude API error {e.status_code}: {e.message}") from e
    except anthropic.APIConnectionError as e:
        raise LLMError(f"Could not reach the Claude API: {e}") from e
    if resp.stop_reason in ("refusal", "max_tokens"):
        raise LLMError(f"Claude stopped early ({resp.stop_reason})")
    text = "".join(b.text for b in resp.content if b.type == "text")
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise LLMError("Could not parse Claude's answer") from e


def deep_dive(df, summary, top_k=5, per_area=60):
    neg = df[df["label"] == "negative"]
    for area in summary["areas"][:top_k]:
        sub = neg[neg["areas"].map(lambda l, a=area["area"]: a in l)]
        sub = sub.sort_values("likes", ascending=False).head(per_area)
        if len(sub) < 5:
            continue
        print(f"  Claude: analysing '{area['area']}' ({len(sub)} comments)")
        try:
            area["llm"] = analyse_texts(summary["company"], area["area"], list(sub["text"]))
        except LLMError as e:
            print(f"  [warn] {e}", file=sys.stderr)
            if "auth" in str(e).lower() or "install" in str(e):
                break
    return summary
