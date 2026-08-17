"""
ingest.py

Purpose:
Load the three raw metadata sources (GEO, ClinicalTrails.gov, DrugBank) into
pandas DataFrames. Each source gets its own function so the rest of the project 
can load a source by name without knowing file paths.
"""

import pandas as pd
from src.config import DATA_RAW

def load_geo_samples() -> pd.DataFrame:
    "Load GEO omics sample metadata"
    return pd.read_csv(DATA_RAW/"geo_omics_sample.csv")

def load_clinical_trials() -> pd.DataFrame:
    "Load ClinicalTrails.gov trail metadata"
    return pd.read_csv(DATA_RAW/"clinicaltrials_sample.csv")

def load_drugbank() -> pd.DataFrame:
    return pd.read_csv(DATA_RAW / "drugbank_sample.csv")


def load_sra_instrument() -> pd.DataFrame:
    return pd.read_csv(DATA_RAW / "sra_instrument_sample.csv")


def load_all() -> dict[str, pd.DataFrame]:
    return {
        "geo": load_geo_samples(),
        "clinical_trials": load_clinical_trials(),
        "drugbank": load_drugbank(),
        "sra_instrument": load_sra_instrument(),
    }

if __name__ == "__main__":
    # This block only runs when you execute this file directly
    # (not when another file imports functions from it)
    sources = load_all()
    for name, df in sources.items():
        print(f"\n=== {name} ===")
        print(df)