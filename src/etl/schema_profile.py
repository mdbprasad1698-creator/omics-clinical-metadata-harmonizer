"""
schema_profile.py

Purpose:
Print each data source's column names and sample values side by side.
This is a deliberate "look before you leap" step - before trying to
match fields across sources with AI, we first just look at what we're
working with in plain output.
"""
from src.etl.ingest import load_all


def profile_source(name: str, df) -> None:
    print(f"\n{'=' * 60}")
    print(f"SOURCE: {name}  ({df.shape[0]} rows, {df.shape[1]} columns)")
    print(f"{'=' * 60}")
    for col in df.columns:
        # Grab up to 3 example values from this column, as strings
        sample_vals = df[col].dropna().astype(str).unique()[:3]
        print(f"  {col:30s} -> {list(sample_vals)}")


def main():
    sources = load_all()
    for name, df in sources.items():
        profile_source(name, df)


if __name__ == "__main__":
    main()