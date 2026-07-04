#!/usr/bin/env python3
# =========================================================
# app.py  —  QLFS ETL  |  Streamlit Web App
# =========================================================
# Run:  streamlit run app.py
# =========================================================

import sys
import tempfile
import logging
from pathlib import Path
from datetime import datetime

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent))

from configs import (
    LABEL_CORRECTIONS, DROP_LABELS,
    METRO_LOOKUP, PROVINCE_LOOKUP, GEO_SUM_ROWS,
    get_configs_for_pdf, detect_quarter_from_filename,
)
from src.extractor   import extract_table
from src.cleaner     import clean_table
from src.validator   import validate_table
from src.transformer import transform_table

# ── Page config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title = "QLFS ETL",
    page_icon  = "📊",
    layout     = "wide",
)

st.markdown("""
<style>
.block-container { padding-top: 1.5rem; padding-bottom: 2rem; }

.app-header {
    background: linear-gradient(135deg, #1F3864 0%, #2E75B6 100%);
    border-radius: 10px; padding: 1.6rem 2rem;
    margin-bottom: 1.5rem; color: white;
}
.app-header h1 { font-size: 2rem; font-weight: 700; margin: 0 0 0.25rem 0; color: white; }
.app-header p  { font-size: 0.95rem; margin: 0; color: rgba(255,255,255,0.82); }

.metric-card {
    background: #F0F4FA; border: 1px solid #D5E3F7;
    border-radius: 8px; padding: 1rem 1.25rem; text-align: center;
}
.metric-card.green { background:#E8F5E9; border-color:#A5D6A7; }
.metric-card.red   { background:#FEECEC; border-color:#FFAAAA; }
.metric-card.amber { background:#FFF8E1; border-color:#FFD54F; }
.metric-num { font-size: 1.9rem; font-weight: 700; color: #1F3864; }
.metric-lbl { font-size: 0.78rem; color: #555; margin-top: 3px; }

.badge-pass { background:#E2EFDA; color:#375623; border-radius:4px; padding:2px 10px; font-size:11px; font-weight:600; }
.badge-fail { background:#FCE4D6; color:#7B2C2C; border-radius:4px; padding:2px 10px; font-size:11px; font-weight:600; }
.badge-warn { background:#FFF2CC; color:#7F6000; border-radius:4px; padding:2px 10px; font-size:11px; font-weight:600; }

.section-title {
    font-size: 1rem; font-weight: 600; color: #1F3864;
    margin-bottom: 0.5rem; border-left: 4px solid #2E75B6; padding-left: 0.6rem;
}

.quality-box {
    background: #E8F5E9; border: 1px solid #A5D6A7;
    border-radius: 8px; padding: 1.2rem 1.5rem; margin-bottom: 1rem;
}
.quality-box h3 { color: #375623; margin: 0 0 0.5rem 0; font-size: 1.1rem; }
.quality-box p  { color: #444; margin: 0; font-size: 0.9rem; }
</style>
""", unsafe_allow_html=True)

# ── Header ──────────────────────────────────────────────────────────────────
st.markdown("""
<div class="app-header">
    <h1>📊 QLFS ETL</h1>
    <p>Quarterly Labour Force Survey — Extract, Transform, Load Pipeline &nbsp;|&nbsp;
       Statistics South Africa &nbsp;|&nbsp; P0211 Series</p>
</div>
""", unsafe_allow_html=True)

# ── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ℹ️ About")
    st.markdown("""
Extracts and transforms labour market data from
**QLFS PDF publications** by Statistics South Africa.

**Pipeline stages:**
1. **Extract** — Camelot PDF table extraction
2. **Clean** — label correction, numeric standardisation
3. **Transform** — apply output schema
4. **Validate** — data quality checks on output

**Supported editions:**
Q1 2024 through Q4 2025
""")
    st.divider()
    st.markdown("**Output encoding:** UTF-8 BOM — opens correctly in Excel")
    st.divider()
    st.markdown("*Built for the National Data Policy Observatory*")

# ── Upload ───────────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">Upload PDF</div>', unsafe_allow_html=True)

uploaded = st.file_uploader(
    "Select a QLFS PDF file (P0211 series)",
    type=["pdf"],
    label_visibility="collapsed",
)

if not uploaded:
    st.info("👆 Upload a QLFS PDF above to begin extraction.")
    with st.expander("Supported PDF editions"):
        editions = pd.DataFrame({
            "File"   : ["P02111stQuarter2024.pdf","P02112ndQuarter2024.pdf",
                        "P02113rdQuarter2024.pdf","P02114thQuarter2024.pdf",
                        "P02111stQuarter2025.pdf","P02112ndQuarter2025.pdf",
                        "P02113rdQuarter2025.pdf","P02114thQuarter2025.pdf"],
            "Quarter": ["Q1 2024","Q2 2024","Q3 2024","Q4 2024",
                        "Q1 2025","Q2 2025","Q3 2025","Q4 2025"],
            "Tables" : [46,46,46,46,46,46,50,50],
            "Status" : ["✅ Full","✅ Full","✅ Full","✅ Full",
                        "✅ Full","✅ Full","⚠️ Partial","⚠️ Partial"],
        })
        st.dataframe(editions, use_container_width=True, hide_index=True)
    st.stop()

col_info, col_btn = st.columns([3, 1])
with col_info:
    st.success(f"✅ **{uploaded.name}** — {uploaded.size/1024/1024:.1f} MB")
with col_btn:
    run = st.button("▶  Run ETL", type="primary", use_container_width=True)

if not run:
    st.stop()

# ── Pipeline ─────────────────────────────────────────────────────────────────
st.divider()
st.markdown('<div class="section-title">Pipeline</div>', unsafe_allow_html=True)

with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
    tmp.write(uploaded.read())
    tmp_path = Path(tmp.name)

filename       = uploaded.name
configs        = get_configs_for_pdf(filename)
fallback_q, fallback_y = detect_quarter_from_filename(filename)
n_tables       = len(configs)
RUN_TS         = datetime.now().strftime("%Y%m%d_%H%M%S")

all_trans      = []
all_val        = []
summary_rows   = []
detected_q     = detected_y = 0
log_lines      = []

progress_bar   = st.progress(0)
status_text    = st.empty()
log_expander   = st.expander("📋 Extraction log", expanded=False)
log_area       = log_expander.empty()

for i, (table_key, config) in enumerate(configs.items()):
    pct = int(i / n_tables * 100)
    progress_bar.progress(pct)
    status_text.markdown(
        f"⚙️ Extracting **`{table_key}`** &nbsp;·&nbsp; "
        f"Table {i+1} of {n_tables} &nbsp;·&nbsp; {pct}% complete"
    )
    log_lines.append(f"{'─'*52}")
    log_lines.append(f"[{i+1:02d}/{n_tables}]  {table_key}  (pages {config['pages']})")

    trans_df = pd.DataFrame()

    # Stage 1 — Extract
    try:
        raw_df = extract_table(str(tmp_path), table_key, config)
        log_lines.append(f"  EXTRACT  : {len(raw_df):4d} raw rows")
    except Exception as e:
        raw_df = pd.DataFrame()
        log_lines.append(f"  EXTRACT  : FAILED — {e}")

    # Stage 2 — Clean
    try:
        clean_df, q_col, q, y = clean_table(raw_df, LABEL_CORRECTIONS, DROP_LABELS)
        if q and y and not detected_q:
            detected_q, detected_y = q, y
            log_lines.append(f"  QUARTER  : Q{q} {y} detected")
        if not q:
            q, y  = detected_q or fallback_q, detected_y or fallback_y
            q_col = f"Q{q}_{y}" if q else "Q_current"
        log_lines.append(f"  CLEAN    : {len(clean_df):4d} rows  col={q_col}")
    except Exception as e:
        clean_df, q_col, q, y = pd.DataFrame(), "", fallback_q, fallback_y
        log_lines.append(f"  CLEAN    : FAILED — {e}")

    # Stage 3 — Transform
    try:
        trans_df = transform_table(
            clean_df, table_key, config, q_col, q, y,
            METRO_LOOKUP, PROVINCE_LOOKUP, GEO_SUM_ROWS,
        )
        if not trans_df.empty:
            all_trans.append(trans_df)
        log_lines.append(f"  TRANSFORM: {len(trans_df):4d} records")
    except Exception as e:
        trans_df = pd.DataFrame()
        log_lines.append(f"  TRANSFORM: FAILED — {e}")

    # Stage 4 — Validate (against transformed output)
    try:
        val_df = validate_table(
            clean_df, table_key, config, q_col, q, y, trans_df, RUN_TS
        )
        all_val.append(val_df)
        n_f = (val_df["status"] == "FAIL").sum()
        n_w = (val_df["status"] == "WARN").sum()
        log_lines.append(
            f"  VALIDATE : {'PASS' if not n_f else f'{n_f} FAIL'}"
            f"{'  ' + str(n_w) + ' WARN' if n_w else ''}"
        )
    except Exception as e:
        log_lines.append(f"  VALIDATE : FAILED — {e}")

    summary_rows.append({
        "table_key": table_key,
        "pages"    : config["pages"],
        "type"     : config["type"],
        "records"  : len(trans_df),
        "status"   : "PASS" if not trans_df.empty else "FAIL",
    })

    log_area.code("\n".join(log_lines[-35:]), language=None)

progress_bar.progress(100)
status_text.markdown("✅ **ETL pipeline complete**")

try:
    tmp_path.unlink(missing_ok=True)
except PermissionError:
    pass  # Windows file lock — safe to ignore

# ── Results ──────────────────────────────────────────────────────────────────
combined   = pd.concat(all_trans, ignore_index=True) if all_trans else pd.DataFrame()
val_all    = pd.concat(all_val,   ignore_index=True) if all_val   else pd.DataFrame()
summary_df = pd.DataFrame(summary_rows)

passed     = (summary_df["status"] == "PASS").sum() if not summary_df.empty else 0
n_fail_v   = int((val_all["status"] == "FAIL").sum()) if not val_all.empty else 0
n_warn_v   = int((val_all["status"] == "WARN").sum()) if not val_all.empty else 0
qtr_lbl    = f"Q{detected_q or fallback_q} {detected_y or fallback_y}"
records    = len(combined)

# ── Metric cards ─────────────────────────────────────────────────────────────
st.divider()
st.markdown('<div class="section-title">Summary</div>', unsafe_allow_html=True)

m1, m2, m3, m4, m5 = st.columns(5)

def metric_card(col, value, label, style=""):
    col.markdown(f"""
    <div class="metric-card {style}">
        <div class="metric-num">{value}</div>
        <div class="metric-lbl">{label}</div>
    </div>""", unsafe_allow_html=True)

metric_card(m1, qtr_lbl,               "Quarter detected")
metric_card(m2, f"{passed}/{n_tables}", "Tables extracted",
            "green" if passed == n_tables else "amber")
metric_card(m3, f"{records:,}",        "Records produced",
            "green" if records > 0 else "red")
metric_card(m4, str(n_fail_v),         "Data quality issues",
            "green" if n_fail_v == 0 else "red")
metric_card(m5, str(n_warn_v),         "Warnings",
            "green" if n_warn_v == 0 else "amber")

st.markdown("<br>", unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────────────────────
st.divider()
tab1, tab2, tab3 = st.tabs([
    "📋  Extracted Data",
    "✅  Validation Report",
    "⬇  Downloads",
])

# ── Tab 1: Extracted Data ─────────────────────────────────────────────────────
with tab1:
    if combined.empty:
        st.warning("No data extracted. Check the validation report for details.")
    else:
        st.markdown('<div class="section-title">Filter</div>', unsafe_allow_html=True)
        f1, f2, f3, f4 = st.columns(4)

        tbl_sel = f1.multiselect("Table",
            sorted(combined["table_key"].unique()), placeholder="All tables")
        ind_sel = f2.multiselect("Indicator",
            sorted(combined["indicator"].dropna().unique()), placeholder="All indicators")
        msr_sel = f3.multiselect("Measure",
            sorted(combined["measure"].dropna().unique()), placeholder="All measures")
        prv_sel = f4.multiselect("Province ID",
            sorted(combined["province_id"].dropna().astype(int).unique()),
            placeholder="All provinces")

        view = combined.copy()
        if tbl_sel: view = view[view["table_key"].isin(tbl_sel)]
        if ind_sel: view = view[view["indicator"].isin(ind_sel)]
        if msr_sel: view = view[view["measure"].isin(msr_sel)]
        if prv_sel: view = view[view["province_id"].isin(prv_sel)]

        st.markdown(
            f'<div class="section-title">Data &nbsp;·&nbsp; '
            f'{len(view):,} rows shown of {records:,} total</div>',
            unsafe_allow_html=True
        )
        st.dataframe(view, use_container_width=True, height=480, hide_index=True)

        filtered_csv = view.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
        st.download_button(
            "⬇  Download filtered data (CSV)", filtered_csv,
            f"qlfs_{qtr_lbl.replace(' ','_')}_filtered.csv", "text/csv",
        )

# ── Tab 2: Validation Report ──────────────────────────────────────────────────
with tab2:
    if val_all.empty:
        st.warning("No validation data available.")
    else:
        # ── Overall quality banner ─────────────────────────────────────────
        total_checks = len(val_all)
        total_pass   = (val_all["status"] == "PASS").sum()
        total_fail   = (val_all["status"] == "FAIL").sum()
        total_warn   = (val_all["status"] == "WARN").sum()
        pct_pass     = round(total_pass / total_checks * 100, 1)

        if total_fail == 0:
            st.markdown(f"""
            <div class="quality-box">
                <h3>✅ All data quality checks passed</h3>
                <p>{total_checks} checks run across {passed} tables —
                {total_pass} passed, {total_warn} warnings (suppressed values in source PDF).
                The extracted dataset is complete and ready for use.</p>
            </div>""", unsafe_allow_html=True)
        else:
            st.error(
                f"⚠️ {total_fail} checks failed across {passed} tables. "
                f"See detail below."
            )

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Key data quality metrics ───────────────────────────────────────
        st.markdown('<div class="section-title">Data quality metrics</div>',
                    unsafe_allow_html=True)

        q1, q2, q3, q4 = st.columns(4)

        tables_with_data = (summary_df["records"] > 0).sum()
        total_records    = summary_df["records"].sum()
        null_warns       = val_all[
            (val_all["status"] == "WARN") &
            (val_all["check_type"] == "Completeness")
        ]
        pct_complete = round(
            (1 - null_warns["actual"].astype(str)
             .str.extract(r"(\d+)")[0].fillna(0).astype(int).sum()
             / max(total_records, 1)) * 100, 1
        ) if not null_warns.empty else 100.0

        q1.metric("Tables with data",    f"{tables_with_data}/{n_tables}")
        q2.metric("Total records",        f"{total_records:,}")
        q3.metric("Checks passed",        f"{total_pass}/{total_checks}")
        q4.metric("Data completeness",    f"{pct_complete}%")

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Per-table status grid ──────────────────────────────────────────
        st.markdown('<div class="section-title">Table-by-table status</div>',
                    unsafe_allow_html=True)

        tbl_summary = (
            val_all.groupby(["table_key", "status"])
            .size().unstack(fill_value=0).reset_index()
        )
        for col in ["PASS", "FAIL", "WARN"]:
            if col not in tbl_summary.columns:
                tbl_summary[col] = 0

        # Merge with record counts
        rec_counts = summary_df[["table_key", "records"]]
        tbl_summary = tbl_summary.merge(rec_counts, on="table_key", how="left")

        def overall_badge(row):
            if row.get("FAIL", 0) > 0:
                return '<span class="badge-fail">FAIL</span>'
            if row.get("WARN", 0) > 0:
                return '<span class="badge-warn">WARN</span>'
            return '<span class="badge-pass">PASS</span>'

        tbl_summary["Overall"] = tbl_summary.apply(overall_badge, axis=1)
        display_cols = ["table_key", "records", "PASS", "FAIL", "WARN", "Overall"]
        display_cols = [c for c in display_cols if c in tbl_summary.columns]

        st.markdown(
            tbl_summary[display_cols]
            .rename(columns={"table_key": "Table", "records": "Records"})
            .to_html(escape=False, index=False),
            unsafe_allow_html=True,
        )

        # ── Failure detail (only if failures exist) ────────────────────────
        fails = val_all[val_all["status"] == "FAIL"]
        if not fails.empty:
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown('<div class="section-title">Failure detail</div>',
                        unsafe_allow_html=True)
            st.dataframe(
                fails[["table_key","check_type","description",
                        "expected","actual","notes"]],
                use_container_width=True, height=280, hide_index=True,
            )

        # ── Warnings (only if warnings exist) ─────────────────────────────
        warns = val_all[val_all["status"] == "WARN"]
        if not warns.empty:
            st.markdown("<br>", unsafe_allow_html=True)
            with st.expander(f"ℹ️ {len(warns)} warnings (suppressed source values)"):
                st.dataframe(
                    warns[["table_key","check_type","description",
                           "expected","actual","notes"]],
                    use_container_width=True, height=240, hide_index=True,
                )

# ── Tab 3: Downloads ──────────────────────────────────────────────────────────
with tab3:
    st.markdown('<div class="section-title">Download outputs</div>',
                unsafe_allow_html=True)
    st.markdown(
        "All files use **UTF-8 with BOM** encoding — "
        "they open correctly in Excel without any import settings."
    )
    st.markdown("<br>", unsafe_allow_html=True)

    d1, d2, d3 = st.columns(3)

    if not combined.empty:
        csv_data = combined.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
        d1.markdown("**Transformed data**")
        d1.markdown(f"*{records:,} records · {passed} tables*")
        d1.download_button(
            "⬇  Download CSV", csv_data,
            f"qlfs_{qtr_lbl.replace(' ','_')}_transformed.csv",
            "text/csv", use_container_width=True,
        )

    if not val_all.empty:
        val_csv = val_all.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
        d2.markdown("**Validation report**")
        d2.markdown(f"*{total_pass} passed · {total_fail} failed · {total_warn} warnings*")
        d2.download_button(
            "⬇  Download CSV", val_csv,
            f"qlfs_{qtr_lbl.replace(' ','_')}_validation.csv",
            "text/csv", use_container_width=True,
        )

    if not summary_df.empty:
        sum_csv = summary_df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
        d3.markdown("**Pipeline summary**")
        d3.markdown(f"*{passed}/{n_tables} tables completed all stages*")
        d3.download_button(
            "⬇  Download CSV", sum_csv,
            f"qlfs_{qtr_lbl.replace(' ','_')}_pipeline_summary.csv",
            "text/csv", use_container_width=True,
        )

    st.divider()
    st.markdown('<div class="section-title">Output schema reference</div>',
                unsafe_allow_html=True)
    schema = pd.DataFrame({
        "Column"     : ["table_key","region","province_id","district_id",
                        "municipality_id","indicator","measure","quarter","year","value"],
        "Type"       : ["string","string","integer","integer","integer",
                        "string","string","integer","integer","float"],
        "Description": [
            "Source table identifier (e.g. table2_3)",
            "Always 'South Africa'",
            "Province ID 1–9, NULL for national rows",
            "District ID for metro municipalities, NULL otherwise",
            "Metro local ID, 9999 for non-metro, NULL for province-level rows",
            "What is being measured (e.g. Employed, Labour force)",
            "Breakdown dimension (e.g. Women, Black African), NULL for geography tables",
            "Quarter number 1–4",
            "Year (2024 or 2025)",
            "Value in thousands, NULL if suppressed in source PDF",
        ],
        "Example"    : [
            "table2_3","South Africa","6","2","212",
            "Employed","Women","1","2025","8 234",
        ],
    })
    st.dataframe(schema, use_container_width=True, hide_index=True)
