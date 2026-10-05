# =========================================================
# run_engine.py — Process ISIbalo raw microdata CSV
# =========================================================
# Purpose:
#   Reads a raw QLFS microdata CSV downloaded from the Stats SA ISIbalo
#   Data Portal, sums the survey weights for each labour market indicator
#   x measure x geography combination, and saves the result as a
#   structured estimates CSV.
#
# Usage:
#   python microdata/run_engine.py
#
# Input:
#   Place the raw QLFS microdata CSV in microdata/data/
#   e.g. microdata/data/QLFS202501.csv
#   (Not included in this repository — download from ISIbalo)
#
# Output:
#   microdata/sample_output/qlfs_indicators_{YEAR}Q{QUARTER}.csv
# =========================================================

import sys
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from engine  import calculate_all_measures_and_categories, get_download_columns
from lookups import INDICATORS

# ── Settings — update these ───────────────────────────────────────────────
YEAR    = 2025
QUARTER = 1

DATA_DIR   = Path(__file__).parent / "data"
OUTPUT_DIR = Path(__file__).parent / "sample_output"
CSV_FILE   = DATA_DIR / f"QLFS{YEAR}{QUARTER:02d}.csv"
OUTPUT     = OUTPUT_DIR / f"qlfs_indicators_{YEAR}Q{QUARTER}.csv"

# ── Check input file ──────────────────────────────────────────────────────
if not CSV_FILE.exists():
    print(f"ERROR: Microdata CSV not found at: {CSV_FILE}")
    print(f"       Download QLFS{YEAR}0{QUARTER}.csv from the ISIbalo Data Portal")
    print(f"       (https://isibaloweb.statssa.gov.za) and place it in microdata/data/")
    sys.exit(1)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ── Load CSV ──────────────────────────────────────────────────────────────
print(f"Loading {CSV_FILE.name} ...")
df = pd.read_csv(CSV_FILE, low_memory=False)
print(f"Loaded: {len(df):,} rows")

# ── Run all indicators ────────────────────────────────────────────────────
all_frames = []
for ind_key in INDICATORS:
    if ind_key == "none":
        continue
    print(f"Calculating {ind_key} ...")
    res    = calculate_all_measures_and_categories(df, ind_key, YEAR, QUARTER)
    master = res.get("__master__", pd.DataFrame())
    if not master.empty:
        all_frames.append(master)
        print(f"  -> {len(master):,} rows")

# ── Combine and save ──────────────────────────────────────────────────────
combined = pd.concat(all_frames, ignore_index=True)
combined = combined.sort_values(
    ["indicator_type", "measure_type_id", "province", "measure_code"]
).reset_index(drop=True)
combined["id"] = range(1, len(combined) + 1)

dl_cols = get_download_columns()
output  = combined[[c for c in dl_cols if c in combined.columns]]

output.to_csv(OUTPUT, index=False)
print(f"\nTotal rows : {len(output):,}")
print(f"Saved      : {OUTPUT}")
