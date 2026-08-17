# Omics ↔ Clinical Trial ↔ Instrument Metadata Harmonizer

A demo pipeline that harmonizes metadata across four heterogeneous, real
public life-sciences data sources using AI-assisted field matching with
human-in-the-loop review.

## The real-world anchor

All four sources describe the same underlying research program: the
Sweden Cancerome Analysis Network – Breast (SCAN-B) initiative.

| Source | What it is | Real ID used here |
|---|---|---|
| GEO (Gene Expression Omnibus) | RNA-seq sample metadata | GSE96058 |
| SRA (Sequence Read Archive) | Instrument/sequencing run metadata | BioProject PRJNA378692 |
| ClinicalTrials.gov | Trial-level registration record | NCT02306096 |
| DrugBank | Drug/molecule data | Trastuzumab, Lapatinib, Imatinib |

GEO explicitly cites the ClinicalTrials.gov ID in its series description,
and shares BioProject/sample accessions with SRA — so these sources are
genuinely connected, not artificially paired.

## The problem this solves

Each source uses different field names for the same real-world concepts:

- GEO's `platform_name` vs SRA's `instrument_model` (same sequencing machine)
- ClinicalTrials' `condition` vs DrugBank's `indication` (same disease)
- No source shares a single universal join key with all the others

## Pipeline

| File | Purpose |
|---|---|
| `data/raw/` | Raw metadata from all 4 sources |
| `src/etl/ingest.py` | Loads all sources into DataFrames |
| `src/etl/schema_profile.py` | Prints columns + sample values side by side |
| `src/etl/normalize.py` | Cleans column names/values before joining |
| `src/matching/llm_matcher.py` | LLM proposes field matches (confidence + rationale) |
| `src/matching/review.py` | Human approves/rejects proposed matches |
| `src/etl/pipeline.py` | Builds the final harmonized catalog from approved matches |

## Quickstart

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

export GEMINI_API_KEY=your-key-here

python3 -m src.etl.schema_profile
python3 -m src.matching.review
python3 -m src.etl.pipeline

## Result

A unified catalog connecting, per row: a sequencing sample, the
instrument that ran it, the clinical trial it's part of, and drugs
relevant to that trial's condition. None of these connections exist
explicitly in any single source — they're derived by matching fields
across all four.

## Known limitations
 - Uses model-agnostic AI-assisted matching. Currently implemented with
  Google's Gemini API; the matching logic (prompt design, confidence
  scoring, JSON parsing) is provider-independent and would work with
  OpenAI's API with a straightforward model-client swap.
- The `condition` ↔ `indication` join uses substring matching first, with
  an LLM-based semantic fallback (`values_match()`) when substring
  matching finds nothing. This was necessary in practice: the real,
  live-pulled ClinicalTrials.gov record uses the MeSH term "Breast
  Neoplasms" while DrugBank uses "breast cancer." Direct equivalence
  checking initially failed too, since the LLM correctly recognized
  these terms have a parent/subtype relationship, not identical meaning —
  the fallback question was refined to check clinical relevance rather
  than strict equivalence, which resolved it correctly.
- GEO and ClinicalTrials.gov data are now pulled from live sources
  (GSE96058 SOFT file, ClinicalTrials.gov API respectively). SRA
  instrument data and DrugBank data are still small representative
  samples, not yet pulled from live sources.