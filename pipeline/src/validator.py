# =========================================================
# src/validator.py  —  Stage 3: Validation
# =========================================================
import logging
import pandas as pd

logger = logging.getLogger(__name__)


def _row(check_type, description, expected, actual, status, notes=""):
    return {
        "check_type" : check_type,
        "description": description,
        "expected"   : str(expected),
        "actual"     : str(actual),
        "status"     : status,
        "notes"      : notes,
    }


def validate_table(
    clean_df      : pd.DataFrame,
    table_key     : str,
    config        : dict,
    current_q_col : str,
    quarter       : int,
    year          : int,
    trans_df      : pd.DataFrame = None,
    run_ts        : str = "",
) -> pd.DataFrame:
    """
    Validate the transformed output (trans_df) rather than the
    intermediate clean DataFrame. This gives a true picture of
    data quality — if records were produced the pipeline worked.
    """
    results = []

    # ── Check 1: Extraction succeeded ─────────────────────────────────────
    extracted = not clean_df.empty
    results.append(_row(
        "Extraction", "Raw data extracted from PDF",
        "Yes", "Yes" if extracted else "No",
        "PASS" if extracted else "FAIL",
        "" if extracted else "Camelot returned no tables for this page"
    ))

    # ── Check 2: Records produced ──────────────────────────────────────────
    n_records = len(trans_df) if trans_df is not None and not trans_df.empty else 0
    results.append(_row(
        "Records", "Transformed records produced",
        ">0", str(n_records),
        "PASS" if n_records > 0 else "FAIL",
        "" if n_records > 0 else "Transformer produced no output rows"
    ))

    if trans_df is not None and not trans_df.empty:

        # ── Check 3: No null values in current quarter ─────────────────────
        null_vals = trans_df["value"].isna().sum()
        pct_null  = round(null_vals / len(trans_df) * 100, 1)
        results.append(_row(
            "Completeness", "Null values in output",
            "0", str(null_vals),
            "PASS" if null_vals == 0 else "WARN",
            f"{pct_null}% of values suppressed in source PDF" if null_vals else ""
        ))

        # ── Check 4: Indicators present ───────────────────────────────────
        indicators = config.get("indicators", [])
        if isinstance(indicators, str):
            indicators = [indicators]
        # Strip compound suffix for matching (e.g. "Pension: Yes" → "Pension")
        base_inds = set()
        for ind in indicators:
            base_inds.add(ind.split(": ")[0] if ": " in ind else ind)

        actual_inds = set(trans_df["indicator"].dropna().unique())
        # Match by checking if any actual indicator starts with expected base
        missing = []
        for base in base_inds:
            found = any(base.lower() in a.lower() for a in actual_inds)
            if not found:
                missing.append(base)

        results.append(_row(
            "Indicators", "Expected indicators found in output",
            str(len(base_inds)),
            f"{len(base_inds) - len(missing)} of {len(base_inds)}",
            "PASS" if not missing else "WARN",
            f"Not found: {', '.join(missing[:3])}" if missing else ""
        ))

        # ── Check 5: Measures present (grouped tables only) ───────────────
        group_values = config.get("group_values", [])
        if group_values and config.get("type") == "grouped":
            actual_measures = set(trans_df["measure"].dropna().unique())
            missing_m = [g for g in group_values
                         if not any(g.lower() in m.lower() for m in actual_measures)]
            results.append(_row(
                "Measures", "Expected measures found in output",
                str(len(group_values)),
                f"{len(group_values) - len(missing_m)} of {len(group_values)}",
                "PASS" if not missing_m else "WARN",
                f"Not found: {', '.join(missing_m[:3])}" if missing_m else ""
            ))

        # ── Check 6: Geography IDs for geography tables ────────────────────
        if config.get("type") == "geography":
            no_prov = trans_df["province_id"].isna().sum()
            results.append(_row(
                "Geography", "All rows have province_id assigned",
                "0 missing", str(no_prov),
                "PASS" if no_prov == 0 else "WARN",
                f"{no_prov} rows missing province_id" if no_prov else ""
            ))

        # ── Check 7: Quarter and year correct ─────────────────────────────
        wrong_q = ((trans_df["quarter"] != quarter) |
                   (trans_df["year"] != year)).sum()
        results.append(_row(
            "Period", f"All rows tagged Q{quarter} {year}",
            "0 mismatches", str(wrong_q),
            "PASS" if wrong_q == 0 else "FAIL",
            f"{wrong_q} rows have incorrect quarter/year" if wrong_q else ""
        ))

    report = pd.DataFrame(results)
    report.insert(0, "quarter",       quarter)
    report.insert(0, "year",          year)
    report.insert(0, "run_timestamp", run_ts)
    report.insert(0, "table_key",     table_key)

    n_fail = (report["status"] == "FAIL").sum()
    n_warn = (report["status"] == "WARN").sum()
    logger.info("  [VALIDATE] %d checks — %d FAIL  %d WARN", len(report), n_fail, n_warn)
    return report
