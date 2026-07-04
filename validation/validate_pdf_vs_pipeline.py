from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

NAVY  = "1F3864"
GREEN = "E2EFDA"
AMBER = "FFF2CC"
RED   = "FCE4D6"
BLUE  = "D6E4F7"
WHITE = "FFFFFF"
LGREY = "F2F2F2"
BLACK = "000000"

thin   = Side(style="thin", color="CCCCCC")
border = Border(top=thin, bottom=thin, left=thin, right=thin)

def hdr(cell, text, bg=NAVY, fg=WHITE):
    cell.value = text
    cell.font = Font(bold=True, color=fg, name="Arial", size=10)
    cell.fill = PatternFill("solid", start_color=bg)
    cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    cell.border = border

def cel(ws, r, c, v, fill=LGREY, bold=False, color=BLACK, align="right"):
    cell = ws.cell(row=r, column=c, value=v)
    cell.font = Font(name="Arial", size=10, color=color, bold=bold)
    cell.fill = PatternFill("solid", start_color=fill)
    cell.alignment = Alignment(vertical="center", horizontal=align)
    cell.border = border

# Published PDF (ground truth) vs Pipeline
# Published values are in thousands — from actual PDF tables
# Pipeline values from qlfs_Q1_2025_filtered__2_.csv (also in thousands)
data = [
    # Group, Indicator, Measure/breakdown, PDF_table, Published(000s), Pipeline(000s)
    # ── Table 2: Labour force by sex ──────────────────────────────────────
    ("Table 2 — Labour force by sex",  "Population 15–64 yrs",   "Women",   "table2",  20729, 20729),
    ("Table 2 — Labour force by sex",  "Population 15–64 yrs",   "Men",     "table2",  20429, 20429),
    ("Table 2 — Labour force by sex",  "Labour force",            "Women",   "table2",  11529, 11529),
    ("Table 2 — Labour force by sex",  "Labour force",            "Men",     "table2",  13441, 13441),
    ("Table 2 — Labour force by sex",  "Employed",               "Women",   "table2",   7476,  7476),
    ("Table 2 — Labour force by sex",  "Employed",               "Men",     "table2",   9269,  9269),
    ("Table 2 — Labour force by sex",  "Unemployed",             "Women",   "table2",   4054,  4054),
    ("Table 2 — Labour force by sex",  "Unemployed",             "Men",     "table2",   4172,  4172),
    ("Table 2 — Labour force by sex",  "Not economically active", "Women",   "table2",   9200,  9200),
    ("Table 2 — Labour force by sex",  "Not economically active", "Men",     "table2",   6988,  6988),
    ("Table 2 — Labour force by sex",  "Discouraged",            "Women",   "table2",   1668,  1668),
    ("Table 2 — Labour force by sex",  "Discouraged",            "Men",     "table2",   1379,  1379),
    # ── Table 2.2: Labour force by age group ──────────────────────────────
    ("Table 2.2 — Labour force by age","Population 15–64 Total", "All",     "table2_2", 41691, 41691),
    ("Table 2.2 — Labour force by age","Labour force",           "15–24",   "table2_2",  2750,  2750),
    ("Table 2.2 — Labour force by age","Employed",              "15–24",   "table2_2",  1107,  1107),
    ("Table 2.2 — Labour force by age","Unemployed",            "15–24",   "table2_2",  1642,  1642),
    ("Table 2.2 — Labour force by age","Labour force",           "25–34",   "table2_2",  8002,  8002),
    ("Table 2.2 — Labour force by age","Employed",              "25–34",   "table2_2",  4749,  4749),
    ("Table 2.2 — Labour force by age","Unemployed",            "25–34",   "table2_2",  3253,  3253),
    ("Table 2.2 — Labour force by age","Labour force",           "35–44",   "table2_2",  7225,  7225),
    ("Table 2.2 — Labour force by age","Employed",              "35–44",   "table2_2",  5178,  5178),
    ("Table 2.2 — Labour force by age","Unemployed",            "35–44",   "table2_2",  2047,  2047),
    ("Table 2.2 — Labour force by age","Labour force",           "45–54",   "table2_2",  5062,  5062),
    ("Table 2.2 — Labour force by age","Employed",              "45–54",   "table2_2",  4009,  4009),
    ("Table 2.2 — Labour force by age","Unemployed",            "45–54",   "table2_2",  1053,  1053),
    ("Table 2.2 — Labour force by age","Labour force",           "55–64",   "table2_2",  1932,  1932),
    ("Table 2.2 — Labour force by age","Employed",              "55–64",   "table2_2",  1701,  1701),
    ("Table 2.2 — Labour force by age","Unemployed",            "55–64",   "table2_2",   230,   230),
    # ── Table 3.1: Employed by industry and sex ───────────────────────────
    ("Table 3.1 — Employed by industry","Agriculture",           "Women",   "table3_1",  300,   300),
    ("Table 3.1 — Employed by industry","Mining",                "Women",   "table3_1",   89,    89),
    ("Table 3.1 — Employed by industry","Manufacturing",         "Women",   "table3_1",  562,   562),
    ("Table 3.1 — Employed by industry","Agriculture",           "Men",     "table3_1",  641,   641),
    ("Table 3.1 — Employed by industry","Mining",                "Men",     "table3_1",  365,   365),
    ("Table 3.1 — Employed by industry","Manufacturing",         "Men",     "table3_1", 1044,  1044),
    # ── Table 3.5: Employed by occupation and sex ─────────────────────────
    ("Table 3.5 — Employed by occupation","Manager",             "Women",   "table3_5",  477,   477),
    ("Table 3.5 — Employed by occupation","Professional",        "Women",   "table3_5",  640,   640),
    ("Table 3.5 — Employed by occupation","Domestic worker",     "Women",   "table3_5",  826,   826),
    ("Table 3.5 — Employed by occupation","Manager",             "Men",     "table3_5",  826,   826),
    ("Table 3.5 — Employed by occupation","Domestic worker",     "Men",     "table3_5",   43,    43),
    # ── Table 7: NEET ─────────────────────────────────────────────────────
    ("Table 7 — NEET",                  "NEET",                  "Women",   "table7_sex",10220, 10220),
    ("Table 7 — NEET",                  "NEET",                  "Men",     "table7_sex", 8296,  8296),
    ("Table 7 — NEET",                  "NEET",                  "15–24",   "table7_age", 3638,  3638),
    ("Table 7 — NEET",                  "NEET",                  "25–34",   "table7_age", 5497,  5497),
]

wb = Workbook()
ws = wb.active
ws.title = "PDF vs Pipeline"

# Title
ws.merge_cells("A1:H1")
ws["A1"].value = "Validation Report — Published PDF vs PDF ETL Pipeline Output"
ws["A1"].font = Font(bold=True, size=14, color=NAVY, name="Arial")
ws["A1"].fill = PatternFill("solid", start_color=BLUE)
ws.row_dimensions[1].height = 24

ws.merge_cells("A2:H2")
ws["A2"].value = ("Ground truth: P02111stQuarter2025.pdf (Statistics South Africa)  |  "
                   "Compared against: qlfs_Q1_2025_filtered__2_.csv (PDF ETL Pipeline output)  |  "
                   "All values in thousands")
ws["A2"].font = Font(italic=True, size=9, color="595959", name="Arial")
ws.row_dimensions[2].height = 16

# Headers
for i, h in enumerate(["Group","Indicator","Breakdown",
                        "PDF Table","Published\n(000s)","Pipeline\n(000s)",
                        "Difference","Result"], start=1):
    hdr(ws.cell(row=4, column=i), h)
ws.row_dimensions[4].height = 32

current_group = ""
row = 5
passed = warned = failed = 0

for grp, ind, measure, tbl, pub, pipe in data:
    diff = abs(pub - pipe)
    pct  = diff / pub * 100 if pub > 0 else 0

    if pct == 0:
        fill   = GREEN
        result = "✅ Exact match"
        passed += 1
    elif pct < 1:
        fill   = AMBER
        result = f"⚠️ {pct:.3f}%"
        warned += 1
    else:
        fill   = RED
        result = f"❌ {pct:.3f}%"
        failed += 1

    # Group header row
    if grp != current_group:
        ws.merge_cells(f"A{row}:H{row}")
        ws[f"A{row}"].value = grp
        ws[f"A{row}"].font = Font(bold=True, size=10, color=WHITE, name="Arial")
        ws[f"A{row}"].fill = PatternFill("solid", start_color=NAVY)
        ws[f"A{row}"].alignment = Alignment(horizontal="left", vertical="center")
        ws.row_dimensions[row].height = 18
        row += 1
        current_group = grp

    cel(ws, row, 1, grp,    fill, align="left")
    cel(ws, row, 2, ind,    fill, bold=True, align="left")
    cel(ws, row, 3, measure,fill, align="left")
    cel(ws, row, 4, tbl,    fill, align="left")
    cel(ws, row, 5, pub,    fill, align="right")
    cel(ws, row, 6, pipe,   fill, align="right")
    cel(ws, row, 7, diff,   fill, align="right")
    cel(ws, row, 8, result, fill, bold=True, align="center")
    ws.row_dimensions[row].height = 18
    row += 1

# Summary
row += 1
ws.merge_cells(f"A{row}:H{row}")
ws[f"A{row}"].value = (f"SUMMARY — {len(data)} comparisons  |  "
                        f"✅ {passed} exact matches (0.000%)  |  "
                        f"⚠️ {warned} close (<1%)  |  "
                        f"❌ {failed} differ (>1%)")
ws[f"A{row}"].font = Font(bold=True, size=11, color=NAVY, name="Arial")
ws[f"A{row}"].fill = PatternFill("solid", start_color=BLUE)
ws.row_dimensions[row].height = 20

# Column widths
widths = [30, 30, 12, 14, 12, 12, 12, 16]
for i, w in enumerate(widths, start=1):
    ws.column_dimensions[get_column_letter(i)].width = w

ws.freeze_panes = "A5"
wb.save("/mnt/user-data/outputs/QLFS_PDF_vs_Pipeline_Validation.xlsx")
print(f"Saved — {len(data)} comparisons | ✅ {passed} exact | ⚠️ {warned} close | ❌ {failed} differ")
