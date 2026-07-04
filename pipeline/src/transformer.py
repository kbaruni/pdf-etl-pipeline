# =========================================================
# src/transformer.py  —  Stage 4: Transform to output schema
# =========================================================
import re
import logging
import pandas as pd

logger = logging.getLogger(__name__)
REGION = "South Africa"


def _parse_geo(label, metro_lookup, province_lookup, geo_sum_rows, has_metros=True):
    label = label.strip()
    if label.lower() == "south africa":
        return None

    sep = " \u2013 " if " \u2013 " in label else (" - " if " - " in label else None)
    if sep:
        province, sub = label.split(sep, 1)
        prov_id = province_lookup.get(province.strip())
        if "non-metro" in sub.lower():
            return {"province_id": prov_id, "district_id": None, "municipality_id": 9999}
        metro = metro_lookup.get(sub.strip(), {})
        return {
            "province_id"    : metro.get("province_id", prov_id),
            "district_id"    : metro.get("district_id"),
            "municipality_id": metro.get("local_id"),
        }

    prov_id = province_lookup.get(label)
    if prov_id is not None:
        if has_metros and label in geo_sum_rows:
            return None
        return {"province_id": prov_id, "district_id": None, "municipality_id": None}

    return None


def _has_value(row, col):
    """Check if a row has a non-null, non-empty value in the current quarter col."""
    v = row.get(col)
    return v is not None and str(v).strip() not in ("", "None", "nan")


def _make_record(table_key, indicator, measure, quarter, year, value,
                 province_id=None, district_id=None, municipality_id=None):
    return {
        "table_key"      : table_key,
        "region"         : REGION,
        "province_id"    : province_id,
        "district_id"    : district_id,
        "municipality_id": municipality_id,
        "indicator"      : indicator,
        "measure"        : measure,
        "quarter"        : quarter,
        "year"           : year,
        "value"          : value,
    }


# ── Grouped transformer ────────────────────────────────────────────────────

def _transform_grouped(clean_df, config, table_key, current_q_col, quarter, year):
    group_values = config.get("group_values", [])
    indicators   = config.get("indicators", [])
    if isinstance(indicators, str):
        indicators = [indicators]

    group_set = {g.lower(): g for g in group_values}

    # ── Build compound indicator index ────────────────────────────────────
    # e.g. "Pension/retirement fund contribution: Yes"
    # → prefix = "pension/retirement fund contribution"
    # → sub    = "yes"
    compound = {}   # prefix_lower → {sub_lower → canonical_indicator}
    plain    = {}   # label_lower  → canonical_indicator
    for ind in indicators:
        if ": " in ind:
            prefix, sub = ind.split(": ", 1)
            compound.setdefault(prefix.lower(), {})[sub.lower()] = ind
        else:
            plain[ind.lower()] = ind

    records         = []
    current_group   = None
    current_section = None   # for compound indicators

    # Drop lines that are known sum rows inside grouped tables
    sum_labels = {"both sexes", "south africa", "total", "population groups",
                  "age group", "15\u201364 years"}

    for _, row in clean_df.iterrows():
        label       = str(row["label"]).strip()
        label_lower = label.lower()

        # Skip sum rows and empty labels
        if not label or label_lower in sum_labels:
            continue

        # ── Detect compound section header ─────────────────────────────────
        # e.g. "Pension/retirement fund contribution"
        if label_lower in compound:
            current_section = label_lower
            continue

        # ── Detect group header ────────────────────────────────────────────
        if label_lower in group_set:
            current_group = group_set[label_lower]
            # Single-indicator tables: value lives on the group header row
            if len(plain) == 1 and _has_value(row, current_q_col) and not compound:
                ind = list(plain.values())[0]
                records.append(_make_record(
                    table_key, ind, current_group, quarter, year,
                    row.get(current_q_col)
                ))
            continue

        # ── Detect compound sub-row (Yes / No / Don't know) ───────────────
        if current_section and current_group:
            sub_map = compound.get(current_section, {})
            if label_lower in sub_map:
                records.append(_make_record(
                    table_key,
                    sub_map[label_lower],
                    current_group,
                    quarter, year,
                    row.get(current_q_col)
                ))
                continue

        # ── Detect plain indicator ─────────────────────────────────────────
        matched = None
        for ind_lower, ind_canonical in plain.items():
            if label_lower == ind_lower or label_lower.startswith(ind_lower):
                matched = ind_canonical
                break

        if matched:
            measure = current_group or (group_values[0] if len(group_values) == 1 else None)
            if measure:
                records.append(_make_record(
                    table_key, matched, measure, quarter, year,
                    row.get(current_q_col)
                ))

    if not records:
        logger.warning("  [TRANSFORM] No records — %s", table_key)
    return pd.DataFrame(records)


# ── Geography transformer ──────────────────────────────────────────────────

def _transform_geography(clean_df, config, table_key, current_q_col,
                         quarter, year, metro_lookup, province_lookup, geo_sum_rows):
    indicators   = config.get("indicators", [])
    if isinstance(indicators, str):
        indicators = [indicators]
    ind_set      = {i.lower(): i for i in indicators}
    has_metros   = config.get("has_metros", True)
    province_set = set(province_lookup.keys()) | {"South Africa"}

    records     = []
    current_geo = None

    for _, row in clean_df.iterrows():
        label       = str(row["label"]).strip()
        label_lower = label.lower()

        is_province = label in province_set
        is_sub_geo  = " \u2013 " in label or bool(re.match(r".+ - .+", label))

        if is_province or is_sub_geo:
            current_geo = _parse_geo(
                label, metro_lookup, province_lookup, geo_sum_rows, has_metros
            )
            # Single-indicator tables: value is on the geography row itself
            if current_geo is not None and len(indicators) == 1:
                value = row.get(current_q_col)
                if _has_value(row, current_q_col):
                    records.append(_make_record(
                        table_key, indicators[0], None,
                        quarter, year, value,
                        **current_geo
                    ))
            continue

        # Multi-indicator: indicator appears as a sub-row under the geography
        matched = None
        for ind_lower, ind_canonical in ind_set.items():
            if label_lower == ind_lower or label_lower.startswith(ind_lower):
                matched = ind_canonical
                break

        if matched and current_geo is not None:
            records.append(_make_record(
                table_key, matched, None,
                quarter, year, row.get(current_q_col),
                **current_geo
            ))

    if not records:
        logger.warning("  [TRANSFORM] No records — %s", table_key)

    df = pd.DataFrame(records)
    for col in ["province_id", "district_id", "municipality_id"]:
        if col in df.columns:
            df[col] = df[col].where(df[col].notna(), None)
    return df


# ── Public interface ───────────────────────────────────────────────────────

def transform_table(clean_df, table_key, config, current_q_col,
                    quarter, year, metro_lookup, province_lookup, geo_sum_rows):
    if clean_df.empty:
        return pd.DataFrame()

    if config["type"] == "grouped":
        df = _transform_grouped(
            clean_df, config, table_key, current_q_col, quarter, year
        )
    elif config["type"] == "geography":
        df = _transform_geography(
            clean_df, config, table_key, current_q_col,
            quarter, year, metro_lookup, province_lookup, geo_sum_rows
        )
    else:
        logger.error("Unknown type '%s' for %s", config["type"], table_key)
        return pd.DataFrame()

    cols = ["table_key", "region", "province_id", "district_id",
            "municipality_id", "indicator", "measure", "quarter", "year", "value"]
    for c in cols:
        if c not in df.columns:
            df[c] = None
    return df[cols]
