"""
pipeline.py

Purpose:
Orchestrates the full harmonization run: load raw sources, normalize
them, load human-approved matches, and use those matches to join all
four sources into one unified catalog.
"""
import json

import pandas as pd

from src.config import DATA_PROCESSED
from src.etl.ingest import load_all
from src.etl.normalize import normalize_source


def load_reviewed_matches() -> list[dict]:
    path = DATA_PROCESSED / "reviewed_matches.json"
    if not path.exists():
        raise FileNotFoundError(
            "No reviewed matches found. Run `python3 -m src.matching.review` first."
        )
    with open(path) as f:
        return json.load(f)


def find_match(matches: list[dict], source_x: str, source_y: str) -> dict | None:
    """Find an approved match between two named sources, if one exists."""
    return next(
        (m for m in matches if {m["source_a"], m["source_b"]} == {source_x, source_y}),
        None,
    )


def build_harmonized_catalog() -> pd.DataFrame:
    sources = {name: normalize_source(df) for name, df in load_all().items()}
    matches = load_reviewed_matches()

    print(f"Using {len(matches)} approved match(es) to join sources:")
    for m in matches:
        print(f"  {m['source_a']}.{m['field_a']}  <->  {m['source_b']}.{m['field_b']}")

    catalog = sources["geo"]

    # Join 1: geo -> sra_instrument (exact match join, e.g. sample_accession)
    geo_sra_match = find_match(matches, "geo", "sra_instrument")
    if geo_sra_match:
        left_col = geo_sra_match["field_a"] if geo_sra_match["source_a"] == "geo" else geo_sra_match["field_b"]
        right_col = geo_sra_match["field_b"] if geo_sra_match["source_a"] == "geo" else geo_sra_match["field_a"]
        catalog = catalog.merge(
            sources["sra_instrument"],
            left_on=left_col,
            right_on=right_col,
            how="left",
            suffixes=("", "_sra"),
        )

    # Join 2: geo -> clinical_trials (exact match join, e.g. NCT ID)
    geo_ct_match = find_match(matches, "geo", "clinical_trials")
    if geo_ct_match:
        left_col = geo_ct_match["field_a"] if geo_ct_match["source_a"] == "geo" else geo_ct_match["field_b"]
        right_col = geo_ct_match["field_b"] if geo_ct_match["source_a"] == "geo" else geo_ct_match["field_a"]
        catalog = catalog.merge(
            sources["clinical_trials"],
            left_on=left_col,
            right_on=right_col,
            how="left",
            suffixes=("", "_trial"),
        )

    # Join 3: catalog -> drugbank (fuzzy substring join, e.g. condition/indication)
    ct_db_match = find_match(matches, "clinical_trials", "drugbank")
    if ct_db_match:
        left_col = ct_db_match["field_a"] if ct_db_match["source_a"] == "clinical_trials" else ct_db_match["field_b"]
        right_col = ct_db_match["field_b"] if ct_db_match["source_a"] == "clinical_trials" else ct_db_match["field_a"]

        catalog[left_col] = catalog[left_col].astype(str).str.lower()
        drugbank_df = sources["drugbank"].copy()
        drugbank_df[right_col] = drugbank_df[right_col].astype(str).str.lower()

        matched_rows = []
        for _, cat_row in catalog.iterrows():
            condition_value = cat_row[left_col]
            related_drugs = drugbank_df[drugbank_df[right_col].str.contains(condition_value, na=False)]
            if len(related_drugs) == 0:
                merged_row = {**cat_row.to_dict(), **{c: None for c in drugbank_df.columns}}
                matched_rows.append(merged_row)
            else:
                for _, drug_row in related_drugs.iterrows():
                    merged_row = {**cat_row.to_dict(), **drug_row.to_dict()}
                    matched_rows.append(merged_row)
        catalog = pd.DataFrame(matched_rows)

    return catalog


if __name__ == "__main__":
    catalog = build_harmonized_catalog()
    print(f"\nHarmonized catalog: {catalog.shape[0]} rows, {catalog.shape[1]} columns")
    print(f"Columns: {list(catalog.columns)}")

    out_path = DATA_PROCESSED / "harmonized_catalog.csv"
    catalog.to_csv(out_path, index=False)
    print(f"\nSaved to {out_path}")