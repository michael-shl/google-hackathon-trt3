"""Small hand-made corridor used when USE_MOCK_DATA=true.

Same shapes as the BigQuery tables (see docs/DATA_SOURCES.md) so every tool can be built and
demoed before the data lane finishes. Names are illustrative, not real Central Market businesses.
"""

BUSINESSES = {
    "B01": {"name": "Bayside Roasters", "address": "101 Market St", "naics4": "3119"},
    "B02": {"name": "Sixth St Cafe", "address": "600 Market St", "naics4": "7225"},
    "B03": {"name": "Yerba Deli", "address": "612 Market St", "naics4": "7225"},
    "B04": {"name": "Kearny Kitchen", "address": "20 Kearny St", "naics4": "7223"},
    "B05": {"name": "Larkin Event Hall", "address": "45 Larkin St", "naics4": "7111"},
    "B06": {"name": "Mint Plaza Parking", "address": "1 Mint Plaza", "naics4": "8129"},
    "B07": {"name": "Golden Produce Wholesale", "address": "220 Jessie St", "naics4": "4244"},
    "B08": {"name": "Civic Center Bistro", "address": "75 Hyde St", "naics4": "7225"},
    "B09": {"name": "Tenderloin Bakery", "address": "330 Eddy St", "naics4": "3118"},
    "B10": {"name": "Market St Hardware", "address": "900 Market St", "naics4": "4441"},
    "B11": {"name": "Jessie Print Shop", "address": "88 Jessie St", "naics4": "3231"},
    "B12": {"name": "Hyde Barber", "address": "112 Hyde St", "naics4": "8121"},
    "B13": {"name": "Polk Linen Service", "address": "500 Polk St", "naics4": "8123"},
    "B14": {"name": "Eddy St Diner", "address": "410 Eddy St", "naics4": "7225"},
}

# (supplier_id, buyer_id, intensity): supplier -> buyer, as in a4i_econ.supplies
SUPPLIES = [
    ("B01", "B02", 0.06), ("B01", "B03", 0.05), ("B01", "B04", 0.04), ("B01", "B08", 0.05),
    ("B01", "B14", 0.04),
    ("B04", "B05", 0.12),
    ("B07", "B02", 0.09), ("B07", "B03", 0.08), ("B07", "B04", 0.10), ("B07", "B08", 0.09),
    ("B07", "B09", 0.07), ("B07", "B14", 0.08),
    ("B09", "B02", 0.04), ("B09", "B08", 0.05), ("B09", "B14", 0.03),
    ("B10", "B11", 0.02), ("B10", "B13", 0.02),
    ("B11", "B05", 0.03), ("B11", "B10", 0.01),
    ("B13", "B04", 0.03), ("B13", "B05", 0.04), ("B13", "B08", 0.03),
]

APPLICANTS = [
    {"business_id": "B07", "requested_amount": 25000, "stated_need": "Lost a large restaurant account"},
    {"business_id": "B01", "requested_amount": 15000, "stated_need": "Roaster repair after equipment failure"},
    {"business_id": "B09", "requested_amount": 10000, "stated_need": "Rent increase; behind two months"},
    {"business_id": "B13", "requested_amount": 12000, "stated_need": "Delivery van replacement"},
    {"business_id": "B04", "requested_amount": 10000, "stated_need": "Catering demand down since office closures"},
    {"business_id": "B12", "requested_amount": 5000, "stated_need": "Foot traffic down"},
    {"business_id": "B06", "requested_amount": 10000, "stated_need": "Monthly permits cancelled"},
]

TRACTS = {
    "06075012400": {"total_pop": 4100, "median_income": 31000, "poverty_rate": 0.31, "no_vehicle_rate": 0.78, "assistance_rate": 0.24},
    "06075017601": {"total_pop": 5200, "median_income": 58000, "poverty_rate": 0.18, "no_vehicle_rate": 0.61, "assistance_rate": 0.12},
    "06075012502": {"total_pop": 3900, "median_income": 44000, "poverty_rate": 0.24, "no_vehicle_rate": 0.70, "assistance_rate": 0.19},
}

BUSINESS_TRACT = {
    "B01": "06075017601", "B02": "06075017601", "B03": "06075017601", "B04": "06075012502",
    "B05": "06075012502", "B06": "06075017601", "B07": "06075012400", "B08": "06075012400",
    "B09": "06075012400", "B10": "06075017601", "B11": "06075012502", "B12": "06075012400",
    "B13": "06075012502", "B14": "06075012400",
}

LOANS = [
    {"business_id": "B09", "bank_name": "Mission Community Bank", "gross_approval": 150000,
     "approval_date": "2021-04-12", "loan_status": "CHGOFF", "charged_off": True},
]
