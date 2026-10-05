#!/usr/bin/env python3
# =========================================================
# app.py  —  QLFS Microdata Explorer  |  Streamlit Web App
# =========================================================
# Run:  streamlit run app.py
# =========================================================

import sys
import io
from pathlib import Path

import pandas as pd
import streamlit as st
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

sys.path.insert(0, str(Path(__file__).parent))
from lookups import MEASURES, INDICATORS
from engine  import (calculate_all_measures_and_categories,
                     get_download_columns, get_display_columns)

# ── Styling ────────────────────────────────────────────────────────────────
NAVY = "1F3864"
WHITE = "FFFFFF"
LGREY = "F5F5F5"
thin  = Side(style="thin", color="CCCCCC")
xborder = Border(top=thin, bottom=thin, left=thin, right=thin)

def xl_hdr(cell, text):
    cell.value = text
    cell.font = Font(bold=True, color=WHITE, name="Arial", size=10)
    cell.fill = PatternFill("solid", start_color=NAVY)
    cell.alignment = Alignment(horizontal="left", vertical="center")
    cell.border = xborder

def xl_cel(cell, value, shade):
    cell.value = value
    cell.font = Font(name="Arial", size=10)
    cell.fill = PatternFill("solid", start_color=LGREY if shade else WHITE)
    cell.alignment = Alignment(vertical="center")
    cell.border = xborder

TABLE_NAMES = {
    "status"         : "stats_sa_qlfs_labour_market_sta",
    "industry"       : "stats_sa_qlfs_industry",
    "occupation"     : "stats_sa_qlfs_occupation",
    "neet"           : "stats_sa_qlfs_neet",
    "underemployment": "stats_sa_qlfs_underemployed",
    "formal_informal": "stats_sa_qlfs_formal_informal_e",
}


def build_excel(all_indicators_results, year, quarter):
    """
    Build one Excel file with one tab per database table.
    Each tab = all measures stacked — ready to load into database as-is.
    """
    wb = Workbook()
    wb.remove(wb.active)

    for indicator_key, all_results in all_indicators_results.items():
        if indicator_key == "none":
            continue

        is_multi     = INDICATORS[indicator_key]["is_multi"]
        dl_cols      = get_download_columns(is_multi)
        master       = all_results.get("__master__", pd.DataFrame())
        if master.empty:
            continue

        sheet_name = TABLE_NAMES.get(indicator_key, indicator_key)[:31]
        ws = wb.create_sheet(title=sheet_name)

        dl = master[[c for c in dl_cols if c in master.columns]]

        # Header row only — no title row
        for ci, col in enumerate(dl.columns, start=1):
            xl_hdr(ws.cell(row=1, column=ci), col)

        # Data rows
        for ri, row in enumerate(dl.itertuples(index=False), start=2):
            shade = ri % 2 == 0
            for ci, val in enumerate(row, start=1):
                import math
                v = None if (isinstance(val, float) and math.isnan(val)) else val
                xl_cel(ws.cell(row=ri, column=ci), v, shade)

        for ci in range(1, len(dl.columns)+1):
            ws.column_dimensions[get_column_letter(ci)].width = 14
        ws.freeze_panes = "A2"

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf


# ── Page config ─────────────────────────────────────────────────────────────
st.set_page_config(page_title="QLFS Microdata Explorer", page_icon="📊", layout="wide")

st.markdown("""
<style>
.block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
.app-header {
    background: linear-gradient(135deg, #1F3864 0%, #2E75B6 100%);
    border-radius: 10px; padding: 1.6rem 2rem; margin-bottom: 1.5rem; color: white;
}
.app-header h1 { font-size: 2rem; font-weight: 700; margin: 0 0 0.25rem 0; color: white; }
.app-header p  { font-size: 0.95rem; margin: 0; color: rgba(255,255,255,0.82); }
.metric-card {
    background: #F0F4FA; border: 1px solid #D5E3F7;
    border-radius: 8px; padding: 1rem 1.25rem; text-align: center;
}
.metric-card.green { background:#E8F5E9; border-color:#A5D6A7; }
.metric-num { font-size: 1.8rem; font-weight: 700; color: #1F3864; }
.metric-lbl { font-size: 0.78rem; color: #555; margin-top: 3px; }
.section-title {
    font-size: 1rem; font-weight: 600; color: #1F3864;
    margin-bottom: 0.5rem; border-left: 4px solid #2E75B6; padding-left: 0.6rem;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="app-header">
    <h1>📊 QLFS Microdata Explorer</h1>
    <p>Calculate labour market estimates directly from Stats SA QLFS unit record microdata
       &nbsp;|&nbsp; ISIbalo Data Portal</p>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### ℹ️ About")
    st.markdown("""
Calculates weighted population estimates
from QLFS unit record microdata (CSV).

**One click → one Excel file** with:
- One tab per measure category
- One master tab with all rows combined
- All measures calculated automatically

**Download:** numeric codes aligned
with the database schema.
""")
    st.divider()
    st.markdown("**measure_type_id reference:**")
    st.markdown("""
| ID | Measure |
|---|---|
| 1 | Gender |
| 2 | Age band |
| 3 | Population group |
| 4 | Marital status |
| 5 | Education status |
""")

# ── Upload ────────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">1. Upload microdata CSV</div>',
            unsafe_allow_html=True)
uploaded = st.file_uploader("Select a QLFS microdata CSV file",
                             type=["csv"], label_visibility="collapsed")
if not uploaded:
    st.info("👆 Upload a QLFS microdata CSV to begin.")
    st.stop()

with st.spinner("Loading file..."):
    df = pd.read_csv(uploaded, low_memory=False)
st.success(f"✅ Loaded **{uploaded.name}** — {len(df):,} rows, {len(df.columns)} columns")

# ── Selection ──────────────────────────────────────────────────────────────
st.divider()
st.markdown('<div class="section-title">2. Choose quarter and year</div>',
            unsafe_allow_html=True)

c1, c2 = st.columns(2)
with c1:
    quarter = st.number_input("Quarter", min_value=1, max_value=4, value=1)
with c2:
    year = st.number_input("Year", min_value=2000, max_value=2100, value=2025)

st.caption("ℹ️ All 6 indicators × all 5 measures will be calculated in one run — "
           "producing 6 database-ready sheets in one Excel file.")

run = st.button("▶  Calculate all indicators", type="primary", use_container_width=True)
if not run:
    st.stop()

# ── Validate ──────────────────────────────────────────────────────────────
required = {"Metro_code", "Weight", "Q14AGE"}
for m_cfg in MEASURES.values():
    required.add(m_cfg["column"])
for ind_cfg in INDICATORS.values():
    if ind_cfg["column"]:
        required.add(ind_cfg["column"])
missing = required - set(df.columns)
if missing:
    st.error(f"Missing required columns: {', '.join(missing)}")
    st.stop()

# ── Calculate ALL indicators × ALL measures ───────────────────────────────
with st.spinner("Calculating all indicators and measures — please wait..."):
    all_indicators_results = {}
    for ind_key in INDICATORS:
        if ind_key == "none":
            continue
        all_indicators_results[ind_key] = calculate_all_measures_and_categories(
            df, ind_key, int(year), int(quarter)
        )

# Use labour market status Gender as reference for summary
ref_results = all_indicators_results.get("status", {})
ref_gender  = ref_results.get("Gender", {})
ref_combined = ref_gender.get("Combined", pd.DataFrame())
national_total = ref_combined["value"].sum() if not ref_combined.empty else 0
total_rows = sum(
    len(res.get("__master__", pd.DataFrame()))
    for res in all_indicators_results.values()
)

is_multi     = True  # for display purposes default
display_cols = get_display_columns(True)

# ── Summary ────────────────────────────────────────────────────────────────
st.divider()
st.markdown('<div class="section-title">Summary</div>', unsafe_allow_html=True)

m1, m2, m3 = st.columns(3)
m1.markdown(f"""<div class="metric-card">
    <div class="metric-num">6</div>
    <div class="metric-lbl">Indicators calculated</div>
</div>""", unsafe_allow_html=True)
m2.markdown(f"""<div class="metric-card green">
    <div class="metric-num">{national_total:,.0f}</div>
    <div class="metric-lbl">Working-age population (15–64) — Gender reference</div>
</div>""", unsafe_allow_html=True)
m3.markdown(f"""<div class="metric-card">
    <div class="metric-num">{total_rows:,}</div>
    <div class="metric-lbl">Total rows across all 6 tables</div>
</div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Preview tabs — one per database table ─────────────────────────────────
st.divider()
st.markdown('<div class="section-title">Preview — one tab per database table</div>',
            unsafe_allow_html=True)

ind_labels = [INDICATORS[k]["label"] for k in all_indicators_results]
tabs = st.tabs(ind_labels)

for tab, ind_key in zip(tabs, all_indicators_results):
    with tab:
        res     = all_indicators_results[ind_key]
        master  = res.get("__master__", pd.DataFrame())
        is_m    = INDICATORS[ind_key]["is_multi"]
        disp_c  = get_display_columns(is_m)
        disp    = master[[c for c in disp_c if c in master.columns]]
        st.markdown(f"**{TABLE_NAMES.get(ind_key, ind_key)}_estimates** — "
                    f"{len(master):,} rows")
        st.dataframe(disp, use_container_width=True, hide_index=True, height=400)

# ── Single Excel download ─────────────────────────────────────────────────
st.divider()
st.markdown('<div class="section-title">Download</div>', unsafe_allow_html=True)
st.markdown("One Excel file — **6 sheets**, one per database table. "
            "Ready to load into the database as-is.")

with st.spinner("Building Excel file..."):
    excel_buf = build_excel(all_indicators_results, int(year), int(quarter))

st.download_button(
    "⬇  Download all database tables (Excel)",
    excel_buf,
    f"qlfs_all_indicators_{year}Q{quarter}.xlsx",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    type="primary",
    use_container_width=True,
)
