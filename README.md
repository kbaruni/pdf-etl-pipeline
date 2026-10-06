# QLFS ETL Pipeline

An automated Extract–Transform–Load (ETL) pipeline that extracts structured data from ruled, machine-generated PDF tables and produces clean, analysis-ready CSV datasets. Demonstrated using the South African **Quarterly Labour Force Survey (QLFS) P0211** series published by Statistics South Africa.

> **Associated paper:** "Beyond the Spreadsheet: An Automated ETL Pipeline for Ruled PDF Tables — A QLFS Use Case" — submitted to SoftwareX (Elsevier).

---

## Repository Structure

```
pdf-etl-pipeline/
├── pipeline/               # Core ETL pipeline
│   ├── src/
│   │   ├── extractor.py    # Stage 1: PDF table extraction (Camelot lattice mode)
│   │   ├── cleaner.py      # Stage 2: Label correction and aggregate-row removal
│   │   ├── transformer.py  # Stage 3: Schema transformation and geo-ID mapping
│   │   └── validator.py    # Stage 4: Three-level data quality validation
│   ├── configs.py          # Per-edition page mappings and table configurations
│   └── main.py             # Entry point — single PDF or batch mode
├── validation/
│   ├── validate_pdf_vs_pipeline.py   # Level 1: pipeline output vs PDF figures
│   ├── validate_3source.py           # Level 2: PDF + pipeline + microdata
│   ├── compare_pdf_vs_isibalo.py     # Level 3: PDF values vs ISIbalo aggregates
│   └── reports/
│       ├── QLFS_PDF_vs_Pipeline_Validation.xlsx   # Pre-generated Level 1 report
│       └── QLFS_3Source_Validation_Report.xlsx    # Pre-generated Level 2/3 report
├── microdata/              # Weighted-estimate engine (ISIbalo microdata)
│   ├── engine.py
│   ├── lookups.py
│   └── sample_output/      # Pre-generated microdata estimates (Q1 2025)
├── data/
│   └── lookups/            # Municipality and district dimension tables
└── docs/                   # Additional documentation
```

---

## Requirements

- Python 3.9 or higher
- Ghostscript (required by Camelot for PDF rendering)
  - **Ubuntu/Debian:** `sudo apt-get install ghostscript`
  - **macOS:** `brew install ghostscript`
  - **Windows:** download from [ghostscript.com](https://www.ghostscript.com)
- All Python dependencies: see `requirements.txt`

---

## Installation

```bash
# 1. Clone the repository
git clone https://github.com/kbaruni/pdf-etl-pipeline.git
cd pdf-etl-pipeline

# 2. Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate        # Linux/macOS
venv\Scripts\activate           # Windows

# 3. Install Python dependencies
pip install -r requirements.txt
```

---

## Quick Start — Run the Pipeline

### Step 1: Get a sample PDF

Download the Q1 2025 QLFS report directly from Statistics South Africa:

```
https://www.statssa.gov.za/publications/P0211/P02111stQuarter2025.pdf
```

Place the downloaded file in:

```
pipeline/data/input/P02111stQuarter2025.pdf
```

### Step 2: Run the pipeline (single PDF)

```bash
cd pipeline
python main.py --pdf P02111stQuarter2025.pdf
```

### Step 3: Run the pipeline (all registered editions)

```bash
cd pipeline
python main.py
```

Place all PDFs in `pipeline/data/input/` first. Registered editions are listed in `configs.py`.

---

## Output

All outputs are written to `pipeline/outputs/`:

```
outputs/
├── per_quarter/
│   ├── all_tables_Q1_2025.csv       # Combined output for one edition
│   └── all_validation_Q1_2025.csv   # Validation results for one edition
├── all_tables_all_quarters.csv      # Combined output across all editions
├── pipeline_summary_all.csv         # Pass/fail summary per table per edition
└── logs/                            # Timestamped run logs
```

Each row in the output CSV follows this schema:

```
table_key | region | province_id | district_id | municipality_id | indicator | measure | quarter | year | value
```

---

## Validation

Pre-generated validation reports for Q1 2025 are in `validation/reports/` and can be opened directly in Excel or any spreadsheet application without running any code.

To regenerate the reports:

```bash
# Level 1: pipeline output vs published PDF figures
python validation/validate_pdf_vs_pipeline.py

# Level 2/3: three-source validation (PDF + pipeline + ISIbalo microdata)
python validation/validate_3source.py
```

> **Note:** The three-source validation requires the QLFS Q1 2025 unit-record microdata CSV (~167 MB) downloaded from the [ISIbalo Data Portal](https://isibaloweb.statssa.gov.za) (free registration required). Place the file at `microdata/data/QLFS202501.csv`. The pre-generated report in `validation/reports/` covers this comparison and can be reviewed without downloading the microdata.

---

## Supported Editions

The pipeline is configured for the following QLFS editions:

| Edition | Filename |
|---------|----------|
| Q4 2023 | P02114thQuarter2023.pdf |
| Q1 2024 | P02111stQuarter2024.pdf |
| Q2 2024 | P02112ndQuarter2024.pdf |
| Q3 2024 | P02113rdQuarter2024.pdf |
| Q4 2024 | P02114thQuarter2024.pdf |
| Q1 2025 | P02111stQuarter2025.pdf |
| Q2 2025 | P02112ndQuarter2025.pdf |
| Q3 2025 | P02113rdQuarter2025.pdf |
| Q4 2025 | P02114thQuarter2025.pdf |

> Q3 and Q4 2025 use the ICSE-18 employment classification and include additional tables not present in earlier editions. These are extracted by the pipeline but require separate transformation logic for cross-edition comparison.

All PDFs are freely available from [Statistics South Africa](https://www.statssa.gov.za).

---

## Data Sources

| Source | Description | Access |
|--------|-------------|--------|
| QLFS PDF reports | Stats SA P0211 series | [statssa.gov.za](https://www.statssa.gov.za) |
| QLFS microdata | Unit-record CSV files | [ISIbalo Portal](https://isibaloweb.statssa.gov.za) |
| Municipality register | Local municipality and district IDs | Included in `data/lookups/` |

*Source: Statistics South Africa, Quarterly Labour Force Survey P0211 series.*

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

## Citation

If you use this software in your research, please cite:

```
[Citation details will be added upon publication]
```

---

## Author

Kedimotse Baruni — National Data Policy Observatory
