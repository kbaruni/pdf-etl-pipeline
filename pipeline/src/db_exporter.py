# =========================================================
# src/db_exporter.py  —  Database-ready output stage
# =========================================================
# Converts the pipeline text-label output into the numeric
# schema used by the database — identical to microdata output.
# This is proof the pipeline works: same schema, same values,
# produced from the PDF rather than raw survey responses.
#
# Multi-value schema:
#   id | province | district | municipality | year | quarter |
#   indicator_code | measure_type_id | measure_code | value
#
# Simple schema (NEET):
#   id | province | district | municipality | year | quarter |
#   measure_type_id | measure_code | value
# =========================================================

import io
import math
import logging
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

logger = logging.getLogger(__name__)

# ── Indicator code maps (from stats_sa dimension tables) ──────────────────

LABOUR_MARKET_CODES = {
    "Employed"                  : 1,
    "Unemployed"                : 2,
    "Discouraged work-seekers"  : 3,
    "Not economically active"   : 4,
}

INDUSTRY_CODES = {
    "Agriculture"               : 1,
    "Mining"                    : 2,
    "Manufacturing"             : 3,
    "Electricity"               : 4,
    "Construction"              : 5,
    "Trade"                     : 6,
    "Transport"                 : 7,
    "Finance"                   : 8,
    "Community and social services": 9,
    "Private households"        : 10,
    "Other"                     : 11,
}

OCCUPATION_CODES = {
    "Manager"                   : 1,
    "Professional"              : 2,
    "Technical"                 : 3,
    "Clerk"                     : 4,
    "Service worker"            : 5,
    "Skilled agricultural"      : 6,
    "Craft and related trade"   : 7,
    "Plant and machine operator": 8,
    "Elementary"                : 9,
    "Domestic worker"           : 10,
    "Other"                     : 11,
}

# ── Measure code maps (from stats_sa dimension tables) ────────────────────

GENDER_CODES = {
    "Men"   : 1,
    "Male"  : 1,
    "Women" : 2,
    "Female": 2,
}

POPULATION_GROUP_CODES = {
    "Black African" : 1,
    "Black/African" : 1,
    "African/Black" : 1,
    "Coloured"      : 2,
    "Indian/Asian"  : 3,
    "White"         : 4,
}

AGE_BAND_CODES = {
    "15-24 yrs"  : 4,
    "15–24 years": 4,
    "25-34 yrs"  : 6,
    "25–34 years": 6,
    "35-44 yrs"  : 8,
    "35–44 years": 8,
    "45-54 yrs"  : 10,
    "45–54 years": 10,
    "55-64 yrs"  : 12,
    "55–64 years": 12,
}

# ── measure_type_id reference ─────────────────────────────────────────────
# 1=Gender, 2=Age band, 3=Population group, 4=Marital status, 5=Education

# ── Table routing ─────────────────────────────────────────────────────────
# Maps table_key → (db_table_name, indicator_code_map, is_multi)
TABLE_ROUTING = {
    # Labour market status — by sex
    "table2"    : ("stats_sa_qlfs_labour_market_status_estimates", LABOUR_MARKET_CODES, True),
    # Labour market status — by population group
    "table2_1"  : ("stats_sa_qlfs_labour_market_status_estimates", LABOUR_MARKET_CODES, True),
    "table2_5"  : ("stats_sa_qlfs_labour_market_status_estimates", LABOUR_MARKET_CODES, True),
    # Labour market status — by age group
    "table2_2"  : ("stats_sa_qlfs_labour_market_status_estimates", LABOUR_MARKET_CODES, True),
    "table2_6"  : ("stats_sa_qlfs_labour_market_status_estimates", LABOUR_MARKET_CODES, True),
    # Industry — by sex
    "table3_1"  : ("stats_sa_qlfs_industry_estimates",   INDUSTRY_CODES,   True),
    # Occupation — by sex
    "table3_5"  : ("stats_sa_qlfs_occupation_estimates", OCCUPATION_CODES, True),
    # NEET — by sex (simple — no indicator_code)
    "table7_sex": ("stats_sa_qlfs_neet_estimates", None, False),
    # NEET — by age group
    "table7_age": ("stats_sa_qlfs_neet_estimates", None, False),
    # NEET — by population group
    "table7_population_group": ("stats_sa_qlfs_neet_estimates", None, False),
}


def _resolve_measure(measure_label: str):
    """Convert text measure label to (measure_type_id, measure_code)."""
    if measure_label in GENDER_CODES:
        return 1, GENDER_CODES[measure_label]
    if measure_label in POPULATION_GROUP_CODES:
        return 3, POPULATION_GROUP_CODES[measure_label]
    if measure_label in AGE_BAND_CODES:
        return 2, AGE_BAND_CODES[measure_label]
    return None, None


def _resolve_indicator(indicator_label: str, code_map: dict):
    """Convert text indicator label to numeric code using partial matching."""
    if code_map is None:
        return None
    if indicator_label in code_map:
        return code_map[indicator_label]
    ind_lower = indicator_label.lower()
    for key, code in code_map.items():
        if key.lower() in ind_lower:
            return code
    return None


def convert_to_db_schema(pipeline_df: pd.DataFrame) -> dict:
    """
    Convert pipeline text-label output to numeric database schema.

    Args:
        pipeline_df: Pipeline output DataFrame with columns:
                     table_key, province_id, district_id, municipality_id,
                     indicator, measure, quarter, year, value

    Returns:
        dict: {db_table_name: DataFrame} — database-ready, numeric codes only.
    """
    results  = {}
    skipped  = []
    n_mapped = 0

    for table_key, group in pipeline_df.groupby("table_key"):
        routing = TABLE_ROUTING.get(table_key)
        if routing is None:
            skipped.append(table_key)
            continue

        db_table_name, indicator_codes, is_multi = routing
        rows = []

        for _, row in group.iterrows():
            # Skip national totals
            if pd.isna(row.get("province_id")):
                continue

            measure_type_id, measure_code = _resolve_measure(
                str(row.get("measure", "")).strip()
            )
            if measure_type_id is None:
                continue

            try:
                raw_val = float(row["value"])
                if math.isnan(raw_val):
                    continue
                # PDF values are in thousands — convert to actual count
                value = round(raw_val * 1000)
            except (ValueError, TypeError):
                continue

            rec = {
                "province"        : int(row["province_id"]) if pd.notna(row.get("province_id")) else None,
                "district"        : int(row["district_id"]) if pd.notna(row.get("district_id")) else None,
                "municipality"    : int(row["municipality_id"]) if pd.notna(row.get("municipality_id")) else None,
                "year"            : int(row["year"]),
                "quarter"         : int(row["quarter"]),
                "measure_type_id" : measure_type_id,
                "measure_code"    : measure_code,
                "value"           : value,
            }

            if is_multi:
                indicator_code = _resolve_indicator(
                    str(row.get("indicator", "")).strip(), indicator_codes
                )
                if indicator_code is None:
                    continue
                rec["indicator_code"] = indicator_code

            rows.append(rec)
            n_mapped += 1

        if not rows:
            continue

        df = pd.DataFrame(rows)
        cols = (
            ["province", "district", "municipality", "year", "quarter",
             "indicator_code", "measure_type_id", "measure_code", "value"]
            if is_multi else
            ["province", "district", "municipality", "year", "quarter",
             "measure_type_id", "measure_code", "value"]
        )
        df = df[[c for c in cols if c in df.columns]]

        # Stack into existing table if already seen (multiple source tables → same db table)
        if db_table_name in results:
            results[db_table_name] = (
                pd.concat([results[db_table_name], df], ignore_index=True)
                .drop_duplicates()
            )
        else:
            results[db_table_name] = df

    # Add auto-incrementing id
    for name in results:
        results[name] = results[name].reset_index(drop=True)
        results[name].insert(0, "id", range(1, len(results[name]) + 1))

    logger.info(
        f"db_exporter: {n_mapped} rows mapped across {len(results)} tables. "
        f"{len(skipped)} table(s) skipped (no routing): {skipped[:5]}"
    )
    return results


def export_to_excel(db_tables: dict, year: int, quarter: int) -> bytes:
    """
    Export database-ready tables to a single Excel file.
    One sheet per database fact table — same structure as microdata output.
    """
    NAVY  = "1F3864"
    LGREY = "F2F2F2"
    WHITE = "FFFFFF"
    thin  = Side(style="thin", color="CCCCCC")
    bdr   = Border(top=thin, bottom=thin, left=thin, right=thin)

    def hdr(cell, text):
        cell.value     = text
        cell.font      = Font(bold=True, color=WHITE, name="Arial", size=10)
        cell.fill      = PatternFill("solid", start_color=NAVY)
        cell.alignment = Alignment(horizontal="left", vertical="center")
        cell.border    = bdr

    def cel(cell, value, shade):
        v = None if (isinstance(value, float) and math.isnan(value)) else value
        cell.value     = v
        cell.font      = Font(name="Arial", size=10)
        cell.fill      = PatternFill("solid", start_color=LGREY if shade else WHITE)
        cell.alignment = Alignment(vertical="center")
        cell.border    = bdr

    wb = Workbook()
    wb.remove(wb.active)

    for table_name, df in db_tables.items():
        sheet_name = table_name.replace("stats_sa_qlfs_", "")[:31]
        ws = wb.create_sheet(title=sheet_name)

        for ci, col in enumerate(df.columns, start=1):
            hdr(ws.cell(row=1, column=ci), col)
            ws.column_dimensions[get_column_letter(ci)].width = 14

        for ri, row in enumerate(df.itertuples(index=False), start=2):
            shade = ri % 2 == 0
            for ci, val in enumerate(row, start=1):
                cel(ws.cell(row=ri, column=ci), val, shade)

        ws.freeze_panes = "A2"

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf.read()


# ── Geographic-only tables (no measure breakdown) ─────────────────────────
# These tables provide provincial/metro totals without demographic breakdown.
# measure_type_id = 0, measure_code = 0 signals "Total — no breakdown"

GEO_TABLE_ROUTING = {
    "table2_3"       : ("stats_sa_qlfs_labour_market_status_estimates", LABOUR_MARKET_CODES, True),
    "table2_7"       : ("stats_sa_qlfs_labour_market_status_estimates", LABOUR_MARKET_CODES, True),
    "table3_2"       : ("stats_sa_qlfs_industry_estimates",             INDUSTRY_CODES,      True),
    "table3_4"       : ("stats_sa_qlfs_industry_estimates",             INDUSTRY_CODES,      True),
    "table7_province": ("stats_sa_qlfs_neet_estimates",                 None,                False),
}


def convert_geo_tables_to_db_schema(pipeline_df: pd.DataFrame) -> dict:
    """
    Convert geographic-breakdown tables (province/metro totals, no measure)
    to database schema. Uses measure_type_id=0, measure_code=0 to signal
    total population (no demographic breakdown applied).
    """
    results = {}

    for table_key, group in pipeline_df.groupby("table_key"):
        routing = GEO_TABLE_ROUTING.get(table_key)
        if routing is None:
            continue

        db_table_name, indicator_codes, is_multi = routing
        rows = []

        for _, row in group.iterrows():
            if pd.isna(row.get("province_id")):
                continue
            try:
                raw_val = float(row["value"])
                if math.isnan(raw_val):
                    continue
                value = round(raw_val * 1000)
            except (ValueError, TypeError):
                continue

            rec = {
                "province"        : int(row["province_id"]),
                "district"        : int(row["district_id"]) if pd.notna(row.get("district_id")) else None,
                "municipality"    : int(row["municipality_id"]) if pd.notna(row.get("municipality_id")) else None,
                "year"            : int(row["year"]),
                "quarter"         : int(row["quarter"]),
                "measure_type_id" : 0,   # 0 = Total, no demographic breakdown
                "measure_code"    : 0,   # 0 = Total
                "value"           : value,
            }

            if is_multi:
                indicator_code = _resolve_indicator(
                    str(row.get("indicator", "")).strip(), indicator_codes
                )
                if indicator_code is None:
                    continue
                rec["indicator_code"] = indicator_code

            rows.append(rec)

        if not rows:
            continue

        df = pd.DataFrame(rows)
        cols = (
            ["province", "district", "municipality", "year", "quarter",
             "indicator_code", "measure_type_id", "measure_code", "value"]
            if is_multi else
            ["province", "district", "municipality", "year", "quarter",
             "measure_type_id", "measure_code", "value"]
        )
        df = df[[c for c in cols if c in df.columns]]

        if db_table_name in results:
            results[db_table_name] = pd.concat(
                [results[db_table_name], df], ignore_index=True
            ).drop_duplicates()
        else:
            results[db_table_name] = df

    for name in results:
        results[name] = results[name].reset_index(drop=True)
        results[name].insert(0, "id", range(1, len(results[name]) + 1))

    return results


def convert_all_to_db_schema(pipeline_df: pd.DataFrame) -> dict:
    """
    Master function — converts all PDF pipeline output to database schema.
    Combines both demographic breakdowns and geographic totals.
    """
    demo_tables = convert_to_db_schema(pipeline_df)
    geo_tables  = convert_geo_tables_to_db_schema(pipeline_df)

    # Merge — stack geo rows into same tables as demo rows
    all_tables = dict(demo_tables)
    for name, df in geo_tables.items():
        if name in all_tables:
            combined = pd.concat([all_tables[name].drop("id", axis=1),
                                   df.drop("id", axis=1)], ignore_index=True)
            combined = combined.drop_duplicates().reset_index(drop=True)
            combined.insert(0, "id", range(1, len(combined) + 1))
            all_tables[name] = combined
        else:
            all_tables[name] = df

    return all_tables
