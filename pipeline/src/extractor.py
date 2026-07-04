# =========================================================
# src/extractor.py  —  Stage 1: PDF extraction
# =========================================================
import logging
import pandas as pd
import camelot

logger = logging.getLogger(__name__)


def _parse_pages(pages_str: str) -> list[int]:
    result = []
    for part in pages_str.split(","):
        part = part.strip()
        if "-" in part:
            s, e = part.split("-")
            result.extend(range(int(s), int(e) + 1))
        else:
            result.append(int(part))
    return result


def extract_table(pdf_path: str, table_key: str, config: dict) -> pd.DataFrame:
    pages     = _parse_pages(config["pages"])
    all_frames = []

    for page in pages:
        try:
            tables = camelot.read_pdf(str(pdf_path), pages=str(page), flavor="lattice")
            if tables.n == 0:
                tables = camelot.read_pdf(
                    str(pdf_path), pages=str(page), flavor="stream",
                    edge_tol=50, row_tol=10
                )
            for t in tables:
                if not t.df.empty:
                    all_frames.append(t.df)
        except Exception as exc:
            logger.error("  Camelot error p%s %s: %s", page, table_key, exc)

    if not all_frames:
        return pd.DataFrame()

    raw = pd.concat(all_frames, ignore_index=True)
    logger.info("  [EXTRACT] %d raw rows — %s", len(raw), table_key)
    return raw
