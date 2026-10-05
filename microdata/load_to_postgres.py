# =========================================================
# load_to_postgres.py
# Loads the combined QLFS estimates into PostgreSQL
# =========================================================
# Run: py load_to_postgres.py
# =========================================================

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

conn = psycopg2.connect(
    host     = "localhost",
    dbname   = "dataObservatory",
    user     = "postgres",
    password = "your_password_here",
    port     = 5432
)
cur = conn.cursor()

# Path to your combined Excel file
EXCEL_FILE = r"C:\path\to\your\qlfs_all_indicators_combined.xlsx"

TABLE   = "npdo.stats_sa_qlfs_estimates"
COLUMNS = ["province","district","municipality","year","quarter",
           "indicator_type","indicator_code","measure_type_id","measure_code","value"]

print("Loading Excel file...")
xl = pd.read_excel(EXCEL_FILE, sheet_name=None)

all_frames = []
for sheet_name, df in xl.items():
    # Add indicator_type from sheet name
    df["indicator_type"] = sheet_name.replace("stats_sa_qlfs_","").replace("_estimates","")
    all_frames.append(df)

combined = pd.concat(all_frames, ignore_index=True)
combined = combined[COLUMNS].copy()
combined["value"] = combined["value"].round(0).astype(int)

rows = [tuple(row) for row in combined.itertuples(index=False)]
col_str = ", ".join(COLUMNS)
sql = f"INSERT INTO {TABLE} ({col_str}) VALUES %s"

execute_values(cur, sql, rows)
conn.commit()

print(f"✅ {TABLE} — {len(rows):,} rows inserted")
cur.close()
conn.close()
print("Done!")
