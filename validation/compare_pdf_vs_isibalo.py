# =========================================================
# compare_pdf_vs_isibalo.py
# Cross-validation: PDF ETL pipeline vs ISIbalo microdata estimates
# =========================================================
# Purpose:
#   Compares national labour market totals extracted by the PDF ETL
#   pipeline against pre-computed population estimates derived from
#   ISIbalo QLFS microdata (Statistics South Africa).
#
#   The ISIbalo estimates are produced by summing survey weights from
#   the raw microdata CSV using the microdata pipeline
#   (see ../microdata/run_engine.py).  The pre-computed output file
#   used here is:
#       microdata/sample_output/qlfs_indicators_2025Q1.csv
#
#   PDF pipeline values are published in thousands (as in the PDF
#   report).  This script converts them to actual population counts
#   (x 1 000) before comparison.
#
# Usage (from repo root):
#   python validation/compare_pdf_vs_isibalo.py
#
# Inputs (update paths below if needed):
#   PDF_OUTPUT_CSV  — CSV output from the PDF pipeline
#   ISIBALO_CSV     — pre-computed ISIbalo estimates for Q1 2025
# =========================================================

import sys
from pathlib import Path
import pandas as pd

# ── File paths (relative to repo root) ───────────────────────────────────
PDF_OUTPUT_CSV = Path("data/sample_output/all_tables_all_quarters.csv")
ISIBALO_CSV    = Path("microdata/sample_output/qlfs_indicators_2025Q1.csv")

YEAR    = 2025
QUARTER = 1

# ── ISIbalo indicator codes (from microdata/lookups.py) ──────────────────
# indicator_type=1 (labour market status)
# indicator_code: 1=Employed  2=Unemployed  3=Discouraged  4=Other NEA
# measure_type_id=1 (gender): summing both measure_code values gives
# the combined Men + Women national total.
ISIBALO_STATUS_CODES = {
    1: "Employed",
    2: "Unemployed",
    3: "Discouraged work-seekers",
    4: "Other not economically active",
}


def load_pdf_national_totals(csv_path: Path, year: int, quarter: int) -> pd.Series:
    """
    Read the PDF pipeline output CSV and return national totals in actual
    population counts for table2, South Africa, Men + Women combined.

    Values in the PDF (and in the pipeline output) are published in
    thousands; this function multiplies by 1 000 to match ISIbalo counts.
    """
    df = pd.read_csv(csv_path)

    subset = df[
        (df["table_key"] == "table2") &
        (df["region"]    == "South Africa") &
        (df["year"]      == year) &
        (df["quarter"]   == quarter) &
        (df["measure"].isin(["Men", "Women"]))
    ]

    key_indicators = [
        "Employed",
        "Unemployed",
        "Discouraged work-seekers",
        "Not economically active",
        "Labour force",
    ]
    subset = subset[subset["indicator"].isin(key_indicators)]

    # Sum Men + Women, then convert thousands to actual counts
    totals = subset.groupby("indicator")["value"].sum() * 1_000
    return totals


def load_isibalo_national_totals(csv_path: Path, year: int, quarter: int) -> dict:
    """
    Read the ISIbalo pre-computed estimates CSV and return national totals
    for the labour market status indicator (indicator_type=1).

    The CSV was produced by run_engine.py (microdata pipeline), which sums
    survey weights from the raw QLFS microdata for each indicator x measure
    x geography combination.

    Each province has two row types:
      - district=9999  : non-metro remainder of the province
      - metro rows     : one row per metropolitan municipality

    National totals are obtained by summing ALL rows across all provinces
    (both non-metro and metro). Summing both measure_code values (1=Men,
    2=Women) for measure_type_id=1 gives the combined national total.
    """
    df = pd.read_csv(csv_path)

    national = df[
        (df["year"]           == year) &
        (df["quarter"]        == quarter) &
        (df["indicator_type"] == 1) &       # labour market status
        (df["measure_type_id"]== 1)         # gender (Men + Women)
    ]

    totals = {}
    for code, label in ISIBALO_STATUS_CODES.items():
        val = national[national["indicator_code"] == code]["value"].sum()
        totals[label] = int(val)

    # Derived aggregates
    totals["Labour force"] = totals["Employed"] + totals["Unemployed"]
    # Broad NEA (PDF definition) = Discouraged + Other NEA
    totals["Not economically active (broad)"] = (
        totals["Discouraged work-seekers"] +
        totals["Other not economically active"]
    )

    return totals


def print_comparison(pdf_totals: pd.Series, isibalo_totals: dict):
    """Print a formatted side-by-side comparison table."""

    sep = "=" * 84
    print(f"\n{sep}")
    print(f"  Cross-Validation: PDF ETL Pipeline vs ISIbalo Microdata Estimates")
    print(f"  Quarter {QUARTER}, {YEAR}  |  National level  |  South Africa")
    print(sep)
    print(f"  {'Indicator':<36} {'PDF Pipeline':>14} {'ISIbalo':>14} {'Diff':>10} {'%':>6}")
    print(f"  {'-'*36} {'-'*14} {'-'*14} {'-'*10} {'-'*6}")

    # Indicators with identical definitions in both sources
    matched = [
        ("Employed",     "Employed"),
        ("Unemployed",   "Unemployed"),
        ("Labour force", "Labour force"),
    ]
    print(f"\n  Matched indicators (same definition in both sources):")
    for pdf_label, isi_label in matched:
        pdf_v = pdf_totals.get(pdf_label)
        isi_v = isibalo_totals.get(isi_label)
        if pdf_v is None or isi_v is None:
            print(f"  {pdf_label:<36} {'N/A':>14} {'N/A':>14}")
            continue
        diff = int(isi_v) - int(pdf_v)
        pct  = (diff / isi_v) * 100
        print(f"  {pdf_label:<36} {int(pdf_v):>14,} {int(isi_v):>14,} {diff:>+10,} {pct:>+5.2f}%")

    # Indicators where definitions differ
    print(f"\n  Definitional difference (PDF uses broad NEA including discouraged):")
    noted = [
        ("Not economically active", "Not economically active (broad)"),
        ("Discouraged work-seekers", "Discouraged work-seekers"),
    ]
    for pdf_label, isi_label in noted:
        pdf_v = pdf_totals.get(pdf_label)
        isi_v = isibalo_totals.get(isi_label)
        if pdf_v is None or isi_v is None:
            print(f"  {pdf_label:<36} {'N/A':>14} {'N/A':>14}")
            continue
        diff = int(isi_v) - int(pdf_v)
        pct  = (diff / isi_v) * 100
        print(f"  {pdf_label:<36} {int(pdf_v):>14,} {int(isi_v):>14,} {diff:>+10,} {pct:>+5.2f}%")

    broad_isi = isibalo_totals["Not economically active (broad)"]
    broad_pdf = int(pdf_totals.get("Not economically active", 0))
    print(f"\n  Notes:")
    print(f"  1. PDF values are published in thousands; multiplied by 1 000 here.")
    print(f"  2. ISIbalo values are survey-weight sums from the raw QLFS microdata CSV.")
    print(f"  3. NEA in the PDF (P0211) includes discouraged work-seekers (broad NLFS")
    print(f"     definition). ISIbalo reports them separately (narrow definition).")
    print(f"     ISIbalo Discouraged + Other NEA = {broad_isi:,},")
    print(f"     which is within {abs(broad_isi - broad_pdf)/broad_isi*100:.2f}% of the PDF broad NEA ({broad_pdf:,}).")
    print(f"  4. Labour Force = Employed + Unemployed (derived in both sources).")
    print(sep)


def main():
    # Check input files exist
    for path, label in [(PDF_OUTPUT_CSV, "PDF pipeline output"),
                        (ISIBALO_CSV,    "ISIbalo estimates")]:
        if not path.exists():
            print(f"\nERROR: {label} not found at: {path.resolve()}")
            print(f"       Update the path constant at the top of this script.")
            sys.exit(1)

    print(f"Loading PDF pipeline output : {PDF_OUTPUT_CSV}")
    pdf_totals = load_pdf_national_totals(PDF_OUTPUT_CSV, YEAR, QUARTER)

    print(f"Loading ISIbalo estimates   : {ISIBALO_CSV}")
    isibalo_totals = load_isibalo_national_totals(ISIBALO_CSV, YEAR, QUARTER)

    print_comparison(pdf_totals, isibalo_totals)


if __name__ == "__main__":
    main()
