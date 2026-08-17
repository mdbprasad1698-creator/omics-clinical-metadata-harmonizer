"""
config.py

Purpose:
This file is the single source of truth for file paths used across the project.
Instead of typing folder paths repeatedly in every script (and risking typos or
broken paths if the project moves), every other file imports paths from here.

Author: Durga Menda
"""

from pathlib import Path
# Path is Python's built-in tool for working with file/folder locations

# __file__ is a special built-in variable that always holds the location
# of the current file (config.py itself) - not something we choose or type in.
# .resolve() converts it into a full, unambiguous path (removes any "..").
# .parent.parent walks up two folder levels: config.py -> src/ -> project root.
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Full path to the folder holding raw, unprocessed input data
# (e.g. the original CSV files pulled from GEO, ClinicalTrials.gov, etc.)
DATA_RAW = PROJECT_ROOT / "data" / "raw"

# Full path to the folder holding cleaned/harmonized output data
# (e.g. the final matched catalog after running the ETL + matching pipeline)
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"