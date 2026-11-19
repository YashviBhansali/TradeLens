
from pathlib import Path
import pandas as pd

# --------------------------------------------------
# TRADELENS: RESIDUAL PARTNER CATEGORY AUDIT
# --------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]

RAW_FILE = ROOT / "data" / "raw" / "comtrade_combined.csv"
OUTPUT_FILE = ROOT / "data" / "clean" / "residual_partner_audit.csv"

df = pd.read_csv(RAW_FILE, low_memory=False)

df["primaryValue"] = pd.to_numeric(
    df["primaryValue"], errors="coerce"
)

df["partnerCode"] = df["partnerCode"].astype(str).str.strip()
df["partnerDesc"] = df["partnerDesc"].astype(str).str.strip()

group_columns = ["reporterDesc", "refYear", "cmdCode"]

# Identify World benchmark records
world = df[
    df["partnerDesc"].str.casefold().eq("world")
    | df["partnerCode"].eq("0")
].copy()

# Identify residual / not-elsewhere-specified categories
residual = df[
    df["partnerDesc"].str.contains(
        r"\bnes\b|^Other ",
        case=False,
        regex=True,
        na=False
    )
].copy()

# Summarise residual partner values
residual_summary = (
    residual.groupby(
        group_columns + ["partnerCode", "partnerDesc"],
        dropna=False
    )["primaryValue"]
    .sum()
    .reset_index(name="residual_imports_usd")
)

# Sum all residual categories within each economy-year-chapter
residual_totals = (
    residual.groupby(group_columns)["primaryValue"]
    .sum()
    .reset_index(name="total_residual_imports_usd")
)

# Obtain World totals for each economy-year-chapter
world_totals = (
    world.groupby(group_columns)["primaryValue"]
    .sum()
    .reset_index(name="world_imports_usd")
)

# Combine totals
audit = residual_totals.merge(
    world_totals,
    on=group_columns,
    how="left"
)

audit["residual_share_of_world_pct"] = (
    audit["total_residual_imports_usd"]
    / audit["world_imports_usd"]
    * 100
)

# Attach individual residual category breakdowns
audit = audit.merge(
    residual_summary,
    on=group_columns,
    how="left"
)

audit = audit.sort_values(
    ["reporterDesc", "cmdCode", "refYear", "partnerDesc"]
)

# Save results
OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
audit.to_csv(OUTPUT_FILE, index=False)

# Display results
print("\n" + "=" * 65)
print("TRADELENS RESIDUAL PARTNER CATEGORY AUDIT")
print("=" * 65)

print("\n1. IDENTIFIED RESIDUAL CATEGORIES")

print(
    residual[["partnerCode", "partnerDesc"]]
    .drop_duplicates()
    .sort_values("partnerDesc")
    .to_string(index=False)
)

print("\n2. RESIDUAL IMPORT SHARES")

display_columns = [
    "reporterDesc",
    "refYear",
    "cmdCode",
    "partnerDesc",
    "residual_imports_usd",
    "world_imports_usd",
    "residual_share_of_world_pct"
]

print(
    audit[display_columns]
    .to_string(index=False)
)

print("\n3. OUTPUT")
print(f"Saved to: {OUTPUT_FILE}")

print("\nAudit completed.")
