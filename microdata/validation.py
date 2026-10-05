# =========================================================
# validation.py  —  Output validation logic
# =========================================================
from lookups import INDICATORS, MEASURES

EXPECTED_PROVINCES     = list(range(1, 10))
EXPECTED_MEASURE_TYPES = [1, 2, 3, 4, 5]
EXPECTED_INDICATOR_TYPES = list(INDICATORS.keys())

EXPECTED_INDICATOR_CODES = {
    "status"         : [1, 2, 3, 4],
    "industry"       : list(range(1, 12)),
    "occupation"     : list(range(1, 12)),
    "neet"           : [1],
    "underemployment": [1],
    "formal_informal": [1, 2],
}

MIN_ROWS_TOTAL = 2000

PASS = "pass"
FAIL = "fail"
WARN = "warn"


def validate_output(all_indicators_results):
    """
    Validate the combined output from all indicators.
    Expects __master__ key in each indicator result.
    Returns summary, checks and details.
    """
    import pandas as pd

    # Collect all masters into one combined table
    frames = []
    for ind_key, res in all_indicators_results.items():
        if ind_key == "none":
            continue
        master = res.get("__master__", pd.DataFrame())
        if not master.empty:
            frames.append(master)

    checks  = []
    details = []

    def check(name, passed, detail="", warning=False):
        status = WARN if warning else (PASS if passed else FAIL)
        checks.append({"name": name, "status": status, "detail": detail})
        if not passed:
            details.append(f"{'⚠️' if warning else '❌'} {name}: {detail}")

    if not frames:
        check("Output produced", False, "No data produced")
        return {
            "summary": {"total":1,"passed":0,"warned":0,"failed":1},
            "checks" : checks,
            "details": details,
        }

    df = pd.concat(frames, ignore_index=True)

    # ── Check 1: Row count ────────────────────────────────────────────────
    check("Minimum row count", len(df) >= MIN_ROWS_TOTAL,
          f"{len(df):,} rows (minimum {MIN_ROWS_TOTAL:,})")

    # ── Check 2: All 9 provinces ──────────────────────────────────────────
    found_p  = sorted(df["province"].dropna().unique().astype(int).tolist())
    missing_p = [p for p in EXPECTED_PROVINCES if p not in found_p]
    check("All 9 provinces present", not missing_p,
          f"Missing: {missing_p}" if missing_p else "All 9 confirmed")

    # ── Check 3: All 5 measure types ──────────────────────────────────────
    found_mt  = sorted(df["measure_type_id"].dropna().unique().astype(int).tolist())
    missing_mt = [m for m in EXPECTED_MEASURE_TYPES if m not in found_mt]
    check("All 5 measure types present", not missing_mt,
          f"Missing: {missing_mt}" if missing_mt else "All 5 confirmed")

    # ── Check 4: All indicator types present ──────────────────────────────
    found_it  = sorted(df["indicator_type"].dropna().unique().tolist())
    expected_it = [k for k in INDICATORS if k != "none"]
    missing_it  = [t for t in expected_it if t not in found_it]
    check("All indicator types present", not missing_it,
          f"Missing: {missing_it}" if missing_it else f"All {len(expected_it)} confirmed")

    # ── Check 5: Indicator codes per type ─────────────────────────────────
    for ind_type, exp_codes in EXPECTED_INDICATOR_CODES.items():
        sub = df[df["indicator_type"] == ind_type]
        if sub.empty:
            check(f"{ind_type} — indicator codes", False, "No rows found")
            continue
        found_codes  = sorted(sub["indicator_code"].dropna().unique().astype(int).tolist())
        missing_codes = [c for c in exp_codes if c not in found_codes]
        check(f"{ind_type} — indicator codes", not missing_codes,
              f"Missing: {missing_codes}" if missing_codes else
              f"All {len(exp_codes)} codes confirmed")

    # ── Check 6: No nulls in key columns ─────────────────────────────────
    key_cols = ["province","year","quarter","indicator_type",
                "indicator_code","measure_type_id","measure_code","value"]
    nulls = {c: int(df[c].isnull().sum())
             for c in key_cols if c in df.columns and df[c].isnull().sum() > 0}
    check("No null values in key columns", not nulls,
          f"Nulls: {nulls}" if nulls else "No nulls")

    # ── Check 7: No negative values ───────────────────────────────────────
    neg = int((df["value"] < 0).sum())
    check("No negative values", neg == 0,
          f"{neg} negative values" if neg else "All values ≥ 0")

    # ── Check 8: No duplicate rows ────────────────────────────────────────
    dedup = ["province","district","year","quarter",
             "indicator_type","indicator_code","measure_type_id","measure_code"]
    dups = int(df.duplicated(subset=[c for c in dedup if c in df.columns]).sum())
    check("No duplicate rows", dups == 0,
          f"{dups} duplicates" if dups else "No duplicates")

    passed = sum(1 for c in checks if c["status"] == PASS)
    warned = sum(1 for c in checks if c["status"] == WARN)
    failed = sum(1 for c in checks if c["status"] == FAIL)

    return {
        "summary": {"total": len(checks), "passed": passed,
                    "warned": warned, "failed": failed},
        "checks" : checks,
        "details": details,
    }
