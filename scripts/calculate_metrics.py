
from pathlib import Path
import pandas as pd

# ============================================================
# TRADELENS: FINAL PARTNER CONCENTRATION AND EXPOSURE METRICS
# ============================================================

ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = ROOT / "data" / "clean" / "trade_data.csv"
OUTPUT_DIR = ROOT / "data" / "clean"

# These are regional / residual partner groupings, not individual
# country suppliers. Keep them in the full analysis, but exclude
# them from the identified-country-only sensitivity analysis.
RESIDUAL_PATTERN = r"\bnes\b|^Other\s"

GROUP_COLUMNS = ["economy", "year", "hs_code"]

# ------------------------------------------------------------
# 1. LOAD AND CHECK DATA
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("TRADELENS CONCENTRATION ANALYSIS")
print("=" * 70)

df = pd.read_csv(INPUT_FILE, low_memory=False)

required_columns = [
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

missing_columns = [
    column for column in required_columns
    if column not in df.columns
]

if missing_columns:
    raise ValueError(
        f"Missing required columns: {missing_columns}"
    )

df["import_value_usd"] = pd.to_numeric(
    df["import_value_usd"],
    errors="coerce"
)

if df["import_value_usd"].isna().any():
    raise ValueError(
        "Missing or invalid import values found."
    )

if (df["import_value_usd"] < 0).any():
    raise ValueError(
        "Negative import values found."
    )

for column in [
    "economy",
    "product",
    "partner_code",
    "partner",
    "classificationCode",
]:
    df[column] = df[column].astype(str).str.strip()

df["year"] = pd.to_numeric(df["year"], errors="raise").astype(int)
df["hs_code"] = df["hs_code"].astype(str).str.strip()

# Remove World benchmark records if any remain.
# The analysis denominator will be the sum of individual
# partner records, not an additional World row.
world_mask = (
    df["partner"].str.casefold().eq("world")
    | df["partner_code"].eq("0")
)

world_rows_removed = int(world_mask.sum())
df = df.loc[~world_mask].copy()

if df.empty:
    raise ValueError("No individual partner records remain.")

# ------------------------------------------------------------
# 2. IDENTIFY RESIDUAL PARTNER GROUPINGS
# ------------------------------------------------------------

df["is_residual"] = df["partner"].str.contains(
    RESIDUAL_PATTERN,
    case=False,
    regex=True,
    na=False,
)

print(f"\nIndividual partner records: {len(df):,}")
print(f"World rows removed: {world_rows_removed:,}")

print("\nResidual categories identified:")

residual_categories = sorted(
    df.loc[df["is_residual"], "partner"].dropna().unique()
)

for category in residual_categories:
    print(f"- {category}")

if not residual_categories:
    print("None identified.")

# ------------------------------------------------------------
# 3. CHECK CLASSIFICATION CONSISTENCY
# ------------------------------------------------------------

classification_counts = (
    df.groupby(GROUP_COLUMNS)["classificationCode"]
    .nunique()
)

if (classification_counts > 1).any():
    problem_groups = classification_counts[
        classification_counts > 1
    ]

    raise ValueError(
        "Multiple HS classifications found within the same "
        "economy-year-chapter groups:\n"
        f"{problem_groups}"
    )

# ------------------------------------------------------------
# 4. AGGREGATE PARTNER RECORDS
# ------------------------------------------------------------

# Aggregate any repeated observations for the same partner
# within an economy, year and HS chapter.

partner_data = (
    df.groupby(
        GROUP_COLUMNS + [
            "product",
            "partner_code",
            "partner",
            "classificationCode",
            "is_residual",
        ],
        dropna=False,
        as_index=False,
    )
    .agg(
        import_value_usd=("import_value_usd", "sum")
    )
)

if partner_data.duplicated(
    GROUP_COLUMNS + ["partner_code"]
).any():
    raise ValueError(
        "Duplicate partner codes remain within an economy-year-HS group. "
        "Inspect partner names and codes before continuing."
    )

# ------------------------------------------------------------
# 5. CALCULATE CONCENTRATION METRICS
# ------------------------------------------------------------

metric_rows = []
share_rows = []
top_partner_rows = []
scenario_rows = []
residual_audit_rows = []

for group_values, group in partner_data.groupby(
    GROUP_COLUMNS,
    sort=True,
):
    economy, year, hs_code = group_values

    group = group.copy()

    total_imports = group["import_value_usd"].sum()

    residual_data = group[group["is_residual"]].copy()
    identified_data = group[~group["is_residual"]].copy()

    residual_imports = residual_data["import_value_usd"].sum()
    identified_imports = identified_data["import_value_usd"].sum()

    if total_imports <= 0:
        raise ValueError(
            f"Non-positive total imports: {group_values}"
        )

    residual_share_of_total = (
        residual_imports / total_imports * 100
    )

    identified_share_of_total = (
        identified_imports / total_imports * 100
    )

    product_name = group["product"].iloc[0]
    classification = group["classificationCode"].iloc[0]

    # --------------------------------------------------------
    # 5A. RESIDUAL PARTNER AUDIT
    # --------------------------------------------------------

    for _, row in residual_data.iterrows():
        individual_share = (
            row["import_value_usd"] / total_imports * 100
        )

        residual_audit_rows.append({
            "economy": economy,
            "year": year,
            "hs_code": hs_code,
            "product": product_name,
            "partner_code": row["partner_code"],
            "partner": row["partner"],
            "residual_imports_usd": row["import_value_usd"],
            "total_partner_imports_usd": total_imports,
            "individual_residual_share_pct": individual_share,
            "total_residual_share_pct": residual_share_of_total,
            "classificationCode": classification,
        })

    # --------------------------------------------------------
    # 5B. TWO ANALYSIS SCOPES
    # --------------------------------------------------------

    analysis_scopes = [
        ("all_partner_categories", group),
        ("identified_countries_only", identified_data),
    ]

    for scope_name, scope_data in analysis_scopes:

        if scope_data.empty:
            continue

        analysis_imports = scope_data["import_value_usd"].sum()

        if analysis_imports <= 0:
            raise ValueError(
                f"Non-positive analysis imports: "
                f"{economy}, {year}, {hs_code}, {scope_name}"
            )

        scope_data = scope_data.copy()

        # Calculate shares using unrounded values.
        scope_data["import_share_pct"] = (
            scope_data["import_value_usd"]
            / analysis_imports
            * 100
        )

        # HHI = sum of squared percentage shares.
        hhi = (
            scope_data["import_share_pct"] ** 2
        ).sum()

        effective_partners = 10000 / hhi if hhi > 0 else None

        ranked = scope_data.sort_values(
            "import_value_usd",
            ascending=False,
        ).copy()

        top1 = ranked["import_share_pct"].iloc[0]
        top3 = ranked["import_share_pct"].head(3).sum()
        top5 = ranked["import_share_pct"].head(5).sum()

        top_partner = ranked["partner"].iloc[0]
        top_partner_code = ranked["partner_code"].iloc[0]
        top_partner_imports = ranked["import_value_usd"].iloc[0]

        # Record concentration metrics.
        metric_rows.append({
            "economy": economy,
            "year": year,
            "hs_code": hs_code,
            "product": product_name,
            "analysis_scope": scope_name,
            "classificationCode": classification,

            "total_partner_imports_usd": total_imports,
            "analysis_imports_usd": analysis_imports,
            "identified_imports_usd": identified_imports,
            "residual_imports_usd": residual_imports,

            "identified_share_of_total_pct": identified_share_of_total,
            "residual_share_of_total_pct": residual_share_of_total,

            "partner_count": len(scope_data),
            "hhi": hhi,
            "effective_partner_count": effective_partners,

            "top1_share_pct": top1,
            "top3_share_pct": top3,
            "top5_share_pct": top5,

            "top_partner": top_partner,
            "top_partner_code": top_partner_code,
        })

        # Record individual partner shares.
        for _, row in scope_data.iterrows():
            share_rows.append({
                "economy": economy,
                "year": year,
                "hs_code": hs_code,
                "product": product_name,
                "analysis_scope": scope_name,
                "partner_code": row["partner_code"],
                "partner": row["partner"],
                "import_value_usd": row["import_value_usd"],
                "import_share_pct": row["import_share_pct"],
                "is_residual": row["is_residual"],
                "classificationCode": classification,
            })

        # Record top five partners / categories.
        for rank, (_, row) in enumerate(
            ranked.head(5).iterrows(),
            start=1,
        ):
            top_partner_rows.append({
                "economy": economy,
                "year": year,
                "hs_code": hs_code,
                "product": product_name,
                "analysis_scope": scope_name,
                "rank": rank,
                "partner_code": row["partner_code"],
                "partner": row["partner"],
                "import_value_usd": row["import_value_usd"],
                "import_share_pct": row["import_share_pct"],
                "is_residual": row["is_residual"],
            })

        # Gross exposure scenario:
        # largest category / identified country unavailable,
        # assuming no immediate substitution or inventory buffers.
        scenario_rows.append({
            "economy": economy,
            "year": year,
            "hs_code": hs_code,
            "product": product_name,
            "analysis_scope": scope_name,
            "largest_partner_or_category": top_partner,
            "partner_code": top_partner_code,
            "gross_exposure_usd": top_partner_imports,
            "gross_exposure_pct_of_scope_imports": top1,
            "gross_exposure_pct_of_total_imports": (
                top_partner_imports / total_imports * 100
            ),
            "assumption": (
                "Gross exposure under no immediate substitution "
                "or inventory buffer assumptions; not a forecast "
                "or realised economic loss."
            ),
        })

        # Validation: shares must add up to 100%.
        share_total = scope_data["import_share_pct"].sum()

        if abs(share_total - 100) > 1e-8:
            raise ValueError(
                f"Share total is not 100% for "
                f"{economy}, {year}, {hs_code}, {scope_name}: "
                f"{share_total}"
            )

        if not (0 <= hhi <= 10000):
            raise ValueError(
                f"HHI outside valid range: {hhi}"
            )

# ------------------------------------------------------------
# 6. CREATE OUTPUT DATAFRAMES
# ------------------------------------------------------------

metrics = pd.DataFrame(metric_rows)
shares = pd.DataFrame(share_rows)
top_partners = pd.DataFrame(top_partner_rows)
scenarios = pd.DataFrame(scenario_rows)
residual_audit = pd.DataFrame(residual_audit_rows)

# Sort outputs consistently.
if not metrics.empty:
    metrics = metrics.sort_values(
        ["economy", "hs_code", "year", "analysis_scope"]
    )

if not shares.empty:
    shares = shares.sort_values(
        [
            "economy",
            "hs_code",
            "year",
            "analysis_scope",
            "import_share_pct",
        ],
        ascending=[True, True, True, True, False],
    )

if not top_partners.empty:
    top_partners = top_partners.sort_values(
        ["economy", "hs_code", "year", "analysis_scope", "rank"]
    )

if not scenarios.empty:
    scenarios = scenarios.sort_values(
        ["economy", "hs_code", "year", "analysis_scope"]
    )

if not residual_audit.empty:
    residual_audit = residual_audit.sort_values(
        ["economy", "hs_code", "year", "partner"]
    )

# ------------------------------------------------------------
# 7. SAVE OUTPUTS
# ------------------------------------------------------------

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

outputs = {
    "partner_shares.csv": shares,
    "concentration_metrics.csv": metrics,
    "top_partners.csv": top_partners,
    "disruption_scenarios.csv": scenarios,
    "residual_partner_audit_corrected.csv": residual_audit,
}

for filename, output_df in outputs.items():
    output_path = OUTPUT_DIR / filename
    output_df.to_csv(output_path, index=False)
    print(f"\nSaved: {output_path}")

# ------------------------------------------------------------
# 8. FINAL VALIDATION
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("FINAL VALIDATION")
print("=" * 70)

print(f"\nEconomies: {sorted(metrics['economy'].unique())}")
print(f"Years: {sorted(metrics['year'].unique())}")
print(f"HS chapters: {sorted(metrics['hs_code'].unique())}")

print(f"\nConcentration rows: {len(metrics)}")
print(f"Partner-share rows: {len(shares)}")
print(f"Top-partner rows: {len(top_partners)}")
print(f"Scenario rows: {len(scenarios)}")
print(f"Residual audit rows: {len(residual_audit)}")

print("\nAnalysis scopes:")
print(metrics["analysis_scope"].value_counts().to_string())

print("\nConcentration results (2025):")

latest = metrics[metrics["year"] == metrics["year"].max()]

display_columns = [
    "economy",
    "hs_code",
    "analysis_scope",
    "partner_count",
    "hhi",
    "effective_partner_count",
    "top1_share_pct",
    "top3_share_pct",
    "top5_share_pct",
    "residual_share_of_total_pct",
    "top_partner",
]

print(
    latest[display_columns]
    .round(3)
    .to_string(index=False)
)

print("\nResidual category coverage (2025):")

if not residual_audit.empty:
    residual_latest = (
        residual_audit[
            residual_audit["year"] == residual_audit["year"].max()
        ][
            [
                "economy",
                "hs_code",
                "partner",
                "individual_residual_share_pct",
                "total_residual_share_pct",
            ]
        ]
    )

    print(
        residual_latest
        .round(3)
        .to_string(index=False)
    )
else:
    print("No residual categories found.")

# Every economy-year-chapter group should have both scopes.
scope_counts = (
    metrics.groupby(GROUP_COLUMNS)["analysis_scope"]
    .nunique()
)

if not (scope_counts == 2).all():
    raise ValueError(
        "Some economy-year-chapter groups do not have both analysis scopes."
    )

print("\nAll validation checks passed.")
print("Concentration analysis completed.")
