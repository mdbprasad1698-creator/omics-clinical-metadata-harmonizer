"""
parse_geo_soft.py

Purpose:
Parse a real GEO SOFT family file (downloaded from NCBI) and extract
per-sample metadata into a clean CSV, matching the pipeline's expected
schema. This replaces our earlier hand-typed sample rows with real,
fully-downloaded GEO data.
"""
import csv

from src.config import DATA_RAW

SOFT_FILE = DATA_RAW / "GSE96058_family.soft"
OUT_FILE = DATA_RAW / "geo_omics_sample.csv"
MAX_SAMPLES = 20  # keep the demo small; the real file has 3,273 samples


def parse_samples(path, max_samples=None):
    samples = []
    current = None

    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()

            if line.startswith("^SAMPLE"):
                if current:
                    samples.append(current)
                    if max_samples and len(samples) >= max_samples:
                        break
                current = {"sample_accession": line.split("=")[1].strip()}

            elif current is not None and line.startswith("!Sample_title"):
                current["sample_title"] = line.split("=", 1)[1].strip()

            elif current is not None and line.startswith("!Sample_source_name_ch1"):
                current["source_name"] = line.split("=", 1)[1].strip()

            elif current is not None and line.startswith("!Sample_organism_ch1"):
                current["organism"] = line.split("=", 1)[1].strip()

            elif current is not None and line.startswith("!Sample_characteristics_ch1"):
                value = line.split("=", 1)[1].strip()
                if ":" in value:
                    key, val = value.split(":", 1)
                    key = key.strip().lower().replace(" ", "_")
                    current[key] = val.strip()

        if current and (not max_samples or len(samples) < max_samples):
            samples.append(current)

    return samples


def main():
    print(f"Parsing {SOFT_FILE} ...")
    samples = parse_samples(SOFT_FILE, max_samples=MAX_SAMPLES)
    print(f"Extracted {len(samples)} samples")

    rows = []
    for s in samples:
        rows.append({
            "series_id": "GSE96058",
            "sample_accession": s.get("sample_accession", ""),
            "sample_title": s.get("sample_title", ""),
            "organism": s.get("organism", ""),
            "platform_name": s.get("instrument_model", ""),
            "library_strategy": "RNA-seq",
            "linked_clinical_trial": "NCT02306096",
            "source_name": s.get("source_name", ""),
            "scan-b_external_id": s.get("scan-b_external_id", ""),
            "er_status": s.get("er_status", ""),
            "her2_status": s.get("her2_status", ""),
            "tumor_size": s.get("tumor_size", ""),
        })

    fieldnames = list(rows[0].keys())
    with open(OUT_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} real samples to {OUT_FILE}")


if __name__ == "__main__":
    main()