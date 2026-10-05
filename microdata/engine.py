# =========================================================
# engine.py  —  Calculation engine
# =========================================================

import pandas as pd
from lookups import metro_code_to_geo, MEASURES, INDICATORS

MEASURE_TYPE_ID = {
    "gender"           : 1,
    "age_band"         : 2,
    "population_group" : 3,
    "marital_status"   : 4,
    "education_status" : 5,
}


def _calc(df, measure_key, measure_code,
          indicator_key, indicator_code, year, quarter):
    """Core calculation — one measure_code + one indicator_code."""
    measure_cfg   = MEASURES[measure_key]
    indicator_cfg = INDICATORS[indicator_key]
    is_multi      = indicator_cfg["is_multi"]

    mask = df[measure_cfg["column"]] == measure_code
    if indicator_cfg["column"] is not None and indicator_code is not None:
        mask = mask & (df[indicator_cfg["column"]] == indicator_code)
    if indicator_cfg["working_age_only"]:
        mask = mask & (df["Q14AGE"] >= 15) & (df["Q14AGE"] <= 64)

    filtered = df.loc[mask, ["Metro_code", "Weight"]].copy()
    grouped  = filtered.groupby("Metro_code")["Weight"].sum().reset_index()
    grouped.columns = ["Metro_code", "value"]

    measure_type_id = MEASURE_TYPE_ID.get(measure_key, 0)
    category_label  = measure_cfg["codes"][measure_code]

    records = []
    for _, row in grouped.iterrows():
        geo = metro_code_to_geo(row["Metro_code"])
        rec = {
            "province"        : geo["province"],
            "district"        : geo["district"],
            "municipality"    : geo["municipality"],
            "year"            : year,
            "quarter"         : quarter,
            "measure_type_id" : measure_type_id,
            "measure_code"    : measure_code,
            "value"           : round(row["value"]),
            "category"        : category_label,
        }
        if is_multi:
            rec["indicator_code"] = indicator_code
        records.append(rec)

    if is_multi:
        cols = ["province","district","municipality","year","quarter",
                "indicator_code","measure_type_id","measure_code","value","category"]
    else:
        cols = ["province","district","municipality","year","quarter",
                "measure_type_id","measure_code","value","category"]

    return pd.DataFrame(records, columns=cols).sort_values("province").reset_index(drop=True)


def calculate_all_categories(df, measure_key, indicator_key, year, quarter):
    """
    Calculate every measure category × every indicator code (if multi-value).
    Returns dict: {tab_label: DataFrame} + "Combined" key.
    """
    measure_cfg   = MEASURES[measure_key]
    indicator_cfg = INDICATORS[indicator_key]
    is_multi      = indicator_cfg["is_multi"]

    results         = {}
    combined_frames = []

    # Determine indicator codes to loop over
    if indicator_cfg["codes"] is not None:
        i_codes = list(indicator_cfg["codes"].keys())
    else:
        i_codes = [None]

    for m_code, m_label in measure_cfg["codes"].items():
        tab_frames = []
        for i_code in i_codes:
            t = _calc(df, measure_key, m_code, indicator_key, i_code, year, quarter)
            tab_frames.append(t)

        tab_df = pd.concat(tab_frames, ignore_index=True)
        sort_cols = (["indicator_code","province"] if is_multi else ["province"])
        tab_df = tab_df.sort_values(sort_cols).reset_index(drop=True)
        tab_df.insert(0, "id", range(1, len(tab_df)+1))
        results[m_label] = tab_df
        combined_frames.append(tab_df)

    if combined_frames:
        combined = pd.concat(combined_frames, ignore_index=True)
        sort_cols = (["indicator_code","province","measure_code"]
                     if is_multi else ["province","measure_code"])
        combined = combined.sort_values(sort_cols).reset_index(drop=True)
        combined["id"] = range(1, len(combined)+1)
        results["Combined"] = combined

    return results


def get_download_columns(is_multi):
    if is_multi:
        return ["id","province","district","municipality","year","quarter",
                "indicator_code","measure_type_id","measure_code","value"]
    return ["id","province","district","municipality","year","quarter",
            "measure_type_id","measure_code","value"]


def calculate_all_measures_and_categories(df, indicator_key, year, quarter):
    """
    Run ALL measures × ALL categories × ALL indicator codes in one go.
    Returns dict: {measure_label: {category_label: DataFrame}}
    Plus a flat combined DataFrame with all rows stacked.
    """
    all_measure_results = {}
    all_frames = []

    for measure_key, measure_cfg in MEASURES.items():
        results = calculate_all_categories(df, measure_key, indicator_key, year, quarter)
        all_measure_results[measure_cfg["label"]] = results
        # Add combined frame for this measure to the master list
        if "Combined" in results:
            all_frames.append(results["Combined"])

    # Master combined — all measures, all categories, all indicator codes
    if all_frames:
        master = pd.concat(all_frames, ignore_index=True)
        is_multi = INDICATORS[indicator_key]["is_multi"]
        sort_cols = (["measure_type_id", "indicator_code", "province", "measure_code"]
                     if is_multi else
                     ["measure_type_id", "province", "measure_code"])
        master = master.sort_values(sort_cols).reset_index(drop=True)
        master["id"] = range(1, len(master) + 1)
        all_measure_results["__master__"] = master

    return all_measure_results


def get_display_columns(is_multi):
    if is_multi:
        return ["id","province","district","municipality","year","quarter",
                "indicator_code","measure_type_id","measure_code","value"]
    return ["id","province","district","municipality","year","quarter",
            "measure_type_id","measure_code","value"]
