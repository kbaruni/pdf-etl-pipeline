#!/usr/bin/env python3
# =========================================================
# main.py  —  QLFS Multi-PDF Pipeline
# =========================================================
# Processes all QLFS PDF files in data/input/ automatically.
#
# Run:
#   python main.py                    # process all PDFs
#   python main.py --pdf filename.pdf # process one specific PDF
# =========================================================

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

from configs import (
    DATA_DIR, LOOKUP_PATH, LABEL_CORRECTIONS, DROP_LABELS,
    METRO_LOOKUP, PROVINCE_LOOKUP, GEO_SUM_ROWS, PROVINCES_NO_METROS,
    get_configs_for_pdf, detect_quarter_from_filename, PDF_REGISTRY,
)
from src.extractor   import extract_table
from src.cleaner     import clean_table
from src.validator   import validate_table
from src.transformer import transform_table

# ── Output directories ─────────────────────────────────────────────────────
OUT_BASE   = Path("outputs")
OUT_PQ     = OUT_BASE / "per_quarter"
OUT_LOGS   = OUT_BASE / "logs"

for d in [OUT_PQ, OUT_LOGS]:
    d.mkdir(parents=True, exist_ok=True)

# ── Logging ────────────────────────────────────────────────────────────────
RUN_TS   = datetime.now().strftime("%Y%m%d_%H%M%S")
LOG_FILE = OUT_LOGS / f"pipeline_{RUN_TS}.log"

logging.basicConfig(
    level    = logging.INFO,
    format   = "%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt  = "%H:%M:%S",
    handlers = [
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_FILE, mode="w", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


# ── Process a single PDF ───────────────────────────────────────────────────

def process_pdf(pdf_path: Path) -> tuple[pd.DataFrame, pd.DataFrame, list]:
    """
    Run all 4 stages for every table in one PDF.
    Returns (combined_transformed, combined_validation, summary_rows).
    """
    filename = pdf_path.name
    configs  = get_configs_for_pdf(filename)
    fallback_q, fallback_y = detect_quarter_from_filename(filename)

    logger.info("=" * 65)
    logger.info("PDF      : %s", filename)
    logger.info("Tables   : %d", len(configs))
    logger.info("Fallback : Q%s %s", fallback_q, fallback_y)
    logger.info("=" * 65)

    # Per-PDF sub-directories
    stem    = pdf_path.stem
    out_raw = OUT_BASE / stem / "raw"
    out_cln = OUT_BASE / stem / "clean"
    out_val = OUT_BASE / stem / "validation"
    out_trn = OUT_BASE / stem / "transformed"
    for d in [out_raw, out_cln, out_val, out_trn]:
        d.mkdir(parents=True, exist_ok=True)

    all_trans = []
    all_val   = []
    summary   = []

    # Detected quarter cached from first successful table
    detected_q, detected_y = 0, 0

    for table_key, config in configs.items():
        logger.info("-" * 65)
        logger.info("  %s  pages=%s", table_key, config["pages"])

        stage_ok   = {s: False for s in ["extract", "clean", "validate", "transform"]}
        final_rows = 0

        # Stage 1: Extract
        try:
            raw_df = extract_table(str(pdf_path), table_key, config)
            raw_df.to_csv(out_raw / f"{table_key}_raw.csv",
                          index=False, encoding="utf-8-sig")
            stage_ok["extract"] = not raw_df.empty
        except Exception as e:
            logger.error("  [EXTRACT] FAILED: %s", e)
            raw_df = pd.DataFrame()

        # Stage 2: Clean + detect quarter
        try:
            clean_df, q_col, q, y = clean_table(
                raw_df, LABEL_CORRECTIONS, DROP_LABELS
            )
            # Cache first successful detection
            if q and y and not detected_q:
                detected_q, detected_y = q, y
                logger.info("  Quarter detected: Q%d %d", q, y)
            # Fall back to cached or filename-based detection
            if not q:
                q, y     = detected_q or fallback_q, detected_y or fallback_y
                q_col    = f"Q{q}_{y}" if q else "Q_current"

            clean_df.to_csv(out_cln / f"{table_key}_clean.csv",
                            index=False, encoding="utf-8-sig")
            stage_ok["clean"] = not clean_df.empty
        except Exception as e:
            logger.error("  [CLEAN] FAILED: %s", e)
            clean_df, q_col, q, y = pd.DataFrame(), "", fallback_q, fallback_y

        # Stage 3: Transform
        trans_df = pd.DataFrame()
        try:
            trans_df = transform_table(
                clean_df, table_key, config, q_col, q, y,
                METRO_LOOKUP, PROVINCE_LOOKUP, GEO_SUM_ROWS,
            )
            trans_df.to_csv(out_trn / f"{table_key}_transformed.csv",
                            index=False, encoding="utf-8-sig")
            final_rows = len(trans_df)
            stage_ok["transform"] = not trans_df.empty
            if not trans_df.empty:
                all_trans.append(trans_df)
        except Exception as e:
            logger.error("  [TRANSFORM] FAILED: %s", e)

        # Stage 4: Validate (runs after transform so it can inspect the output)
        try:
            val_df = validate_table(
                clean_df, table_key, config, q_col, q, y,
                trans_df if not trans_df.empty else None, RUN_TS
            )
            val_df.to_csv(out_val / f"{table_key}_validation.csv",
                          index=False, encoding="utf-8-sig")
            all_val.append(val_df)
            stage_ok["validate"] = True
            fails = (val_df["status"] == "FAIL").sum()
            if fails:
                logger.warning("  [VALIDATE] %d FAIL(s)", fails)
        except Exception as e:
            logger.error("  [VALIDATE] FAILED: %s", e)

        summary.append({
            "pdf"          : filename,
            "quarter"      : q,
            "year"         : y,
            "table_key"    : table_key,
            "pages"        : config["pages"],
            "type"         : config["type"],
            "extract_ok"   : stage_ok["extract"],
            "clean_ok"     : stage_ok["clean"],
            "validate_ok"  : stage_ok["validate"],
            "transform_ok" : stage_ok["transform"],
            "records"      : final_rows,
        })

    combined_trans = pd.concat(all_trans, ignore_index=True) if all_trans else pd.DataFrame()
    combined_val   = pd.concat(all_val,   ignore_index=True) if all_val   else pd.DataFrame()
    return combined_trans, combined_val, summary


# ── Main entry point ───────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="QLFS Multi-PDF Pipeline")
    parser.add_argument("--pdf", help="Process a single PDF filename from data/input/")
    args = parser.parse_args()

    # Resolve which PDFs to process
    if args.pdf:
        pdfs = [DATA_DIR / args.pdf]
        if not pdfs[0].exists():
            logger.error("PDF not found: %s", pdfs[0])
            sys.exit(1)
    else:
        # All registered PDFs in order
        pdfs = sorted(
            [DATA_DIR / f for f in PDF_REGISTRY if (DATA_DIR / f).exists()]
        )
        if not pdfs:
            logger.error("No PDFs found in %s", DATA_DIR)
            sys.exit(1)

    logger.info("PDFs to process: %d", len(pdfs))
    for p in pdfs:
        logger.info("  %s", p.name)

    all_trans_global  = []
    all_val_global    = []
    all_summary_global = []

    for pdf_path in pdfs:
        trans, val, summary = process_pdf(pdf_path)

        q = summary[0]["quarter"] if summary else 0
        y = summary[0]["year"]    if summary else 0
        label = f"Q{q}_{y}" if q else pdf_path.stem

        # Per-quarter combined output
        if not trans.empty:
            pq_path = OUT_PQ / f"all_tables_{label}.csv"
            trans.to_csv(pq_path, index=False, encoding="utf-8-sig")
            logger.info("  Per-quarter output: %d records → %s", len(trans), pq_path)
            all_trans_global.append(trans)

        if not val.empty:
            pq_val = OUT_PQ / f"all_validation_{label}.csv"
            val.to_csv(pq_val, index=False, encoding="utf-8-sig")

        all_summary_global.extend(summary)

    # Combined output across all quarters
    if all_trans_global:
        combined = pd.concat(all_trans_global, ignore_index=True)
        combined_path = OUT_BASE / "all_tables_all_quarters.csv"
        combined.to_csv(combined_path, index=False, encoding="utf-8-sig")
        logger.info("Combined output: %d records → %s", len(combined), combined_path)

    # Pipeline summary
    summary_df = pd.DataFrame(all_summary_global)
    summary_df.to_csv(OUT_BASE / "pipeline_summary_all.csv",
                      index=False, encoding="utf-8-sig")

    passed = summary_df["transform_ok"].sum() if not summary_df.empty else 0
    total  = len(summary_df)
    logger.info("=" * 65)
    logger.info("DONE — %d / %d tables succeeded across %d PDFs",
                passed, total, len(pdfs))
    logger.info("Log → %s", LOG_FILE)
    logger.info("=" * 65)


if __name__ == "__main__":
    main()
