"""
review.py

Purpose:
Take AI-proposed matches across ALL source pairs and require a human to
explicitly accept or reject each one. This is the validation step: the
AI proposes, a person decides.
"""
import json
import time
from itertools import combinations

from src.config import DATA_PROCESSED
from src.etl.ingest import load_all
from src.matching.llm_matcher import propose_matches

CONFIDENCE_THRESHOLD = 0.85


def review_matches(matches: list[dict]) -> list[dict]:
    accepted = []

    for m in matches:
        print(f"\n  [{m['source_a']} <-> {m['source_b']}]  {m['field_a']}  <->  {m['field_b']}")
        print(f"  confidence: {m['confidence']}")
        print(f"  reason: {m['rationale']}")

        if m["confidence"] >= CONFIDENCE_THRESHOLD:
            print(f"  -> High confidence. Still confirm? [y/n]")
        else:
            print(f"  -> LOW confidence - review carefully. Accept? [y/n]")

        decision = input("  > ").strip().lower()
        print(f"  [DEBUG] received: {repr(decision)}")
        if decision == "y":
            accepted.append(m)
            print("  accepted")
        else:
            print("  rejected")

    return accepted


def main():
    sources = load_all()
    all_matches = []
    skipped_pairs = []

    pairs = list(combinations(sources.keys(), 2))
    for i, (name_a, name_b) in enumerate(pairs):
        print(f"\n{'=' * 60}\nComparing {name_a} <-> {name_b}\n{'=' * 60}")
        matches = propose_matches(name_a, sources[name_a], name_b, sources[name_b])

        if matches is None:
            print("  ⚠ SKIPPED - API call failed after retries, not a real 'no match' result")
            skipped_pairs.append((name_a, name_b))
        elif not matches:
            print("  (no matches proposed - AI found no strong conceptual overlap)")
        else:
            all_matches.extend(matches)

        # Stay under the free tier's requests-per-minute limit - pause between
        # comparisons, but skip the wait after the very last one
        if i < len(pairs) - 1:
            print("  (pausing 15s to respect API rate limits...)")
            time.sleep(15)

    if skipped_pairs:
        print(f"\n⚠ {len(skipped_pairs)} pair(s) were skipped due to API failures: {skipped_pairs}")
        print("  Re-run later to retry these specifically.")

    print(f"\n{len(all_matches)} total match(es) proposed across all source pairs. Review each:")
    final = review_matches(all_matches)

    print(f"\n{len(final)} match(es) confirmed by human review.")
    for m in final:
        print(f"  [{m['source_a']}<->{m['source_b']}] {m['field_a']} <-> {m['field_b']}")

    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    out_path = DATA_PROCESSED / "reviewed_matches.json"
    with open(out_path, "w") as f:
        json.dump(final, f, indent=2)
    print(f"\nSaved to {out_path}")


if __name__ == "__main__":
    main()