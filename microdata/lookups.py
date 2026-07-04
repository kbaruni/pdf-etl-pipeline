# =========================================================
# lookups.py  —  Geography and measure code lookups
# Source: Quarterly Labour Force Survey 1st Quarter 2025
#         metadata.pdf (Statistics South Africa, ISIbalo Data Portal)
# =========================================================

# ── Province name -> province_id (same numbering as QLFS PDF pipeline) ────
PROVINCE_ID = {
    "Western Cape"  : 1,
    "Eastern Cape"  : 2,
    "Free State"    : 3,
    "KwaZulu-Natal" : 4,
    "North West"    : 5,
    "Gauteng"       : 6,
    "Mpumalanga"    : 7,
    "Limpopo"       : 8,
    "Northern Cape" : 9,
}

# ── Metro_code (microdata, metadata p71) -> (province name, metro name) ───
# metro name is None for non-metro rows
METRO_CODE_MAP = {
    1:  ("Western Cape", None),
    2:  ("Western Cape", "City of Cape Town"),
    3:  ("Eastern Cape", None),
    4:  ("Eastern Cape", "Buffalo City"),
    5:  ("Eastern Cape", "Nelson Mandela Bay"),
    6:  ("Northern Cape", None),
    7:  ("Free State", None),
    8:  ("Free State", "Mangaung"),
    9:  ("KwaZulu-Natal", None),
    10: ("KwaZulu-Natal", "eThekwini"),
    11: ("North West", None),
    12: ("Gauteng", None),
    13: ("Gauteng", "Ekurhuleni"),
    14: ("Gauteng", "City of Johannesburg"),
    15: ("Gauteng", "City of Tshwane"),
    16: ("Mpumalanga", None),
    17: ("Limpopo", None),
}

# ── Metro name -> district_id / municipality_id (same IDs as PDF pipeline) ─
METRO_LOOKUP = {
    "City of Cape Town"    : {"district_id": 47, "municipality_id": 189},
    "Buffalo City"         : {"district_id":  3, "municipality_id": 180},
    "Nelson Mandela Bay"   : {"district_id": 10, "municipality_id": 179},
    "Mangaung"             : {"district_id": 15, "municipality_id": 202},
    "eThekwini"            : {"district_id": 29, "municipality_id": 168},
    "Ekurhuleni"           : {"district_id":  1, "municipality_id": 213},
    "City of Johannesburg" : {"district_id":  2, "municipality_id": 212},
    "City of Tshwane"      : {"district_id": 18, "municipality_id":  37},
}

# ── Measures available in this app ─────────────────────────────────────────
# Each entry: column name in the CSV, plain label, and the code list
# (value -> label) taken directly from the Metadata PDF.

MEASURES = {

    "gender": {
        "label": "Gender",
        "column": "Q13GENDER",
        "page": "p8",
        "codes": {
            1: "Men",
            2: "Women",
        },
    },

    "age_band": {
        "label": "Age band",
        "column": "age_grp1",
        "page": "p71",
        "codes": {
            1:  "Age 00\u201304",
            2:  "Age 05\u201309",
            3:  "Age 10\u201314",
            4:  "Age 15\u201319",
            5:  "Age 20\u201324",
            6:  "Age 25\u201329",
            7:  "Age 30\u201334",
            8:  "Age 35\u201339",
            9:  "Age 40\u201344",
            10: "Age 45\u201349",
            11: "Age 50\u201354",
            12: "Age 55\u201359",
            13: "Age 60\u201364",
            14: "Age 65\u201369",
            15: "Age 70\u201374",
            16: "Age 75+",
        },
    },

    "population_group": {
        "label": "Population group (ethnicity)",
        "column": "Q15POPULATION",
        "page": "p9",
        "codes": {
            1: "African/Black",
            2: "Coloured",
            3: "Indian/Asian",
            4: "White",
        },
    },

    "marital_status": {
        "label": "Marital status",
        "column": "Q16MARITALSTATUS",
        "page": "p9",
        "codes": {
            1: "Married",
            2: "Living together like husband and wife",
            3: "Widow/widower",
            4: "Divorced or separated",
            5: "Never married",
        },
    },

    "education_status": {
        "label": "Education status",
        "column": "Education_Status",
        "page": "p77",
        "codes": {
            1: "No schooling",
            2: "Less than primary completed",
            3: "Primary completed",
            4: "Secondary not completed",
            5: "Secondary completed",
            6: "Tertiary",
            7: "Other",
        },
    },
}

# ── Indicators available in this app ───────────────────────────────────────
# Each entry: column name in the CSV, plain label, code list, and whether
# an age 15-64 filter should be applied automatically (the QLFS working-age
# population convention).

INDICATORS = {

    "none": {
        "label": "(none — plain population count)",
        "column": None,
        "page": None,
        "codes": None,
        "working_age_only": False,
        "is_multi": False,
    },

    "status": {
        "label": "Labour market status",
        "column": "Status",
        "page": "p72",
        "codes": {
            1: "Employed",
            2: "Unemployed",
            3: "Discouraged job-seeker",
            4: "Other not economically active",
        },
        "working_age_only": True,
        "is_multi": True,
    },

    "industry": {
        "label": "Industry",
        "column": "Indus",
        "page": "p73",
        "codes": {
            1:  "Agriculture, hunting, forestry and fishing",
            2:  "Mining and quarrying",
            3:  "Manufacturing",
            4:  "Electricity, gas and water supply",
            5:  "Construction",
            6:  "Wholesale and retail trade",
            7:  "Transport, storage and communication",
            8:  "Financial intermediation, insurance, real estate and business services",
            9:  "Community, social and personal services",
            10: "Private households",
            11: "Other",
        },
        "working_age_only": True,
        "is_multi": True,
    },

    "occupation": {
        "label": "Occupation",
        "column": "Occup",
        "page": "p73-74",
        "codes": {
            1:  "Legislators, senior officials and managers",
            2:  "Professionals",
            3:  "Technical and associate professionals",
            4:  "Clerks",
            5:  "Service workers and shop and market sales workers",
            6:  "Skilled agricultural and fishery workers",
            7:  "Craft and related trades workers",
            8:  "Plant and machine operators and assemblers",
            9:  "Elementary occupation",
            10: "Domestic workers",
            11: "Other",
        },
        "working_age_only": True,
        "is_multi": True,
    },

    "neet": {
        "label": "NEET (Not in Employment, Education or Training)",
        "column": "NEET",
        "page": "p77",
        "codes": {
            1: "Yes — NEET",
        },
        "working_age_only": False,
        "is_multi": False,
    },

    "underemployment": {
        "label": "Underemployment",
        "column": "Underempl",
        "page": "p76",
        "codes": {
            1: "Underemployed",
        },
        "working_age_only": True,
        "is_multi": False,
    },

    "formal_informal": {
        "label": "Formal and Informal employment",
        "column": "Infempl",
        "page": "p75",
        "codes": {
            1: "Formal employment",
            2: "Informal employment",
        },
        "working_age_only": True,
        "is_multi": True,
    },
}


def metro_code_to_geo(metro_code: int) -> dict:
    """Resolve a Metro_code value to province_id/district_id/municipality_id."""
    province_name, metro_name = METRO_CODE_MAP[int(metro_code)]
    province_id = PROVINCE_ID[province_name]

    if metro_name is None:
        return {
            "province": province_id,
            "district": None,
            "municipality": None,
        }

    ids = METRO_LOOKUP[metro_name]
    return {
        "province": province_id,
        "district": ids["district_id"],
        "municipality": ids["municipality_id"],
    }
