"""
llm_matcher.py

Purpose:
Ask an LLM to propose field-level matches across two data sources that
have no shared column names. For each pair of fields it thinks are
conceptually related, it returns a confidence score and a short reason -
it does NOT apply the match itself, just proposes it for review.

Uses Google's Gemini API (free tier) via the current google-genai package.
"""
import json
import os

from google import genai

MATCH_PROMPT = """You are assisting with metadata harmonization across life-sciences data sources.

Below are field names and sample values from two different data sources.

SOURCE A: {source_a_name}
{source_a_fields}

SOURCE B: {source_b_name}
{source_b_fields}

Propose field-level matches between Source A and Source B: pairs of fields
that represent the same or closely related real-world concept, even if the
field names or format differ.

For each proposed match, return:
- field_a: field name from Source A
- field_b: field name from Source B
- confidence: float 0-1
- rationale: one sentence explaining the match

Only propose matches you can justify. Respond ONLY with a JSON array.
No preamble, no markdown fences.
"""


def _describe_source(df) -> str:
    lines = []
    for col in df.columns:
        sample_vals = df[col].dropna().astype(str).unique()[:3]
        lines.append(f"  - {col}: e.g. {list(sample_vals)}")
    return "\n".join(lines)


def propose_matches(source_a_name, df_a, source_b_name, df_b) -> list[dict]:
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

    prompt = MATCH_PROMPT.format(
        source_a_name=source_a_name,
        source_a_fields=_describe_source(df_a),
        source_b_name=source_b_name,
        source_b_fields=_describe_source(df_b),
    )

    import time

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model="gemini-flash-little-latest",
                contents=prompt,
            )
            break
        except Exception as e:
            if attempt < max_retries - 1:
                wait = 5 * (attempt + 1)
                print(f"  API error ({e}). Retrying in {wait}s...")
                time.sleep(wait)
            else:
                print(f"  Failed after {max_retries} attempts: {e}")
                return None

    raw = response.text.strip()
    raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    try:
        matches = json.loads(raw)
    except json.JSONDecodeError:
        print("WARNING: model didn't return valid JSON:\n", raw)
        return []

    for m in matches:
        m["source_a"] = source_a_name
        m["source_b"] = source_b_name

    return matches


if __name__ == "__main__":
    from src.etl.ingest import load_all

    if not os.environ.get("GEMINI_API_KEY"):
        print("Set GEMINI_API_KEY first. Example:")
        print("  export GEMINI_API_KEY=your-key-here")
    else:
        sources = load_all()
        matches = propose_matches("geo", sources["geo"], "clinical_trials", sources["clinical_trials"])
        for m in matches:
            print(f"{m['field_a']}  <->  {m['field_b']}   (confidence={m['confidence']})")
            print(f"   reason: {m['rationale']}\n")