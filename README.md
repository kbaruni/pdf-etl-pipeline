# QLFS ETL Pipeline

An automated Extract, Transform, Load (ETL) pipeline for extracting structured data from PDF documents containing tables. Demonstrated using the South African **Quarterly Labour Force Survey (QLFS)** P0211 series as a use case.

> **Associated paper:** "An Automated ETL Pipeline for Extracting Structured Data from PDF Documents Containing Tables: A Use Case of the South African Quarterly Labour Force Survey" — submitted to SoftwareX (Elsevier).

---

## Repository Structure

```
pdf-etl-pipeline/
├── pipeline/               # PRIMARY — PDF ETL pipeline (4 stages)
│   ├── src/
│   │   ├── extractor.py    # Stage 1: PDF table extraction (Camelot)
│   │   ├── cleaner.py      # Stage 2: Cleaning (aggregate rows, label correction)
│   │   ├── transformer.py  # Stage 3: Schema transformation
│   │   └── validator.py    # Stage 4: Data quality validation
│   ├── configs.py          # Table configurations for all 23 QLFS tables
│   └── main.py             # Entry point (single and multi-edition modes)
├── app/
│   └── app.py              # Streamlit browser application
├── microdata/              # Microdata weighted estimates (validation tool)
│   ├── app.py              # Microdata Explorer Streamlit app
│   ├── engine.py           # Weighted calculation engine
│   ├── lookups.py          # Indicator and measure definitions
│   └── sample_output/      # Pre-generated output tables (Q1 2025)
├── validation/             # Validation scripts and reports
│   ├── validate_pdf_vs_pipeline.py   # Level 1: PDF vs pipeline
│   ├── validate_3source.py           # Level 2: 3-source validation
│   └── reports/            # Pre-generated validation reports
├── data/
│   └── lookups/            # Dimension/lookup tables (Stats SA metadata)
└── docs/                   # Additional documentation
```

---

## Requirements

- Python 3.9 or higher
- See `requirements.txt` for all dependencies

---

## Installation

```bash
# 1. Clone the repository
git clone https://github.com/kbaruni/pdf-etl-pipeline.git
cd pdf-etl-pipeline

# 2. Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate       # Linux/Mac
venv\Scripts\activate          # Windows

# 3. Install dependencies
pip install -r requirements.txt
```

---

## Usage

### Option A — Browser Application (recommended for non-technical users)

```bash
cd app
streamlit run app.py
```

Then open your browser at `http://localhost:8501`, upload a QLFS PDF, and download the extracted CSV.

### Option B — Command Line (single edition)

```bash
cd pipeline
python main.py --pdf path/to/QLFS_Q1_2025.pdf --output output/
```

### Option C — Command Line (batch, multiple editions)

```bash
cd pipeline
python main.py --dir path/to/pdf_folder/ --output output/
```

---

## Microdata Explorer

The microdata component calculates weighted population estimates from QLFS unit record CSV files downloaded from the [Stats SA ISIbalo Data Portal](https://isibaloweb.statssa.gov.za).

> **Note:** The raw microdata CSV (`QLFS202501.csv`, ~167MB) is not included in this repository due to file size and licensing. Download it directly from ISIbalo and place it in `microdata/data/`.

```bash
cd microdata
streamlit run app.py
```

---

## Validation

Pre-generated validation reports are in `validation/reports/`. To regenerate:

```bash
# Level 1: PDF pipeline vs published figures
python validation/validate_pdf_vs_pipeline.py

# Level 2: 3-source validation (PDF + pipeline + microdata)
python validation/validate_3source.py
```

---

## Data Sources

| Source | Description | Access |
|--------|-------------|--------|
| QLFS PDF reports | Stats SA P0211 series | [statssa.gov.za](https://www.statssa.gov.za) |
| QLFS microdata | Unit record CSV | [ISIbalo Portal](https://isibaloweb.statssa.gov.za) |
| Municipality register | Local municipality IDs | Included in `data/lookups/` |

---

## Output Schema

Each extracted table row follows this schema:

```
table_key | province_id | district_id | municipality_id | indicator | measure | quarter | year | value
```

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

## Authors

Kedimotse Baruni — National Data Policy Observatory
