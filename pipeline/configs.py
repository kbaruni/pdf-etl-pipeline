# =========================================================
# configs.py  —  Multi-PDF QLFS Pipeline
# =========================================================

import re
from pathlib import Path

# ── Input paths ────────────────────────────────────────────────────────────
DATA_DIR    = Path("data/input")
LOOKUP_PATH = DATA_DIR / "local_municipalities_district_ids.xlsx"

# ── PDF registry — filename → (quarter, year) ──────────────────────────────
# Used as fallback if auto-detection from column headers fails
PDF_REGISTRY = {
    "P02111stQuarter2024.pdf" : (1, 2024),
    "P02112ndQuarter2024.pdf" : (2, 2024),
    "P02113rdQuarter2024.pdf" : (3, 2024),
    "P02114thQuarter2024.pdf" : (4, 2024),
    "P02111stQuarter2025.pdf" : (1, 2025),
    "P02112ndQuarter2025.pdf" : (2, 2025),
    "P02113rdQuarter2025.pdf" : (3, 2025),
    "P02114thQuarter2025.pdf" : (4, 2025),
}

# ── Per-edition page overrides ─────────────────────────────────────────────
# Standard editions (Q1 2024 – Q2 2025): base_pages in STANDARD_CONFIGS apply unchanged.
# Q3 and Q4 2025 have ICSE-18 tables inserted mid-document which shifts page numbers
# differently for each table — a single offset cannot work. Exact pages listed here.

Q3_2025_PAGES = {
    # Tables before the ICSE-18 insertion (same as standard)
    "table1_sex":               "25", "table1_population_group": "25",
    "table1_province":          "25",
    "table2":                   "26,27,28",
    "table2_1":                 "29,30,31",
    "table2_2":                 "32,33,34",
    "table2_3":                 "35-46",
    "table2_4":                 "47,48",
    "table2_5":                 "49,50",
    "table2_6":                 "51,52",
    "table2_7":                 "53-60",
    "table3_1":                 "47",   # Q3 2025 actual
    "table3_2":                 "49-53",
    "table3_3":                 "54,55",
    "table3_4":                 "56-60",
    # Tables after ICSE-18 insertion
    "table3_5":                 "61,62",
    "table3_6":                 "63",
    "table3_6b":                "64",
    "table3_6c":                "65,66",
    "table3_7":                 "67",
    "table3_8a":                "68",   "table3_8b":              "68",
    "table3_8c":                "69",   "table3_8d":              "69",
    "table3_8e":                "70",   "table3_8f":              "70",
    "table3_8g":                "71",   "table3_8h":              "71",
    "table3_8i":                "72",   "table3_8j":              "72",
    "table3_8k":                "73",
    "table3_9_sex":             "75",
    "table3_9_industry":        "75",
    "table3_9_occupation":      "75",
    "table3_10":                "77,78",
    "table3_10b":               "79,80",
    "table4_reason":            "81",   "table4_duration":        "81",
    "table4_prev_occupation":   "81",   "table4_prev_industry":   "82",
    "table5":                   "83",
    "table6_age":               "84",
    "table6_education":         "84,85",
    "table6_attendance":        "85",
    "table6_marital":           "86",
    "table7_sex":               "87",   "table7_age":             "87",
    "table7_population_group":  "87",   "table7_province":        "87",
    "table8":                   "89-92",
}

Q4_2025_PAGES = {
    "table1_sex":               "24",   "table1_population_group": "24",
    "table1_province":          "24",
    "table2":                   "25,26,27",
    "table2_1":                 "28,29,30",
    "table2_2":                 "31,32,33",
    "table2_3":                 "34-45",
    "table2_4":                 "46,47",
    "table2_5":                 "48,49",
    "table2_6":                 "50,51",
    "table2_7":                 "52-59",
    "table3_1":                 "46",
    "table3_2":                 "48-52",
    "table3_3":                 "53,54",
    "table3_4":                 "55-59",
    "table3_5":                 "60,61",
    "table3_6":                 "62",
    "table3_6b":                "63",
    "table3_6c":                "64,65",
    "table3_7":                 "66",
    "table3_8a":                "67",   "table3_8b":              "67",
    "table3_8c":                "68",   "table3_8d":              "68",
    "table3_8e":                "69",   "table3_8f":              "69",
    "table3_8g":                "70",   "table3_8h":              "70",
    "table3_8i":                "71",   "table3_8j":              "71",
    "table3_8k":                "72",
    "table3_9_sex":             "74",
    "table3_9_industry":        "74",
    "table3_9_occupation":      "74",
    "table3_10":                "76,77",
    "table3_10b":               "78,79",
    "table4_reason":            "80",   "table4_duration":        "80",
    "table4_prev_occupation":   "80",   "table4_prev_industry":   "81",
    "table5":                   "82",
    "table6_age":               "83",
    "table6_education":         "83,84",
    "table6_attendance":        "84",
    "table6_marital":           "85",
    "table7_sex":               "86",   "table7_age":             "86",
    "table7_population_group":  "86",   "table7_province":        "86",
    "table8":                   "88-91",
}

# ── Quarter month tokens → (quarter, offset_from_current) ──────────────────
QUARTER_TOKENS = {
    "jan-mar": 1,
    "apr-jun": 2,
    "jul-sep": 3,
    "oct-dec": 4,
}

# ── Non-metro placeholder ID ───────────────────────────────────────────────
NON_METRO_ID = 9999

# ── Metro name → IDs ──────────────────────────────────────────────────────
METRO_LOOKUP = {
    "City of Cape Town"    : {"province_id": 1, "district_id": 47, "local_id": 189},
    "Buffalo City"         : {"province_id": 2, "district_id":  3, "local_id": 180},
    "Nelson Mandela Bay"   : {"province_id": 2, "district_id": 10, "local_id": 179},
    "Mangaung"             : {"province_id": 3, "district_id": 15, "local_id": 202},
    "eThekwini"            : {"province_id": 4, "district_id": 29, "local_id": 168},
    "Ekurhuleni"           : {"province_id": 6, "district_id":  1, "local_id": 213},
    "City of Johannesburg" : {"province_id": 6, "district_id":  2, "local_id": 212},
    "City of Tshwane"      : {"province_id": 6, "district_id": 18, "local_id":  37},
}

# ── Province name → province_id ───────────────────────────────────────────
PROVINCE_LOOKUP = {
    "Western Cape"   : 1,
    "Eastern Cape"   : 2,
    "Free State"     : 3,
    "KwaZulu-Natal"  : 4,
    "North West"     : 5,
    "Gauteng"        : 6,
    "Mpumalanga"     : 7,
    "Limpopo"        : 8,
    "Northern Cape"  : 9,
}

PROVINCES_NO_METROS = ["Northern Cape", "North West", "Mpumalanga", "Limpopo"]

GEO_SUM_ROWS = {
    "South Africa", "Western Cape", "Eastern Cape",
    "Free State", "KwaZulu-Natal", "Gauteng",
}

# ── Label corrections ──────────────────────────────────────────────────────
LABEL_CORRECTIONS = {
    "Populationn"                                           : "Population",
    "Labour\nforce"                                         : "Labour force",
    "Formal sector (non-\nagricultural)"                    : "Formal sector (non-agricultural)",
    "Informal sector (non-\nagricultural)"                  : "Informal sector (non-agricultural)",
    "Not economically\nactive"                              : "Not economically active",
    "Discouraged work-\nseekers"                            : "Discouraged work-seekers",
    "Other (not economically\nactive)"                      : "Other (not economically active)",
    "Community and social\nservices"                        : "Community and social services",
    "Craft and related\ntrade"                              : "Craft and related trade",
    "Plant and machine\noperator"                           : "Plant and machine operator",
    "Own-account\nworker"                                   : "Own-account worker",
    "Unpaid household\nmember"                              : "Unpaid household member",
    "Skilled\nagriculture"                                  : "Skilled agriculture",
    "Sales and\nservices"                                   : "Sales and services",
    "Fetching water or collecting\nwood/dung"               : "Fetching water or collecting wood/dung",
    "Construction or major repairs to own or\nhousehold"    : "Construction or major repairs to own or household",
    "Hunting or fishing for\nhousehold use"                 : "Hunting or fishing for household use",
    "Produce other goods for\nhousehold use"                : "Produce other goods for household use",
    "Involvement in at least\none activity"                 : "Involvement in at least one activity",
    "How annual salary increment is\nnegotiated"            : "How annual salary increment is negotiated",
    "Trade union membership (both\nsexes)"                  : "Trade union membership",
    "Trade union membership (both sexes)"                   : "Trade union membership",
    "Nature of contract/agreement (both\nsexes)"            : "Nature of contract/agreement",
    "Nature of contract/agreement (both sexes)"             : "Nature of contract/agreement",
    "Pension/retirement fund\ncontribution"                 : "Pension/retirement fund contribution",
    "Entitled to maternity/paternity\nleave"                : "Entitled to maternity/paternity leave",
    "Entitled to any\npaid leave"                           : "Entitled to any paid leave",
    "Entitled to paid\nsick leave"                          : "Entitled to paid sick leave",
    "Medical aid\nbenefits"                                 : "Medical aid benefits",
    "UIF\ncontribution"                                     : "UIF contribution",
    "Income tax (PAYE/SITE)\ndeduction"                     : "Income tax (PAYE/SITE) deduction",
    "Less than primary\ncompleted"                          : "Less than primary completed",
    "Secondary not\ncompleted"                              : "Secondary not completed",
    "Secondary\ncompleted"                                  : "Secondary completed",
    "Living together like husband\nand wife"                : "Living together like husband and wife",
    "Divorced or\nseparated"                                : "Divorced or separated",
    "Never\nmarried"                                        : "Never married",
    "Long-term unemployment (1 year\nand more)"             : "Long-term unemployment (1 year and more)",
    "Short-term unemployment (less\nthan 1 year)"           : "Short-term unemployment (less than 1 year)",
    "Age group of the\nemployed"                            : "Age group of the employed",
    "Age group of the\nunemployed"                          : "Age group of the unemployed",
    "Age group of the not\neconomically active"             : "Age group of the not economically active",
    "Highest level of education of the\nemployed"           : "Highest level of education of the employed",
    "Highest level of education of the\nunemployed"         : "Highest level of education of the unemployed",
    "Highest level of education of the not\neconomically active": "Highest level of education of the not economically active",
    "Current marital status of the\nemployed"               : "Current marital status of the employed",
    "Current marital status of the\nunemployed"             : "Current marital status of the unemployed",
    "Current marital status of the not\neconomically active": "Current marital status of the not economically active",
    "Attending educational\ninstitution"                    : "Attending educational institution",
    "Not attending educational\ninstitution"                : "Not attending educational institution",
    "Previous\noccupation"                                  : "Previous occupation",
    "Previous\nindustry"                                    : "Previous industry",
    "Population 15\u201364\nyrs"                            : "Population 15\u201364 yrs",
    "Don\u2019t know"                                       : "Don't know",
    "Don`t know"                                            : "Don't know",
    # Q3/Q4 2025 renamed table labels
    "Characteristics of Outside the Labour Force"           : "Characteristics of the not economically active",
    "Outside the Labour Force"                              : "Not economically active",
    "Not in employment, education or training"              : "NEET",
    "Formal sector\n(non-agricultural)"                     : "Formal sector (non-agricultural)",
    "Informal sector\n(non-agricultural)"                   : "Informal sector (non-agricultural)",
    "15\u201324\nyears"                                     : "15\u201324 years",
    "25\u201334\nyears"                                     : "25\u201334 years",
    "35\u201344\nyears"                                     : "35\u201344 years",
    "45\u201354\nyears"                                     : "45\u201354 years",
    "55\u201364\nyears"                                     : "55\u201364 years",
}

DROP_LABELS = {
    "Both sexes", "South Africa", "15\u201364 years",
    "Population groups", "Age group", "Total employed",
    "Formal and informal sector (non-agricultural)",
    "Unemployment rate", "Employed/population ratio (absorption)",
    "Labour force participation rate",
    "Inactivity rate by age (both sexes)",
    "Inactivity rate by age (women)",
    "Inactivity rate by age (men)",
    "As percentage of the labour force (both sexes)",
    "As percentage of total employment (both sexes)",
    "Long-term unemployment (%)", "Proportion of the labour force",
    "Proportion of the unemployed",
    "Rates (%)", "Those who have worked in the past 5 years",
}


# ==========================================================================
# STANDARD TABLE CONFIGS  (all 8 PDFs)
# ==========================================================================

STANDARD_CONFIGS = {

    "table1_sex": {
        "type": "grouped", "group_values": ["Women", "Men"],
        "indicators": ["Population"],
        "base_pages": "24",
    },
    "table1_population_group": {
        "type": "grouped",
        "group_values": ["Black African", "Coloured", "Indian/Asian", "White"],
        "indicators": ["Population"],
        "base_pages": "24",
    },
    "table1_province": {
        "type": "geography", "has_metros": False,
        "indicators": ["Population"],
        "base_pages": "24",
    },
    "table2": {
        "type": "grouped", "group_values": ["Women", "Men"],
        "indicators": [
            "Population 15\u201364 yrs", "Labour force", "Employed",
            "Formal sector (non-agricultural)", "Informal sector (non-agricultural)",
            "Agriculture", "Private households", "Unemployed",
            "Not economically active", "Discouraged work-seekers",
            "Other (not economically active)",
        ],
        "base_pages": "25,26",
    },
    "table2_1": {
        "type": "grouped",
        "group_values": ["Black African", "Coloured", "Indian/Asian", "White"],
        "indicators": [
            "Population 15\u201364 yrs", "Labour force",
            "Employed", "Unemployed", "Not economically active",
        ],
        "base_pages": "27,28",
    },
    "table2_2": {
        "type": "grouped",
        "group_values": [
            "15\u201324 years", "25\u201334 years", "35\u201344 years",
            "45\u201354 years", "55\u201364 years",
        ],
        "indicators": ["Labour force", "Employed", "Unemployed", "Not economically active"],
        "base_pages": "29,30",
    },
    "table2_3": {
        "type": "geography",
        "indicators": [
            "Labour force", "Employed", "Unemployed", "Not economically active",
            "Discouraged work-seekers", "Other (not economically active)",
        ],
        "base_pages": "31-42",
    },
    "table2_4": {
        "type": "grouped", "group_values": ["Women", "Men"],
        "indicators": [
            "Population 15\u201364 yrs", "Labour force", "Employed",
            "Formal sector (non-agricultural)", "Informal sector (non-agricultural)",
            "Agriculture", "Private households", "Unemployed", "Not economically active",
        ],
        "base_pages": "43,44",
    },
    "table2_5": {
        "type": "grouped",
        "group_values": ["Black African", "Coloured", "Indian/Asian", "White"],
        "indicators": ["Labour force", "Employed", "Unemployed", "Not economically active"],
        "base_pages": "45,46",
    },
    "table2_6": {
        "type": "grouped",
        "group_values": [
            "15\u201324 years", "25\u201334 years", "35\u201344 years",
            "45\u201354 years", "55\u201364 years",
        ],
        "indicators": ["Labour force", "Employed", "Unemployed", "Not economically active"],
        "base_pages": "47,48",
    },
    "table2_7": {
        "type": "geography",
        "indicators": [
            "Labour force", "Employed", "Unemployed", "Not economically active",
            "Discouraged work-seekers", "Other (not economically active)",
        ],
        "base_pages": "49-56",
    },
    "table3_1": {
        "type": "grouped", "group_values": ["Women", "Men"],
        "indicators": [
            "Agriculture", "Mining", "Manufacturing", "Utilities",
            "Construction", "Trade", "Transport", "Finance",
            "Community and social services", "Private households", "Other",
        ],
        "base_pages": "57",
    },
    "table3_2": {
        "type": "geography", "has_metros": False,
        "indicators": [
            "Agriculture", "Mining", "Manufacturing", "Utilities",
            "Construction", "Trade", "Transport", "Finance",
            "Community and social services", "Private households",
        ],
        "base_pages": "58-61",
    },
    "table3_3": {
        "type": "grouped",
        "group_values": [
            "Formal sector (non-agricultural)",
            "Informal sector (non-agricultural)",
        ],
        "indicators": [
            "Mining", "Manufacturing", "Utilities", "Construction",
            "Trade", "Transport", "Finance", "Community and social services", "Other",
        ],
        "base_pages": "62",
    },
    "table3_4": {
        "type": "geography",
        "indicators": [
            "Formal sector (non-agricultural)", "Informal sector (non-agricultural)",
            "Agriculture", "Private households",
        ],
        "base_pages": "63-67",
    },
    "table3_5": {
        "type": "grouped", "group_values": ["Women", "Men"],
        "indicators": [
            "Manager", "Professional", "Technician", "Clerk",
            "Sales and services", "Skilled agriculture",
            "Craft and related trade", "Plant and machine operator",
            "Elementary", "Domestic worker",
        ],
        "base_pages": "68",
    },
    "table3_6": {
        "type": "grouped", "group_values": ["Women", "Men"],
        "indicators": [
            "Employee", "Employer", "Own-account worker", "Unpaid household member",
        ],
        "base_pages": "69",
    },
    "table3_7": {
        "type": "grouped", "group_values": ["Women", "Men"],
        "indicators": [
            "Working less than 15 hours per week",
            "Working 15\u201329 hours per week",
            "Working 30\u201339 hours per week",
            "Working 40\u201345 hours per week",
            "Working more than 45 hours per week",
        ],
        "base_pages": "70",
    },
    "table3_8a": {
        "type": "grouped", "group_values": ["Women", "Men"],
        "indicators": [
            "Pension/retirement fund contribution: Yes",
            "Pension/retirement fund contribution: No",
            "Pension/retirement fund contribution: Don't know",
        ],
        "base_pages": "71",
    },
    "table3_8b": {
        "type": "grouped", "group_values": ["Women", "Men"],
        "indicators": [
            "Entitled to any paid leave: Yes",
            "Entitled to any paid leave: No",
            "Entitled to any paid leave: Don't know",
        ],
        "base_pages": "71",
    },
    "table3_8c": {
        "type": "grouped", "group_values": ["Women", "Men"],
        "indicators": [
            "Entitled to paid sick leave: Yes",
            "Entitled to paid sick leave: No",
            "Entitled to paid sick leave: Don't know",
        ],
        "base_pages": "72",
    },
    "table3_8d": {
        "type": "grouped", "group_values": ["Women", "Men"],
        "indicators": [
            "Entitled to maternity/paternity leave: Yes",
            "Entitled to maternity/paternity leave: No",
            "Entitled to maternity/paternity leave: Don't know",
        ],
        "base_pages": "72",
    },
    "table3_8e": {
        "type": "grouped", "group_values": ["Women", "Men"],
        "indicators": [
            "UIF contribution: Yes",
            "UIF contribution: No",
            "UIF contribution: Don't know",
        ],
        "base_pages": "73",
    },
    "table3_8f": {
        "type": "grouped", "group_values": ["Women", "Men"],
        "indicators": [
            "Medical aid benefits: Yes",
            "Medical aid benefits: No",
            "Medical aid benefits: Don't know",
        ],
        "base_pages": "73",
    },
    "table3_8g": {
        "type": "grouped", "group_values": ["Women", "Men"],
        "indicators": [
            "Income tax (PAYE/SITE) deduction: Yes",
            "Income tax (PAYE/SITE) deduction: No",
            "Income tax (PAYE/SITE) deduction: Don't know",
        ],
        "base_pages": "74",
    },
    "table3_8h": {
        "type": "grouped", "group_values": ["Women", "Men"],
        "indicators": ["Written contract", "Verbal agreement"],
        "base_pages": "74",
    },
    "table3_8i": {
        "type": "grouped", "group_values": ["Women", "Men"],
        "indicators": ["Limited duration", "Permanent nature", "Unspecified duration"],
        "base_pages": "75",
    },
    "table3_8j": {
        "type": "grouped", "group_values": ["Women", "Men"],
        "indicators": [
            "Trade union membership: Yes",
            "Trade union membership: No",
            "Trade union membership: Don't know",
        ],
        "base_pages": "75",
    },
    "table3_8k": {
        "type": "grouped", "group_values": ["Women", "Men"],
        "indicators": [
            "Individual and employer", "Union and employer", "Bargaining council",
            "Employer only", "No regular increment", "Other",
        ],
        "base_pages": "76",
    },
    "table3_9_sex": {
        "type": "grouped", "group_values": ["Women", "Men"],
        "indicators": ["Underemployed"],
        "base_pages": "77",
    },
    "table3_9_industry": {
        "type": "grouped", "group_values": ["Industry"],
        "indicators": [
            "Agriculture", "Mining", "Manufacturing", "Utilities",
            "Construction", "Trade", "Transport", "Finance",
            "Community and social services", "Private households",
        ],
        "base_pages": "77",
    },
    "table3_9_occupation": {
        "type": "grouped", "group_values": ["Occupation"],
        "indicators": [
            "Manager", "Professional", "Technician", "Clerk",
            "Sales and services", "Skilled agriculture",
            "Craft and related trade", "Plant and machine operator",
            "Elementary", "Domestic worker",
        ],
        "base_pages": "77",
    },
    "table4_reason": {
        "type": "grouped", "group_values": ["Unemployed"],
        "indicators": ["Job losers", "Job leavers", "New entrants", "Re-entrants", "Other"],
        "base_pages": "78",
    },
    "table4_duration": {
        "type": "grouped", "group_values": ["Unemployed"],
        "indicators": [
            "Long-term unemployment (1 year and more)",
            "Short-term unemployment (less than 1 year)",
        ],
        "base_pages": "78",
    },
    "table4_prev_occupation": {
        "type": "grouped", "group_values": ["Previous occupation"],
        "indicators": [
            "Manager", "Professional", "Technician", "Clerk",
            "Sales and services", "Skilled agriculture",
            "Craft and related trade", "Plant and machine operator",
            "Elementary", "Domestic worker",
        ],
        "base_pages": "78",
    },
    "table4_prev_industry": {
        "type": "grouped", "group_values": ["Previous industry"],
        "indicators": [
            "Agriculture", "Mining", "Manufacturing", "Utilities",
            "Construction", "Trade", "Transport", "Finance",
            "Community and social services", "Private households",
        ],
        "base_pages": "79",
    },
    "table5": {
        "type": "grouped", "group_values": ["Not economically active"],
        "indicators": [
            "Student", "Homemaker", "Illness/disability",
            "Too old/young to work", "Discouraged work-seekers", "Other",
        ],
        "base_pages": "80",
    },
    "table6_age": {
        "type": "grouped",
        "group_values": [
            "Age group of the employed",
            "Age group of the unemployed",
            "Age group of the not economically active",
        ],
        "indicators": ["15-24 yrs", "25-34 yrs", "35-44 yrs", "45-54 yrs", "55-64 yrs"],
        "base_pages": "81",
    },
    "table6_education": {
        "type": "grouped",
        "group_values": [
            "Highest level of education of the employed",
            "Highest level of education of the unemployed",
            "Highest level of education of the not economically active",
        ],
        "indicators": [
            "No schooling", "Less than primary completed", "Primary completed",
            "Secondary not completed", "Secondary completed", "Tertiary", "Other",
        ],
        "base_pages": "81,82",
    },
    "table6_attendance": {
        "type": "grouped",
        "group_values": ["Employed", "Unemployed", "Not economically active"],
        "indicators": [
            "Attending educational institution",
            "Not attending educational institution",
        ],
        "base_pages": "82",
    },
    "table6_marital": {
        "type": "grouped",
        "group_values": [
            "Current marital status of the employed",
            "Current marital status of the unemployed",
            "Current marital status of the not economically active",
        ],
        "indicators": [
            "Married", "Living together like husband and wife",
            "Widow/widower", "Divorced or separated", "Never married",
        ],
        "base_pages": "83",
    },
    "table7_sex": {
        "type": "grouped", "group_values": ["Women", "Men"],
        "indicators": ["NEET"],
        "base_pages": "84",
    },
    "table7_age": {
        "type": "grouped",
        "group_values": ["15-24 yrs", "25-34 yrs", "35-44 yrs", "45-54 yrs", "55-64 yrs"],
        "indicators": ["NEET"],
        "base_pages": "84",
    },
    "table7_population_group": {
        "type": "grouped",
        "group_values": ["Black/African", "Coloured", "Indian/Asian", "White"],
        "indicators": ["NEET"],
        "base_pages": "84",
    },
    "table7_province": {
        "type": "geography", "has_metros": False,
        "indicators": ["NEET"],
        "base_pages": "84",
    },
    "table8": {
        "type": "geography", "has_metros": False,
        "indicators": [
            "Subsistence farming",
            "Fetching water or collecting wood/dung",
            "Produce other goods for household use",
            "Construction or major repairs to own or household",
            "Hunting or fishing for household use",
            "Involvement in at least one activity",
            "Employed", "Unemployed", "Not economically active",
        ],
        "base_pages": "85-88",
    },
}


# ==========================================================================
# EXTENDED TABLE CONFIGS  (Q3 2025 and Q4 2025 only)
# These use the ICSE-18 classification — NOT comparable with standard tables
# ==========================================================================

# Page numbers below are for Q3 2025 (offset +1 already applied separately)
# Q4 2025 uses the same base_pages (offset 0)
EXTENDED_CONFIGS = {

    "table3_6b": {
        "type": "grouped", "group_values": ["Women", "Men"],
        "indicators": [
            "Employers",
            "Independent workers without employees",
            "Dependent contractors",
            "Employees",
            "Contributing family workers",
        ],
        "base_pages": "64",         # Q3 2025 PDF page (after offset applied)
        "base_pages_q4": "63",      # Q4 2025 PDF page
        "classification": "ICSE-18",
        "comparable": False,
    },

    "table3_6c": {
        "type": "grouped", "group_values": ["Women", "Men"],
        "indicators": [
            "Employers",
            "Owner-managers of incorporated businesses",
            "Owner-operators of unincorporated businesses",
            "Independent workers without employees",
            "Dependent contractors",
            "Employees",
            "Contributing family workers",
        ],
        "base_pages": "65,66",
        "base_pages_q4": "64,65",
        "classification": "ICSE-18",
        "comparable": False,
    },

    "table3_10": {
        "type": "grouped", "group_values": ["Women", "Men"],
        "indicators": [
            "Formal employment",
            "Informal employment",
        ],
        "base_pages": "77,78",
        "base_pages_q4": "76,77",
        "classification": "ICSE-18",
        "comparable": False,
    },

    "table3_10b": {
        "type": "geography", "has_metros": False,
        "indicators": [
            "Formal employment",
            "Informal employment",
        ],
        "base_pages": "79,80",
        "base_pages_q4": "78,79",
        "classification": "ICSE-18",
        "comparable": False,
    },
}


def get_configs_for_pdf(pdf_filename: str) -> dict:
    """
    Return the correct config dict for a given PDF filename.
    Standard editions get STANDARD_CONFIGS only.
    Q3/Q4 2025 get STANDARD_CONFIGS + EXTENDED_CONFIGS with exact page overrides.
    """
    is_q3_25 = "3rdQuarter2025"  in pdf_filename
    is_q4_25 = "4thQuarter2025"  in pdf_filename
    is_ext   = is_q3_25 or is_q4_25
    page_map = Q3_2025_PAGES if is_q3_25 else (Q4_2025_PAGES if is_q4_25 else {})

    configs = {}

    for key, cfg in STANDARD_CONFIGS.items():
        c = dict(cfg)
        c["pages"] = page_map.get(key, cfg["base_pages"])
        configs[key] = c

    if is_ext:
        for key, cfg in EXTENDED_CONFIGS.items():
            c = dict(cfg)
            c["pages"] = page_map.get(key,
                cfg["base_pages_q4"] if is_q4_25 else cfg["base_pages"])
            configs[key] = c

    return configs


def detect_quarter_from_filename(filename: str) -> tuple[int, int]:
    """Extract (quarter, year) from PDF filename. Returns (0, 0) if unknown."""
    return PDF_REGISTRY.get(Path(filename).name, (0, 0))
