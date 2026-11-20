
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CLEAN = ROOT / "data" / "clean"

shares = pd.read_csv(CLEAN / "partner_shares.csv")
metrics = pd.read_csv(CLEAN / "concentration_metrics.csv")
top = pd.read_csv(CLEAN / "top_partners.csv")
scenarios = pd.read_csv(CLEAN / "disruption_scenarios.csv")
residual = pd.read_csv(CLEAN / "residual_partner_audit_corrected.csv")


def normalise_boolean(series):
    if pd.api.types.is_bool_dtype(series):
        return series.fillna(False)
    return series.astype(str).str.strip().str.casefold().isin(
        {"true", "1", "yes", "y"}
    )


shares["is_residual"] = normalise_boolean(shares["is_residual"])
top["is_residual"] = normalise_boolean(top["is_residual"])

GROUP = ["economy", "year", "hs_code", "analysis_scope"]

checks = []


def record_check(name, passed, detail=""):
    checks.append({
        "check": name,
        "status": "PASS" if passed else "FAIL",
        "detail": detail
    })


# --------------------------------------------------
# 1. BASIC STRUCTURE
# --------------------------------------------------

record_check(
    "Expected economies",
    set(shares["economy"]) == {"Hong Kong", "Singapore"}
)

record_check(
    "Expected years",
    set(shares["year"]) == {2020, 2021, 2022, 2023, 2024, 2025}
)

record_check(
    "Expected HS chapters",
    set(shares["hs_code"].astype(str)) == {"27", "84", "85"}
)

record_check(
    "Both analysis scopes present",
    set(shares["analysis_scope"]) == {
        "all_partner_categories",
        "identified_countries_only"
    }
)

record_check(
    "Expected 72 concentration groups",
    len(metrics) == 72,
    f"Found {len(metrics)}"
)

record_check(
    "Expected 72 scenario rows",
    len(scenarios) == 72,
    f"Found {len(scenarios)}"
)


# --------------------------------------------------
# 2. PARTNER SHARE VALIDATION
# --------------------------------------------------

share_sums = (
    shares.groupby(GROUP)["import_share_pct"]
    .sum()
)

record_check(
    "Partner shares sum to 100%",
    np.allclose(share_sums.values, 100, atol=0.02),
    f"Maximum deviation: {abs(share_sums - 100).max():.8f} percentage points"
)

duplicate_partners = shares.duplicated(
    GROUP + ["partner_code"]
).sum()

record_check(
    "No duplicate partner entries within groups",
    duplicate_partners == 0,
    f"Duplicates: {duplicate_partners}"
)

identified = shares[
    shares["analysis_scope"] == "identified_countries_only"
]

record_check(
    "No residual categories in identified-country scope",
    not identified["is_residual"].any()
)


# --------------------------------------------------
# 3. INDEPENDENT HHI CALCULATION
# --------------------------------------------------

recalculated = (
    shares.assign(
        squared_share=shares["import_share_pct"] ** 2
    )
    .groupby(GROUP)["squared_share"]
    .sum()
    .reset_index(name="recalculated_hhi")
)

hhi_check = metrics.merge(
    recalculated,
    on=GROUP,
    how="left",
    validate="one_to_one"
)

hhi_difference = (
    hhi_check["hhi"] - hhi_check["recalculated_hhi"]
).abs()

record_check(
    "HHI independently recalculated",
    hhi_difference.max() < 0.10,
    f"Maximum difference: {hhi_difference.max():.8f}"
)

expected_effective_count = 10000 / hhi_check["recalculated_hhi"]
effective_difference = (
    hhi_check["effective_partner_count"] - expected_effective_count
).abs()

record_check(
    "Effective partner count matches HHI",
    effective_difference.max() < 0.001,
    f"Maximum difference: {effective_difference.max():.8f}"
)


# --------------------------------------------------
# 4. IMPORT VALUE RECONCILIATION
# --------------------------------------------------

share_values = (
    shares.groupby(GROUP)["import_value_usd"]
    .sum()
    .reset_index(name="recalculated_imports_usd")
)

value_check = metrics.merge(
    share_values,
    on=GROUP,
    how="left",
    validate="one_to_one"
)

value_difference = (
    value_check["analysis_imports_usd"]
    - value_check["recalculated_imports_usd"]
).abs()

record_check(
    "Partner values reconcile with analysis totals",
    np.allclose(
        value_check["analysis_imports_usd"],
        value_check["recalculated_imports_usd"],
        rtol=1e-8,
        atol=1
    ),
    f"Maximum difference: ${value_difference.max():,.4f}"
)

# Identified plus residual imports should equal total partner imports
composition_difference = (
    metrics["identified_imports_usd"]
    + metrics["residual_imports_usd"]
    - metrics["total_partner_imports_usd"]
).abs()

record_check(
    "Identified and residual imports reconcile",
    np.allclose(
        composition_difference,
        0,
        atol=1
    ),
    f"Maximum difference: ${composition_difference.max():,.4f}"
)


# --------------------------------------------------
# 5. TOP PARTNER VALIDATION
# --------------------------------------------------

largest = (
    shares.sort_values(
        GROUP + ["import_share_pct"],
        ascending=[True, True, True, True, False]
    )
    .groupby(GROUP)
    .head(1)
    [GROUP + ["partner", "partner_code", "import_share_pct"]]
    .rename(columns={
        "partner": "recalculated_top_partner",
        "partner_code": "recalculated_top_partner_code",
        "import_share_pct": "recalculated_top1_share"
    })
)

top_check = metrics.merge(
    largest,
    on=GROUP,
    how="left",
    validate="one_to_one"
)

record_check(
    "Top partner names match",
    (
        top_check["top_partner"].astype(str)
        == top_check["recalculated_top_partner"].astype(str)
    ).all()
)

record_check(
    "Top partner codes match",
    (
        top_check["top_partner_code"].astype(str)
        == top_check["recalculated_top_partner_code"].astype(str)
    ).all()
)

record_check(
    "Top-one shares match",
    np.allclose(
        top_check["top1_share_pct"],
        top_check["recalculated_top1_share"],
        atol=0.02
    )
)

ranked_shares = shares.sort_values(
    GROUP + ["import_share_pct"],
    ascending=[True, True, True, True, False]
)
top_share_totals = (
    ranked_shares.groupby(GROUP)["import_share_pct"]
    .agg(
        recalculated_top3=lambda values: values.head(3).sum(),
        recalculated_top5=lambda values: values.head(5).sum(),
    )
    .reset_index()
)
top_share_check = metrics.merge(
    top_share_totals,
    on=GROUP,
    how="left",
    validate="one_to_one"
)

record_check(
    "Top-three shares match",
    np.allclose(
        top_share_check["top3_share_pct"],
        top_share_check["recalculated_top3"],
        atol=0.02
    )
)

record_check(
    "Top-five shares match",
    np.allclose(
        top_share_check["top5_share_pct"],
        top_share_check["recalculated_top5"],
        atol=0.02
    )
)

# Independently rebuild the top-five output table from partner shares.
expected_top = (
    shares.sort_values(
        GROUP + ["import_value_usd"],
        ascending=[True, True, True, True, False]
    )
    .groupby(GROUP, sort=False)
    .head(5)
    .copy()
)
expected_top["rank"] = expected_top.groupby(GROUP).cumcount() + 1

top_compare = top.merge(
    expected_top[
        GROUP + [
            "rank", "partner_code", "partner",
            "import_value_usd", "import_share_pct"
        ]
    ],
    on=GROUP + ["rank", "partner_code"],
    how="outer",
    suffixes=("_actual", "_expected"),
    indicator=True,
    validate="one_to_one"
)

top_rows_match = top_compare["_merge"].eq("both").all()
top_names_match = (
    top_compare["partner_actual"].astype(str)
    == top_compare["partner_expected"].astype(str)
).all()
top_values_match = (
    np.allclose(
        top_compare["import_value_usd_actual"],
        top_compare["import_value_usd_expected"],
        rtol=1e-8,
        atol=1
    )
    and np.allclose(
        top_compare["import_share_pct_actual"],
        top_compare["import_share_pct_expected"],
        atol=0.02
    )
)

record_check(
    "Top-five partner output independently matches source shares",
    top_rows_match and top_names_match and top_values_match,
    f"Compared rows: {len(top_compare)}"
)


# --------------------------------------------------
# 6. DISRUPTION SCENARIO VALIDATION
# --------------------------------------------------

# Independently identify the largest partner and its import value
largest_scenario = (
    shares.sort_values(
        GROUP + ["import_share_pct"],
        ascending=[True, True, True, True, False]
    )
    .groupby(GROUP)
    .head(1)
    [GROUP + ["partner", "partner_code", "import_value_usd"]]
    .rename(columns={
        "partner": "expected_partner",
        "partner_code": "expected_partner_code",
        "import_value_usd": "expected_exposure_usd"
    })
)

# Match expected values to scenarios using group identifiers
scenario_check = scenarios.merge(
    largest_scenario,
    on=GROUP,
    how="left",
    validate="one_to_one"
)

record_check(
    "Scenario selects largest partner",
    (
        scenario_check["largest_partner_or_category"].astype(str)
        == scenario_check["expected_partner"].astype(str)
    ).all()
)

record_check(
    "Scenario partner code matches",
    (
        scenario_check["partner_code"].astype(str)
        == scenario_check["expected_partner_code"].astype(str)
    ).all()
)

exposure_difference = (
    scenario_check["gross_exposure_usd"]
    - scenario_check["expected_exposure_usd"]
).abs()

record_check(
    "Scenario exposure USD matches largest partner",
    np.allclose(
        scenario_check["gross_exposure_usd"],
        scenario_check["expected_exposure_usd"],
        rtol=1e-8,
        atol=1
    ),
    f"Maximum difference: ${exposure_difference.max():,.4f}"
)

# Merge the correct denominator from concentration metrics
scenario_check = scenario_check.drop(
    columns=["analysis_imports_usd"],
    errors="ignore"
)

scope_totals = metrics[
    GROUP + ["analysis_imports_usd", "total_partner_imports_usd"]
]

scenario_check = scenario_check.merge(
    scope_totals,
    on=GROUP,
    how="left",
    validate="one_to_one"
)

expected_scope_pct = (
    scenario_check["expected_exposure_usd"]
    / scenario_check["analysis_imports_usd"]
    * 100
)

record_check(
    "Scenario within-scope percentage matches",
    np.allclose(
        scenario_check["gross_exposure_pct_of_scope_imports"],
        expected_scope_pct,
        atol=0.02
    )
)

expected_total_pct = (
    scenario_check["expected_exposure_usd"]
    / scenario_check["total_partner_imports_usd"]
    * 100
)

record_check(
    "Scenario total-import percentage matches",
    np.allclose(
        scenario_check["gross_exposure_pct_of_total_imports"],
        expected_total_pct,
        atol=0.02
    )
)

record_check(
    "Scenario assumption is appropriately qualified",
    scenarios["assumption"].str.contains(
        "not a forecast",
        case=False,
        na=False
    ).all()
)


# --------------------------------------------------
# 7. RESIDUAL AUDIT VALIDATION
# --------------------------------------------------

record_check(
    "Residual audit has individual and total shares",
    {
        "individual_residual_share_pct",
        "total_residual_share_pct"
    }.issubset(residual.columns)
)

record_check(
    "Residual shares are non-negative",
    (
        residual["individual_residual_share_pct"].ge(0).all()
        and residual["total_residual_share_pct"].ge(0).all()
    )
)


# --------------------------------------------------
# 8. FINAL REPORT
# --------------------------------------------------

report = pd.DataFrame(checks)

print("\n" + "=" * 70)
print("TRADELENS INDEPENDENT METRICS VALIDATION")
print("=" * 70)

print(report.to_string(index=False))

passed = (report["status"] == "PASS").sum()
failed = (report["status"] == "FAIL").sum()

print("\n" + "-" * 70)
print(f"Checks passed: {passed}")
print(f"Checks failed: {failed}")
print("-" * 70)

report.to_csv(
    CLEAN / "independent_validation_report.csv",
    index=False
)

if failed:
    print("\nVALIDATION FAILED. Do not freeze the analysis yet.")
    raise SystemExit(1)

print("\nALL INDEPENDENT VALIDATION CHECKS PASSED.")
print("Analysis is ready for final review.")
