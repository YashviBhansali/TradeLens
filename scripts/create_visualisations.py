
from pathlib import Path

import pandas as pd
import plotly.express as px

ROOT = Path(__file__).resolve().parents[1]
CLEAN = ROOT / "data" / "clean"
FIGURES = ROOT / "figures"

FIGURES.mkdir(parents=True, exist_ok=True)

metrics = pd.read_csv(CLEAN / "concentration_metrics.csv")
shares = pd.read_csv(CLEAN / "partner_shares.csv")
scenarios = pd.read_csv(CLEAN / "disruption_scenarios.csv")

for df in [metrics, shares, scenarios]:
    df["year"] = df["year"].astype(int)
    df["hs_code"] = df["hs_code"].astype(str)

# Use descriptive chapter labels
chapter_labels = {
    "27": "HS 27 — Mineral fuels and oils",
    "84": "HS 84 — Machinery and mechanical appliances",
    "85": "HS 85 — Electrical machinery and equipment"
}

# --------------------------------------------------
# FIGURE 1: CONCENTRATION TRENDS
# --------------------------------------------------

fig1 = px.line(
    metrics,
    x="year",
    y="hhi",
    color="economy",
    line_dash="analysis_scope",
    markers=True,
    facet_col="hs_code",
    facet_col_wrap=1,
    category_orders={
        "hs_code": ["27", "84", "85"],
        "analysis_scope": [
            "all_partner_categories",
            "identified_countries_only"
        ]
    },
    labels={
        "year": "Year",
        "hhi": "Herfindahl–Hirschman Index",
        "economy": "Economy",
        "analysis_scope": "Analysis scope",
        "hs_code": "HS chapter"
    },
    title="Import-Origin Concentration, 2020–2025"
)

fig1.update_layout(
    template="plotly_white",
    height=1050,
    hovermode="x unified",
    legend_title_text="Economy / analysis scope"
)

fig1.for_each_annotation(
    lambda a: a.update(
        text=chapter_labels.get(a.text.split("=")[-1], a.text)
    )
)

fig1.write_html(
    FIGURES / "concentration_trends.html",
    include_plotlyjs=True
)


# --------------------------------------------------
# FIGURE 2: TOP PARTNERS IN 2025
# --------------------------------------------------

top_2025 = shares[
    (shares["year"] == 2025)
    & (shares["analysis_scope"] == "all_partner_categories")
].copy()

top_2025 = (
    top_2025.sort_values(
        ["economy", "hs_code", "import_share_pct"],
        ascending=[True, True, False]
    )
    .groupby(["economy", "hs_code"])
    .head(5)
)

top_2025["chapter"] = top_2025["hs_code"].map(chapter_labels)

fig2 = px.bar(
    top_2025,
    x="import_share_pct",
    y="partner",
    color="economy",
    barmode="group",
    facet_col="chapter",
    facet_col_wrap=1,
    orientation="h",
    hover_data={
        "partner_code": True,
        "import_value_usd": ":,.0f",
        "is_residual": True
    },
    labels={
        "import_share_pct": "Share of total imports (%)",
        "partner": "Partner category",
        "economy": "Economy",
        "chapter": "HS chapter"
    },
    title="Five Largest Import Origins by Chapter, 2025"
)

fig2.update_layout(
    template="plotly_white",
    height=1050,
    legend_title_text="Economy"
)

fig2.write_html(
    FIGURES / "top_partners_2025.html",
    include_plotlyjs=True
)


# --------------------------------------------------
# FIGURE 3: RESIDUAL CATEGORY SHARE
# --------------------------------------------------

residual_trends = metrics[
    metrics["analysis_scope"] == "all_partner_categories"
].copy()

fig3 = px.line(
    residual_trends,
    x="year",
    y="residual_share_of_total_pct",
    color="economy",
    markers=True,
    facet_col="hs_code",
    facet_col_wrap=1,
    category_orders={
        "hs_code": ["27", "84", "85"]
    },
    labels={
        "year": "Year",
        "residual_share_of_total_pct": "Residual imports (%)",
        "economy": "Economy",
        "hs_code": "HS chapter"
    },
    title="Residual Partner Categories as a Share of Imports"
)

fig3.update_layout(
    template="plotly_white",
    height=950,
    hovermode="x unified"
)

fig3.for_each_annotation(
    lambda a: a.update(
        text=chapter_labels.get(a.text.split("=")[-1], a.text)
    )
)

fig3.write_html(
    FIGURES / "residual_partner_shares.html",
    include_plotlyjs=True
)


# --------------------------------------------------
# FIGURE 4: GROSS EXPOSURE
# --------------------------------------------------

exposure_2025 = scenarios[
    (scenarios["year"] == 2025)
    & (scenarios["analysis_scope"] == "all_partner_categories")
].copy()

exposure_2025["chapter"] = exposure_2025["hs_code"].map(
    chapter_labels
)

fig4 = px.bar(
    exposure_2025,
    x="hs_code",
    y="gross_exposure_pct_of_total_imports",
    color="economy",
    barmode="group",
    text="largest_partner_or_category",
    hover_data={
        "largest_partner_or_category": True,
        "gross_exposure_usd": ":,.0f",
        "gross_exposure_pct_of_total_imports": ":.2f"
    },
    labels={
        "hs_code": "HS chapter",
        "gross_exposure_pct_of_total_imports": "Gross exposure (% of total imports)",
        "economy": "Economy"
    },
    title="Largest-Partner Gross Import Exposure, 2025"
)

fig4.update_layout(
    template="plotly_white",
    height=600,
    legend_title_text="Economy"
)

fig4.write_html(
    FIGURES / "gross_exposure_2025.html",
    include_plotlyjs=True
)


# --------------------------------------------------
# COMPLETION
# --------------------------------------------------

print("\n" + "=" * 65)
print("TRADELENS VISUALISATIONS CREATED")
print("=" * 65)

for file in sorted(FIGURES.glob("*.html")):
    print(f"Created: {file.name}")

print("\nVisualisation generation completed.")
