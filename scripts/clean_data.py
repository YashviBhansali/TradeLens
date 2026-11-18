
from pathlib import Path
import pandas as pd

# ==========================================
# PATHS
# ==========================================

ROOT = Path(__file__).resolve().parents[1]

INPUT_DIR = ROOT / "data" / "processed"
OUTPUT_DIR = ROOT / "data" / "clean"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

FILES = [
    "singapore_hs27.csv",
    "singapore_hs84.csv",
    "singapore_hs85.csv",
    "hong_kong_hs27.csv",
    "hong_kong_hs84.csv",
    "hong_kong_hs85.csv",
]

PRODUCTS = {
    "27": "Mineral fuels and oils",
    "84": "Machinery and mechanical appliances",
    "85": "Electrical machinery and equipment",
}

# ==========================================
# LOAD AND STANDARDISE
# ==========================================

partner_datasets = []
world_datasets = []

for filename in FILES:

    path = INPUT_DIR / filename

    if not path.exists():
        raise FileNotFoundError(path)

    df = pd.read_csv(path, low_memory=False)

    # Determine economy from filename
    economy = (
        "Singapore" if filename.startswith("singapore")
        else "Hong Kong"
    )

    # Standardise relevant columns
    df["year"] = pd.to_numeric(
        df["period"], errors="coerce"
    )

    df["hs_code"] = (
        df["cmdCode"]
        .astype(str)
        .str.strip()
        .str.replace(r"\.0$", "", regex=True)
    )

    df["import_value_usd"] = pd.to_numeric(
        df["primaryValue"], errors="coerce"
    )

    df["partner_code"] = (
        df["partnerCode"].astype(str).str.strip()
    )

    df["partner"] = (
        df["partnerDesc"].astype(str).str.strip()
    )

    df["economy"] = economy

    df["product"] = df["hs_code"].map(PRODUCTS)

    # Confirm expected import flow
    if not df["flowCode"].eq("M").all():
        raise ValueError(
            f"Unexpected trade flow in {filename}"
        )

    # Separate World benchmark from individual partners
    is_world = (
        df["partner"].str.casefold() == "world"
    ) | (df["partner_code"] == "0")

    world = df[is_world].copy()
    partners = df[~is_world].copy()

    partner_datasets.append(partners)
    world_datasets.append(world)

# ==========================================
# COMBINE DATASETS
# ==========================================

partners = pd.concat(
    partner_datasets,
    ignore_index=True
)

world = pd.concat(
    world_datasets,
    ignore_index=True
)

# ==========================================
# SELECT ANALYSIS COLUMNS
# ==========================================

columns = [
    "economy",
    "year",
    "hs_code",
    "product",
    "partner_code",
    "partner",
    "import_value_usd",
    "classificationCode",
    "isReported",
    "isAggregate",
]

partners = partners[columns].copy()

world = world[columns].copy()

# Remove rows with invalid essential values
partners = partners.dropna(
    subset=[
        "economy",
        "year",
        "hs_code",
        "partner",
        "import_value_usd",
    ]
)

world = world.dropna(
    subset=["year", "hs_code", "import_value_usd"]
)

partners["year"] = partners["year"].astype(int)
world["year"] = world["year"].astype(int)

# ==========================================
# DUPLICATE CHECK
# ==========================================

keys = [
    "economy",
    "year",
    "hs_code",
    "partner_code",
    "classificationCode",
]

duplicates = partners.duplicated(
    subset=keys,
    keep=False
)

if duplicates.any():
    print("WARNING: Duplicate records found.")
    print(partners[duplicates].to_string(index=False))
    raise ValueError(
        "Resolve duplicate records before analysis."
    )

# ==========================================
# SORT DATA
# ==========================================

partners = partners.sort_values(
    ["economy", "hs_code", "year", "partner"]
)

world = world.sort_values(
    ["economy", "hs_code", "year"]
)

# ==========================================
# SAVE CLEAN DATA
# ==========================================

partners.to_csv(
    OUTPUT_DIR / "trade_data.csv",
    index=False
)

world.to_csv(
    OUTPUT_DIR / "world_totals.csv",
    index=False
)

# ==========================================
# GENERATE SUMMARY
# ==========================================

summary = (
    partners.groupby(
        ["economy", "hs_code", "year"]
    )
    .agg(
        partner_records=("partner", "size"),
        unique_partners=("partner_code", "nunique"),
        sum_partner_imports_usd=(
            "import_value_usd", "sum"
        ),
    )
    .reset_index()
)

world_summary = (
    world.groupby(
        ["economy", "hs_code", "year"]
    )["import_value_usd"]
    .sum()
    .reset_index(name="world_imports_usd")
)

summary = summary.merge(
    world_summary,
    on=["economy", "hs_code", "year"],
    how="left"
)

summary["difference_usd"] = (
    summary["world_imports_usd"]
    - summary["sum_partner_imports_usd"]
)

summary["partner_coverage_pct"] = (
    summary["sum_partner_imports_usd"]
    / summary["world_imports_usd"]
    * 100
)

summary.to_csv(
    OUTPUT_DIR / "trade_summary.csv",
    index=False
)

# ==========================================
# FINAL REPORT
# ==========================================

print("\n" + "=" * 65)
print("TRADELENS CLEANING COMPLETE")
print("=" * 65)

print("\nIndividual partner records:", len(partners))
print("World benchmark records:", len(world))

print("\nEconomies:")
print(partners["economy"].value_counts())

print("\nHS chapters:")
print(partners["hs_code"].value_counts())

print("\nYear coverage:")
print(partners["year"].value_counts().sort_index())

print("\nPartner coverage and reconciliation:")
print(summary.to_string(index=False))

print("\nFiles saved:")
print("data/clean/trade_data.csv")
print("data/clean/world_totals.csv")
print("data/clean/trade_summary.csv")
