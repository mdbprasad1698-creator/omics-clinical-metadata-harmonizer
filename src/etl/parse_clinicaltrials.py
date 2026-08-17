"""
parse_clinicaltrials.py

Purpose:
Parse the real ClinicalTrials.gov API JSON (downloaded from the live API)
and extract trial-level metadata into a clean CSV, matching the pipeline's
expected schema. Replaces our earlier hand-typed single row with real
values pulled directly from the official record.
"""
import csv
import json

from src.config import DATA_RAW

JSON_FILE = DATA_RAW / "clinicaltrials_live.json"
OUT_FILE = DATA_RAW / "clinicaltrials_sample.csv"


def parse_trial(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    protocol = data["protocolSection"]

    identification = protocol.get("identificationModule", {})
    status = protocol.get("statusModule", {})
    sponsor = protocol.get("sponsorCollaboratorsModule", {})
    design = protocol.get("designModule", {})
    conditions = protocol.get("conditionsModule", {})

    return {
        "nct_id": identification.get("nctId", ""),
        "brief_title": identification.get("briefTitle", ""),
        "status": status.get("overallStatus", ""),
        "study_type": design.get("studyType", ""),
        "sponsor": sponsor.get("leadSponsor", {}).get("name", ""),
        "condition": ", ".join(conditions.get("conditions", [])),
        "phase": ", ".join(design.get("phases", [])) if design.get("phases") else "",
        "enrollment": design.get("enrollmentInfo", {}).get("count", ""),
        "start_date": status.get("startDateStruct", {}).get("date", ""),
    }


def main():
    print(f"Parsing {JSON_FILE} ...")
    row = parse_trial(JSON_FILE)

    fieldnames = list(row.keys())
    with open(OUT_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow(row)

    print(f"Wrote real trial data to {OUT_FILE}")
    for k, v in row.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()