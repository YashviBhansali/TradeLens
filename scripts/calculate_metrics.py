
from pathlib import Path
import pandas as pd

# ==========================================
# PATHS
# ==========================================

ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = ROOT / "data" / "clean" / "trade_data.csv"
OUTPUT_DIR = ROOT / "data" / "clean"

df = pd.read_csv(INPUT_FILE)

# ==========================================
# VALIDATE INPUT
# ==========================================

required_columns = [
    "economy",
    "year",
    "hs_code",
    "partner_code",
    "partner",
    "import_value_usd",
]

missing = set(required_columns) - set(df.columns)

if missing:
    raise ValueError(f"Missing columns: {missing}")

df["import_value_usd"] = pd.to_numeric(
    df["import_value_usd"], errors="raise"
)

if (df["import_value_usd"] < 0).any():
    raise ValueError("Negative import values detected.")

# ==========================================
# PARTNER IMPORT VALUES
# ==========================================

group_columns = [
    "economy",
    "year",
    "hs_code",
    "partner_code",
]

partner_data = (
    df.groupby(group_columns, as_index=False)
    .agg(
        partner=("partner", "first"),
        import_value_usd=("import_value_usd", "sum"),
    )
)

# ==========================================
# CALCULATE IMPORT SHARES
# ==========================================

total_columns = ["economy", "year", "hs_code"]

partner_data["total_imports_usd"] = (
    partner_data.groupby(total_columns)[
        "import_value_usd"
    ].transform("sum")
)

partner_data["import_share_pct"] = (
    partner_data["import_value_usd"]
    / partner_data["total_imports_usd"]
    * 100
)

partner_data["import_share_pct"] = (
    partner_data["import_share_pct"].round(6)
)

partner_data = partner_data.sort_values(
    total_columns + ["import_share_pct"],
    ascending=[True, True, True, False]
)

# ==========================================
# HHI AND DEPENDENCY METRICS
# ==========================================

results = []

for keys, group in partner_data.groupby(total_columns):

    economy, year, hs_code = keys

    shares = group["import_share_pct"].to_numpy()

    hhi = (
        group["import_share_pct"] ** 2
    ).sum()

    sorted_group = group.sort_values(
        "import_share_pct",
        ascending=False
    )

    results.append({
        "economy": economy,
        "year": year,
        "hs_code": hs_code,
        "total_imports_usd": group[
            "total_imports_usd"
        ].iloc[0],
        "number_of_partners": len(group),
        "HHI": hhi,
        "effective_number_of_partners": (
            10000 / hhi if hhi > 0 else None
        ),
        "top_1_share_pct": shares.max(),
        "top_3_share_pct": sorted_group[
            "import_share_pct"
        ].head(3).sum(),
        "top_5_share_pct": sorted_group[
            "import_share_pct"
        ].head(5).sum(),
        "top_partner": sorted_group[
            "partner"
        ].iloc[0],
    })

metrics = pd.DataFrame(results)

# ==========================================
# TOP PARTNERS
# ==========================================

top_partners = (
    partner_data
    .sort_values(
        total_columns + ["import_share_pct"],
        ascending=[True, True, True, False]
    )
    .groupby(total_columns, group_keys=False)
    .head(5)
    .reset_index(drop=True)
)

# ==========================================
# HYPOTHETICAL DISRUPTION SCENARIO
# ==========================================

# Assumption: imports from the largest partner
# become unavailable, with no immediate substitution.
# This measures gross exposure, NOT predicted economic loss.

scenarios = []

for keys, group in partner_data.groupby(total_columns):

    economy, year, hs_code = keys

    largest = group.loc[
        group["import_value_usd"].idxmax()
    ]

    total = group["total_imports_usd"].iloc[0]

    scenarios.append({
        "economy": economy,
        "year": year,
        "hs_code": hs_code,
        "disrupted_partner": largest["partner"],
        "exposed_imports_usd": largest[
            "import_value_usd"
        ],
        "exposure_pct": (
            largest["import_value_usd"] / total * 100
        ),
        "remaining_imports_usd": (
            total - largest["import_value_usd"]
        ),
        "scenario_assumption": (
            "No immediate substitution or inventory buffer"
        ),
    })

scenario_df = pd.DataFrame(scenarios)

# ==========================================
# SAVE OUTPUTS
# ==========================================

partner_data.to_csv(
    OUTPUT_DIR / "partner_shares.csv",
    index=False
)

metrics.to_csv(
    OUTPUT_DIR / "concentration_metrics.csv",
    index=False
)

top_partners.to_csv(
    OUTPUT_DIR / "top_partners.csv",
    index=False
)

scenario_df.to_csv(
    OUTPUT_DIR / "disruption_scenarios.csv",
    index=False
)

# ==========================================
# PRINT RESULTS
# ==========================================

print("\n" + "=" * 65)
print("TRADELENS ECONOMIC ANALYSIS")
print("=" * 65)

print("\nCONCENTRATION METRICS")
print(metrics.to_string(index=False))

print("\nTOP PARTNERS")
print(top_partners.to_string(index=False))

print("\nDISRUPTION SCENARIOS")
print(scenario_df.to_string(index=False))

print("\nFiles generated:")
print("- partner_shares.csv")
print("- concentration_metrics.csv")
print("- top_partners.csv")
print("- disruption_scenarios.csv")

print("\nAnalysis completed.")
