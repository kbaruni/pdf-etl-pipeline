# Data Folder

## lookups/
Dimension and lookup tables derived from the Stats SA QLFS metadata PDF.
These are included in the repository and do not need to be downloaded.

- `QLFS_Lookup_Tables.xlsx` — All dimension tables (gender, age band,
  province, industry, occupation, etc.) with numeric codes and labels.

## Microdata (not included)
The raw QLFS unit record microdata CSV files are not included in this
repository due to file size (~167MB per quarter) and Stats SA licensing terms.

To download the microdata:
1. Go to https://isibaloweb.statssa.gov.za
2. Register for a free account
3. Navigate to QLFS > the relevant quarter
4. Download the CSV format file
5. Place it in microdata/data/ before running the microdata app
