# =========================================================
# src/cleaner.py  —  Stage 2: Cleaning + quarter detection
# =========================================================
import re
import logging
import pandas as pd

logger = logging.getLogger(__name__)

PERIOD_TOKENS = ["jan-mar", "apr-jun", "jul-sep", "oct-dec", "thousand", "per cent", "percent"]

MONTH_TO_QUARTER = {
    "jan": 1, "feb": 1, "mar": 1,
    "apr": 2, "may": 2, "jun": 2,
    "jul": 3, "aug": 3, "sep": 3,
    "oct": 4, "nov": 4, "dec": 4,
}

# Fallback column names when detection fails
FALLBACK_COLS = ["Q_minus4", "Q_minus3", "Q_minus2", "Q_minus1", "Q_current"]


def detect_quarter_from_header(header_row: pd.Series) -> tuple[int, int]:
    """
    Parse the period header row to find the current (last) quarter.
    Returns (quarter, year) e.g. (1, 2025).
    Returns (0, 0) if detection fails.
    """
    cells = [str(v).lower().strip() for v in header_row.values if str(v).strip()]

    # Find cells containing month abbreviations and a 4-digit year
    quarters_found = []
    for cell in cells:
        m = re.search(r"(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)", cell)
        y = re.search(r"(20\d{2})", cell)
        if m and y:
            q = MONTH_TO_QUARTER[m.group(1)]
            year = int(y.group(1))
            quarters_found.append((q, year))

    if not quarters_found:
        return (0, 0)

    # The last (rightmost) data column is always the current quarter
    return quarters_found[-1]


def _apply_corrections(text: str, corrections: dict) -> str:
    for bad, good in corrections.items():
        if bad in text:
            text = text.replace(bad, good)
    return text


def _clean_cell(val) -> str:
    if pd.isna(val):
        return ""
    s = str(val).replace("\n", " ").replace("\r", " ")
    return re.sub(r" {2,}", " ", s).strip()


def _is_period_header(row: pd.Series) -> bool:
    text = " ".join(str(v).lower() for v in row.values)
    return any(tok in text for tok in PERIOD_TOKENS)


def _standardise_numeric(val: str):
    v = val.strip()
    if v in ("..", "\u2013", "\u2014", "", "\u2013", "-"):
        return None
    v = v.replace("\u00a0", "").replace(" ", "")
    if "," in v:
        parts = v.split(",")
        if len(parts) == 2 and len(parts[1]) in (1, 2):
            v = parts[0] + "." + parts[1]
        else:
            v = v.replace(",", "")
    try:
        float(v)
        return v
    except ValueError:
        return None


def clean_table(
    raw_df      : pd.DataFrame,
    corrections : dict,
    drop_labels : set  = None,
) -> tuple[pd.DataFrame, str, int, int]:
    """
    Clean raw DataFrame and detect current quarter.

    Returns:
        (clean_df, current_q_col, quarter, year)
        current_q_col: column name for the current quarter e.g. 'Q1_2025'
        quarter, year: detected quarter and year (0, 0 if unknown)
    """
    if raw_df.empty:
        return pd.DataFrame(), "", 0, 0

    df = raw_df.copy()

    # ── 1. Clean cells ──────────────────────────────────────────────────────
    df = df.apply(lambda col: col.map(
        lambda c: _apply_corrections(_clean_cell(c), corrections)
    ))

    # ── 2. Drop fully empty rows/columns ───────────────────────────────────
    df.replace("", pd.NA, inplace=True)
    df.dropna(how="all", inplace=True)
    df.dropna(axis=1, how="all", inplace=True)
    df.reset_index(drop=True, inplace=True)
    df.fillna("", inplace=True)

    if df.empty:
        return pd.DataFrame(), "", 0, 0

    # ── 3. Find period header row ───────────────────────────────────────────
    header_idx = None
    header_row = None
    for i, row in df.iterrows():
        if _is_period_header(row):
            header_idx = i
            header_row = row
            break

    if header_idx is None:
        logger.warning("  Could not detect period header row")
        return pd.DataFrame(), "", 0, 0

    # ── 4. Detect current quarter from header ───────────────────────────────
    quarter, year = detect_quarter_from_header(header_row)
    if quarter and year:
        current_q_col = f"Q{quarter}_{year}"
    else:
        logger.warning("  Could not detect quarter from header — using fallback")
        current_q_col = "Q_current"

    # ── 5. Data rows after header ───────────────────────────────────────────
    data = df.iloc[header_idx + 1:].copy()
    data.reset_index(drop=True, inplace=True)
    data.columns = range(len(data.columns))

    # ── 6. Identify value columns ───────────────────────────────────────────
    value_cols = []
    for c in range(1, len(data.columns)):
        col_vals = [v for v in data[c].tolist() if str(v).strip()]
        if not col_vals:
            continue
        numeric_count = sum(
            1 for v in col_vals
            if re.match(r"^-?[\d\s,.\u00a0]+$", str(v).strip())
        )
        if numeric_count / len(col_vals) > 0.4:
            value_cols.append(c)
        if len(value_cols) == 5:
            break

    if not value_cols:
        logger.warning("  Could not identify value columns")
        return pd.DataFrame(), "", 0, 0

    # ── 7. Build clean output — last value col = current quarter ────────────
    keep     = [0] + value_cols
    clean    = data[keep].copy()
    n_vals   = len(value_cols)

    # Build column names: work backwards from current quarter
    q_map = {1: "Q1", 2: "Q2", 3: "Q3", 4: "Q4"}
    col_names = []
    for i in range(n_vals - 1, -1, -1):
        # i=0 is current quarter, i=1 is one quarter back, etc.
        if quarter and year:
            q = quarter
            y = year
            for _ in range(i):
                q -= 1
                if q == 0:
                    q = 4
                    y -= 1
            col_names.append(f"Q{q}_{y}")
        else:
            col_names.append(FALLBACK_COLS[-(n_vals - i)])
    col_names.reverse()
    clean.columns = ["label"] + col_names

    # ── 8. Standardise numeric values ──────────────────────────────────────
    for col in col_names:
        clean[col] = clean[col].apply(
            lambda v: _standardise_numeric(str(v)) if str(v).strip() else None
        )

    # ── 9. Drop unwanted rows ───────────────────────────────────────────────
    clean = clean[clean["label"].str.strip() != ""].copy()
    if drop_labels:
        clean = clean[~clean["label"].str.strip().isin(drop_labels)].copy()
    rate_pat = r"(rate|ratio|participation|proportion|percentage|as %|per cent)"
    clean = clean[~clean["label"].str.lower().str.contains(rate_pat, na=False)].copy()
    clean.reset_index(drop=True, inplace=True)

    logger.info("  [CLEAN] %d rows  quarter=%s_%s  col=%s",
                len(clean), quarter, year, current_q_col)
    return clean, current_q_col, quarter, year
