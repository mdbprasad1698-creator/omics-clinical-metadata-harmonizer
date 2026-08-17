"""
validate.py

Purpose:
Dedicated data-quality validation layer, run independently of the AI
matching logic. Checks structural integrity of each source before
harmonization, and checks join coverage after the pipeline runs -
answering "how do we know the harmonized catalog is trustworthy?"
rather than just "did the code run without crashing?"
"""
import pandas as pd

from src.etl.ingest import load_all

REQUIRED_FIELDS = {
    "geo": ["sample_accession", "sample_title", "series_id"],
    "clinical_trials": ["nct_id"],
    "drugbank": ["drugbank_id", "drug_name"],
    "sra_instrument": ["run_accession", "sample_accession"],
}


def validate_required_fields(source_name: str, df: pd.DataFrame) -> list[str]:
    """Check that required fields exist and have no missing values."""
    issues = []
    required = REQUIRED_FIELDS.get(source_name, [])
    for field in required:
        if field not in df.columns:
            issues.append(f"[{source_name}] Missing required column: {field}")
        elif df[field].isna().any():
            missing_count = df[field].isna().sum()
            issues.append(f"[{source_name}] {missing_count} row(s) missing value for required field: {field}")
    return issues


def validate_unique_ids(source_name: str, df: pd.DataFrame) -> list[str]:
    """Check for duplicate values in the source's primary identifier column."""
    issues = []
    id_col = REQUIRED_FIELDS.get(source_name, [None])[0]
    if id_col and id_col in df.columns:
        dupes = df[df.duplicated(subset=[id_col], keep=False)]
        if len(dupes) > 0:
            issues.append(f"[{source_name}] {len(dupes)} duplicate value(s) found in {id_col}")
    return issues


def validate_unmapped_fields(source_name: str, df: pd.DataFrame, matches: list[dict]) -> list[str]:
    """Flag fields in a source that never appeared in any approved match."""
    matched_fields = set()
    for m in matches:
        if m["source_a"] == source_name:
            matched_fields.add(m["field_a"])
        if m["source_b"] == source_name:
            matched_fields.add(m["field_b"])

    unmapped = [c for c in df.columns if c not in matched_fields]
    if unmapped:
        return [f"[{source_name}] {len(unmapped)} field(s) never used in any approved match: {unmapped}"]
    return []


def validate_join_coverage(catalog: pd.DataFrame, joined_column: str, source_label: str) -> list[str]:
    """Check what fraction of rows successfully joined vs. fell through as NaN."""
    issues = []
    if joined_column in catalog.columns:
        total = len(catalog)
        missing = catalog[joined_column].isna().sum()
        coverage_pct = 100 * (total - missing) / total if total else 0
        if missing > 0:
            issues.append(
                f"[join coverage] {source_label}: {missing}/{total} rows "
                f"({100 - coverage_pct:.0f}%) did not match any {joined_column} - "
                f"expected if source data sizes differ"
            )
    return issues


def run_all_validations():
    from src.etl.pipeline import load_reviewed_matches  # local import avoids circular import at module load

    sources = load_all()
    matches = load_reviewed_matches()

    all_issues = []
    for name, df in sources.items():
        all_issues += validate_required_fields(name, df)
        all_issues += validate_unique_ids(name, df)
        all_issues += validate_unmapped_fields(name, df, matches)

    print(f"\n{'=' * 60}\nVALIDATION REPORT\n{'=' * 60}")
    if not all_issues:
        print("No issues found.")
    else:
        for issue in all_issues:
            print(f"  ⚠ {issue}")
    print(f"\n{len(all_issues)} item(s) flagged for review (unmapped fields are expected — most fields are descriptive, not join keys).")
    return all_issues


if __name__ == "__main__":
    run_all_validations()