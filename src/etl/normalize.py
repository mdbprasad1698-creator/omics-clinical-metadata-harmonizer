"""
normalize.py

Purpose:
Light cleaning/standardization applied to each source before matching
results get used to build the unified catalog.
"""
import pandas as pd


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Lowercase and strip whitespace from column names."""
    df = df.copy()
    df.columns = [c.strip().lower() for c in df.columns]
    return df


def normalize_strings(df: pd.DataFrame) -> pd.DataFrame:
    """Strip leading/trailing whitespace from all string/object columns."""
    df = df.copy()
    for col in df.select_dtypes(include=["object", "string"]).columns:
        df[col] = df[col].astype(str).str.strip()
    return df


def normalize_source(df: pd.DataFrame) -> pd.DataFrame:
    """Apply all normalization steps to a single source DataFrame."""
    df = normalize_columns(df)
    df = normalize_strings(df)
    return df


if __name__ == "__main__":
    from src.etl.ingest import load_all

    sources = load_all()
    for name, df in sources.items():
        clean = normalize_source(df)
        print(f"\n{name}: {list(clean.columns)}")