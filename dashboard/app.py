
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st


# =========================================================
# 1. PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="TradeLens | Global Trade Intelligence",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# 2. DESIGN SYSTEM
# =========================================================

BG = "#0B1220"
PANEL = "#111D2E"
PANEL_LIGHT = "#17263A"
BORDER = "#263950"
TEXT = "#E8EEF5"
MUTED = "#91A3B8"
TEAL = "#39C6B0"
CYAN = "#55B8D9"
BLUE = "#6488E8"
AMBER = "#E8AD62"

CHART_TEMPLATE = "plotly_dark"

st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {{
        font-family: 'DM Sans', sans-serif;
    }}

    .stApp {{
        background: {BG};
        color: {TEXT};
    }}

    [data-testid="stHeader"] {{
        background: transparent;
    }}

    [data-testid="stSidebar"] {{
        background: #0E1929;
        border-right: 1px solid {BORDER};
    }}

    [data-testid="stSidebar"] > div:first-child {{
        padding-top: 1.5rem;
    }}

    h1, h2, h3 {{
        font-family: 'Manrope', sans-serif;
        color: {TEXT};
        letter-spacing: -0.5px;
    }}

    h1 {{
        font-weight: 800;
        letter-spacing: -1.5px;
    }}

    p, li {{
        color: #C2CDDA;
        line-height: 1.65;
    }}

    [data-testid="stMetric"] {{
        background: {PANEL};
        border: 1px solid {BORDER};
        border-radius: 12px;
        padding: 19px 20px;
        min-height: 112px;
    }}

    [data-testid="stMetricLabel"] {{
        color: {MUTED};
        font-size: 0.83rem;
    }}

    [data-testid="stMetricValue"] {{
        color: {TEXT};
        font-family: 'Manrope', sans-serif;
        font-weight: 700;
    }}

    [data-testid="stMetricDelta"] {{
        font-size: 0.8rem;
    }}

    div[data-testid="stTabs"] button {{
        font-weight: 600;
        color: {MUTED};
    }}

    div[data-testid="stTabs"] button[aria-selected="true"] {{
        color: {TEAL};
    }}

    .brand {{
        font-family: 'Manrope', sans-serif;
        font-size: 1.7rem;
        font-weight: 800;
        letter-spacing: -1.2px;
        color: #F4F7FB;
    }}

    .brand span {{
        color: {TEAL};
    }}

    .eyebrow {{
        color: {TEAL};
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 2px;
        text-transform: uppercase;
    }}

    .hero-subtitle {{
        color: {MUTED};
        font-size: 1rem;
        margin-top: -7px;
    }}

    .panel-note {{
        background: {PANEL};
        border: 1px solid {BORDER};
        border-left: 3px solid {TEAL};
        border-radius: 7px;
        padding: 14px 17px;
        color: #C8D4E1;
        margin: 12px 0;
        font-size: 0.9rem;
    }}

    .small-muted {{
        color: {MUTED};
        font-size: 0.82rem;
    }}

    .stSelectbox label, .stMultiSelect label {{
        color: #C6D1DF !important;
        font-weight: 600;
    }}

    hr {{
        border-color: {BORDER};
    }}

    [data-testid="stDataFrame"] {{
        border: 1px solid {BORDER};
        border-radius: 9px;
    }}

    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# 3. FILE PATHS AND DATA
# =========================================================

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "clean"


@st.cache_data
def load_data():

    filenames = {
        "concentration": "concentration_metrics.csv",
        "shares": "partner_shares.csv",
        "top": "top_partners.csv",
        "scenarios": "disruption_scenarios.csv",
        "residual": "residual_partner_audit_corrected.csv",
    }

    result = {}

    for key, filename in filenames.items():

        path = DATA_DIR / filename

        if not path.exists():
            raise FileNotFoundError(
                f"Missing data file: {path}"
            )

        result[key] = pd.read_csv(path)

    return result


try:
    data = load_data()

except Exception as error:
    st.error(f"Unable to load TradeLens data: {error}")
    st.stop()


concentration = data["concentration"]
shares = data["shares"]
top = data["top"]
scenarios = data["scenarios"]
residual = data["residual"]


# =========================================================
# 4. DATA PREPARATION
# =========================================================

all_frames = [
    concentration,
    shares,
    top,
    scenarios,
    residual,
]

for frame in all_frames:
    frame["year"] = pd.to_numeric(
        frame["year"], errors="coerce"
    )
    frame["hs_code"] = frame["hs_code"].astype(str)


numeric_columns = [
    (
        concentration,
        [
            "hhi",
            "effective_partner_count",
            "top1_share_pct",
            "top3_share_pct",
            "top5_share_pct",
            "residual_share_of_total_pct",
        ],
    ),
    (
        shares,
        [
            "import_value_usd",
            "import_share_pct",
        ],
    ),
    (
        top,
        [
            "import_value_usd",
            "import_share_pct",
        ],
    ),
    (
        scenarios,
        [
            "gross_exposure_usd",
            "gross_exposure_pct_of_scope_imports",
            "gross_exposure_pct_of_total_imports",
        ],
    ),
    (
        residual,
        [
            "residual_imports_usd",
            "individual_residual_share_pct",
            "total_residual_share_pct",
        ],
    ),
]

for frame, columns in numeric_columns:
    for column in columns:
        frame[column] = pd.to_numeric(
            frame[column], errors="coerce"
        )


# =========================================================
# 5. LABELS AND MAP COUNTRY NAMES
# =========================================================

ECONOMIES = ["Hong Kong", "Singapore"]

PRODUCTS = {
    "27": "Mineral fuels and oils",
    "84": "Machinery and mechanical appliances",
    "85": "Electrical machinery and equipment",
}

SCOPES = {
    "all_partner_categories": "All partner categories",
    "identified_countries_only": "Identified countries only",
}

# UN Comtrade partner names can differ from the names
# recognised by Plotly's geographic database.

COUNTRY_ALIASES = {
    "USA": "United States",
    "United States of America": "United States",
    "Rep. of Korea": "South Korea",
    "Republic of Korea": "South Korea",
    "Dem. People's Rep. of Korea": "North Korea",
    "Russian Federation": "Russia",
    "Viet Nam": "Vietnam",
    "Türkiye": "Turkey",
    "Iran (Islamic Republic of)": "Iran",
    "Iran, Islamic Rep. of": "Iran",
    "Lao People's Democratic Republic": "Laos",
    "Syrian Arab Republic": "Syria",
    "Côte d'Ivoire": "Ivory Coast",
    "Congo": "Republic of the Congo",
    "Democratic Republic of the Congo": "Democratic Republic of the Congo",
    "United Rep. of Tanzania": "Tanzania",
    "Bolivia (Plurinational State of)": "Bolivia",
    "Venezuela (Bolivarian Republic of)": "Venezuela",
    "Brunei Darussalam": "Brunei",
    "China, Hong Kong SAR": "Hong Kong",
    "China, Macao SAR": "Macao",
    "Czechia": "Czech Republic",
    "Türkiye": "Turkey",
}


# =========================================================
# 6. PLOTLY LAYOUT
# =========================================================

def style_chart(fig, height=430):

    fig.update_layout(
        template=CHART_TEMPLATE,
        paper_bgcolor=BG,
        plot_bgcolor=BG,
        font=dict(
            family="DM Sans, sans-serif",
            color=TEXT,
            size=12,
        ),
        title=dict(
            font=dict(
                family="Manrope, sans-serif",
                size=17,
                color=TEXT,
            ),
            x=0.02,
        ),
        margin=dict(
            l=20,
            r=25,
            t=65,
            b=35,
        ),
        height=height,
        hoverlabel=dict(
            bgcolor=PANEL_LIGHT,
            bordercolor=BORDER,
            font=dict(color=TEXT),
        ),
    )

    fig.update_xaxes(
        showgrid=True,
        gridcolor="#1C2B40",
        zeroline=False,
        linecolor=BORDER,
    )

    fig.update_yaxes(
        showgrid=True,
        gridcolor="#1C2B40",
        zeroline=False,
        linecolor=BORDER,
    )

    return fig


# =========================================================
# 7. SIDEBAR
# =========================================================

st.sidebar.markdown(
    '<div class="brand">Trade<span>Lens</span></div>',
    unsafe_allow_html=True,
)

st.sidebar.markdown(
    '<div class="eyebrow">GLOBAL TRADE INTELLIGENCE</div>',
    unsafe_allow_html=True,
)

st.sidebar.divider()

st.sidebar.markdown("### Research filters")

economy = st.sidebar.selectbox(
    "Reporting economy",
    ECONOMIES,
)

years = sorted(
    concentration["year"].dropna().astype(int).unique()
)

year = st.sidebar.selectbox(
    "Year",
    years,
    index=len(years) - 1,
)

chapter = st.sidebar.selectbox(
    "Product category",
    list(PRODUCTS.keys()),
    format_func=lambda value: (
        f"HS {value} · {PRODUCTS[value]}"
    ),
)

scope = st.sidebar.selectbox(
    "Analysis scope",
    list(SCOPES.keys()),
    format_func=lambda value: SCOPES[value],
    index=0,
)

st.sidebar.divider()

st.sidebar.markdown("### About TradeLens")

st.sidebar.markdown(
    """
    An independent research project examining:

    - Import-origin concentration
    - Trading-partner dependence
    - Residual import categories
    - Gross exposure to potential disruptions
    """
)

st.sidebar.caption(
    "Source: UN Comtrade | 2020–2025"
)

st.sidebar.caption(
    "All values are based on recorded merchandise imports."
)


# =========================================================
# 8. FILTER DATA
# =========================================================

def filter_data(frame):

    return frame[
        (frame["economy"] == economy)
        & (frame["year"] == year)
        & (frame["hs_code"] == chapter)
        & (frame["analysis_scope"] == scope)
    ].copy()


selected_metrics = filter_data(concentration)
selected_shares = filter_data(shares)
selected_top = filter_data(top)
selected_scenarios = filter_data(scenarios)

selected_residual = residual[
    (residual["economy"] == economy)
    & (residual["year"] == year)
    & (residual["hs_code"] == chapter)
].copy()


if selected_metrics.empty:
    st.error("No data available for the selected filters.")
    st.stop()


metric = selected_metrics.iloc[0]


# =========================================================
# 9. HEADER
# =========================================================

st.markdown(
    '<div class="eyebrow">TRADE DEPENDENCY RESEARCH · 2020—2025</div>',
    unsafe_allow_html=True,
)

st.title("Global Trade Exposure")

st.markdown(
    f'<div class="hero-subtitle">'
    f'Exploring the structure of imports and trading-partner '
    f'dependence in {economy}.'
    f'</div>',
    unsafe_allow_html=True,
)

st.write("")

st.caption(
    f"{economy}  /  {year}  /  "
    f"HS {chapter} — {PRODUCTS[chapter]}  /  "
    f"{SCOPES[scope]}"
)

st.divider()


# =========================================================
# 10. KPI CARDS
# =========================================================

k1, k2, k3, k4 = st.columns(4)

k1.metric(
    "Concentration · HHI",
    f"{metric['hhi']:,.0f}",
)

k2.metric(
    "Effective partner count",
    f"{metric['effective_partner_count']:.2f}",
)

k3.metric(
    "Largest source share",
    f"{metric['top1_share_pct']:.1f}%",
)

k4.metric(
    "Residual share",
    f"{metric['residual_share_of_total_pct']:.1f}%",
)


st.write("")


# =========================================================
# 11. TABS
# =========================================================

overview, concentration_tab, partners_tab, residual_tab, scenario_tab, methodology_tab = st.tabs(
    [
        "Overview",
        "Concentration",
        "Trading Partners",
        "Residual Categories",
        "Disruption Scenarios",
        "Methodology",
    ]
)


# =========================================================
# 12. OVERVIEW AND WORLD MAP
# =========================================================

with overview:

    st.markdown("## Global import network")

    st.markdown(
        """
        The map shows the geographic distribution of recorded
        import origins for the selected economy and product chapter.
        Countries with larger import values receive stronger colour
        intensity.
        """
    )

    map_data = selected_shares.copy()

    # Exclude residual categories: they do not represent
    # individually identifiable countries.

    map_data = map_data[
        map_data["is_residual"].astype(str).str.lower().isin(
            ["false", "0"]
        )
    ].copy()

    map_data["map_country"] = (
        map_data["partner"]
        .astype(str)
        .str.strip()
        .replace(COUNTRY_ALIASES)
    )

    # Remove non-geographic or non-country categories.

    excluded_names = {
        "World",
        "Areas, nes",
        "Special Categories",
        "Free Zones",
        "Bunkers",
        "Other",
    }

    map_data = map_data[
        ~map_data["map_country"].isin(excluded_names)
    ].copy()

    map_data = map_data[
        (map_data["import_value_usd"] > 0)
        & map_data["map_country"].notna()
    ].copy()

    if not map_data.empty:

        # Logarithmic scale makes smaller trading partners
        # visible while preserving the original trade values
        # in hover information.

        map_data["log_import_value"] = np.log10(
            map_data["import_value_usd"].clip(lower=1)
        )

        fig_map = px.choropleth(
            map_data,
            locations="map_country",
            locationmode="country names",
            color="log_import_value",
            hover_name="map_country",
            hover_data={
                "map_country": False,
                "import_value_usd": ":,.0f",
                "import_share_pct": ":.2f",
                "log_import_value": False,
            },
            color_continuous_scale=[
                [0.00, "#17283C"],
                [0.20, "#1C5260"],
                [0.45, "#238C91"],
                [0.70, "#35C2B0"],
                [1.00, "#B0F1D8"],
            ],
            labels={
                "import_value_usd": "Import value (USD)",
                "import_share_pct": "Share of imports (%)",
                "log_import_value": "Log10 import value",
            },
        )

        fig_map.update_geos(
            projection_type="natural earth",
            showland=True,
            landcolor="#172438",
            showocean=True,
            oceancolor=BG,
            showcountries=True,
            countrycolor="#35465B",
            showcoastlines=True,
            coastlinecolor="#50627A",
            showframe=False,
            showlakes=True,
            lakecolor=BG,
            bgcolor=BG,
            showrivers=False,
            lataxis_showgrid=False,
            lonaxis_showgrid=False,
        )

        fig_map.update_layout(
            paper_bgcolor=BG,
            plot_bgcolor=BG,
            font_color=TEXT,
            height=560,
            margin=dict(l=0, r=0, t=20, b=0),
            coloraxis_colorbar=dict(
                title="Trade value<br>(log scale)",
                tickfont=dict(color=MUTED),
                title_font=dict(color=TEXT),
                outlinewidth=0,
                thickness=12,
            ),
            hoverlabel=dict(
                bgcolor=PANEL_LIGHT,
                bordercolor=BORDER,
                font_color=TEXT,
            ),
        )

        st.plotly_chart(
            fig_map,
            width="stretch",
            config={
                "displayModeBar": False,
                "scrollZoom": False,
            },
        )

        st.caption(
            "Colour intensity represents the logarithm of import "
            "value in USD. Hover over a country for its original "
            "import value and share. Residual categories are excluded "
            "because they cannot be placed on a country map."
        )

    else:
        st.info(
            "No individually identifiable partner countries "
            "are available for this selection."
        )

    st.divider()

    st.markdown("## Import concentration comparison")

    comparison = concentration[
        (concentration["year"] == year)
        & (concentration["hs_code"] == chapter)
        & (concentration["analysis_scope"] == scope)
    ].copy()

    fig_comparison = px.bar(
        comparison,
        x="economy",
        y="hhi",
        color="economy",
        text_auto=".0f",
        color_discrete_map={
            "Hong Kong": BLUE,
            "Singapore": TEAL,
        },
        labels={
            "economy": "Economy",
            "hhi": "HHI",
        },
        title="Import-origin concentration by economy",
    )

    fig_comparison = style_chart(
        fig_comparison,
        height=350,
    )

    fig_comparison.update_layout(
        showlegend=False,
    )

    st.plotly_chart(
        fig_comparison,
        width="stretch",
    )

    st.markdown(
        """
        <div class="panel-note">
        Import concentration describes the distribution of recorded
        import origins. It does not independently establish how easily
        an economy could replace disrupted imports.
        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# 13. CONCENTRATION TAB
# =========================================================

with concentration_tab:

    st.markdown("## Import-origin concentration")

    trend = concentration[
        (concentration["economy"] == economy)
        & (concentration["hs_code"] == chapter)
        & (concentration["analysis_scope"] == scope)
    ].sort_values("year")

    fig = px.line(
        trend,
        x="year",
        y="hhi",
        markers=True,
        title=f"{economy} · HHI trend · HS {chapter}",
        labels={
            "year": "Year",
            "hhi": "Herfindahl–Hirschman Index",
        },
    )

    fig.update_traces(
        line=dict(color=TEAL, width=3),
        marker=dict(
            size=9,
            color=TEAL,
            line=dict(color=BG, width=2),
        ),
    )

    fig = style_chart(fig, 440)

    fig.update_xaxes(dtick=1)

    st.plotly_chart(
        fig,
        width="stretch",
    )

    st.markdown("### Concentration indicators")

    table = trend[
        [
            "year",
            "hhi",
            "effective_partner_count",
            "top1_share_pct",
            "top3_share_pct",
            "top5_share_pct",
        ]
    ].rename(
        columns={
            "year": "Year",
            "hhi": "HHI",
            "effective_partner_count": "Effective partners",
            "top1_share_pct": "Top 1 (%)",
            "top3_share_pct": "Top 3 (%)",
            "top5_share_pct": "Top 5 (%)",
        }
    )

    st.dataframe(
        table.round(2),
        width="stretch",
        hide_index=True,
    )

    st.caption(
        "Higher HHI values indicate more concentrated import origins."
    )


# =========================================================
# 14. TRADING PARTNERS TAB
# =========================================================

with partners_tab:

    st.markdown("## Trading-partner dependence")

    st.markdown(
        f"Leading import sources for {economy} in {year}."
    )

    if selected_top.empty:

        st.info("No partner records are available.")

    else:

        partner_chart = selected_top.sort_values(
            "import_share_pct",
            ascending=True,
        ).copy()

        partner_chart["source_type"] = np.where(
            partner_chart["is_residual"].astype(bool),
            "Residual category",
            "Identified country",
        )

        fig = px.bar(
            partner_chart,
            x="import_share_pct",
            y="partner",
            orientation="h",
            color="source_type",
            text=partner_chart["import_share_pct"].map(
                lambda x: f"{x:.1f}%"
            ),
            color_discrete_map={
                "Identified country": BLUE,
                "Residual category": AMBER,
            },
            title=f"Top import sources · HS {chapter}",
            labels={
                "import_share_pct": "Import share (%)",
                "partner": "Partner or category",
                "source_type": "Source type",
            },
        )

        fig = style_chart(fig, 430)

        fig.update_layout(
            showlegend=True,
            legend=dict(
                orientation="h",
                y=1.12,
            ),
        )

        st.plotly_chart(
            fig,
            width="stretch",
        )

        display = selected_top[
            [
                "rank",
                "partner",
                "partner_code",
                "import_value_usd",
                "import_share_pct",
                "is_residual",
            ]
        ].rename(
            columns={
                "rank": "Rank",
                "partner": "Partner or category",
                "partner_code": "Partner code",
                "import_value_usd": "Import value (USD)",
                "import_share_pct": "Import share (%)",
                "is_residual": "Residual",
            }
        )

        st.dataframe(
            display,
            width="stretch",
            hide_index=True,
            column_config={
                "Import value (USD)": st.column_config.NumberColumn(
                    format="$%.0f"
                ),
                "Import share (%)": st.column_config.NumberColumn(
                    format="%.2f%%"
                ),
            },
        )

    st.caption(
        "Residual categories represent broad or unspecified "
        "partner groupings, not individual countries."
    )


# =========================================================
# 15. RESIDUAL CATEGORIES TAB
# =========================================================

with residual_tab:

    st.markdown("## Residual import categories")

    st.markdown(
        """
        Some recorded import origins are represented by broad
        regional or unspecified categories. This section shows
        their contribution to total imports.
        """
    )

    residual_total = metric["residual_share_of_total_pct"]

    st.metric(
        "Combined residual share",
        f"{residual_total:.2f}%",
    )

    if selected_residual.empty:

        st.info("No residual records are available.")

    else:

        residual_chart = selected_residual.sort_values(
            "individual_residual_share_pct",
            ascending=True,
        )

        fig = px.bar(
            residual_chart,
            x="individual_residual_share_pct",
            y="partner",
            orientation="h",
            text=residual_chart[
                "individual_residual_share_pct"
            ].map(lambda x: f"{x:.2f}%"),
            title="Residual category share of total imports",
            labels={
                "individual_residual_share_pct": "Import share (%)",
                "partner": "Category",
            },
        )

        fig.update_traces(
            marker_color=AMBER,
        )

        fig = style_chart(fig, 400)

        fig.update_layout(
            showlegend=False,
        )

        st.plotly_chart(
            fig,
            width="stretch",
        )

        display = selected_residual[
            [
                "partner",
                "partner_code",
                "residual_imports_usd",
                "individual_residual_share_pct",
                "total_residual_share_pct",
            ]
        ].rename(
            columns={
                "partner": "Residual category",
                "partner_code": "Partner code",
                "residual_imports_usd": "Import value (USD)",
                "individual_residual_share_pct": "Individual share (%)",
                "total_residual_share_pct": "Combined share (%)",
            }
        )

        st.dataframe(
            display,
            width="stretch",
            hide_index=True,
            column_config={
                "Import value (USD)": st.column_config.NumberColumn(
                    format="$%.0f"
                ),
                "Individual share (%)": st.column_config.NumberColumn(
                    format="%.3f%%"
                ),
                "Combined share (%)": st.column_config.NumberColumn(
                    format="%.2f%%"
                ),
            },
        )

    st.markdown(
        """
        <div class="panel-note">
        Removing residual categories changes the denominator of
        identified-country shares. Both analysis scopes should
        therefore be interpreted separately.
        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# 16. DISRUPTION SCENARIOS TAB
# =========================================================

with scenario_tab:

    st.markdown("## Largest-partner gross exposure")

    st.markdown(
        """
        A hypothetical calculation of the gross import value
        associated with the largest recorded partner or category.
        """
    )

    if selected_scenarios.empty:

        st.info("No scenario data are available.")

    else:

        scenario = selected_scenarios.iloc[0]

        a, b, c = st.columns(3)

        a.metric(
            "Largest source",
            str(scenario["largest_partner_or_category"]),
        )

        b.metric(
            "Gross exposure",
            f"${scenario['gross_exposure_usd']:,.0f}",
        )

        c.metric(
            "Share of total imports",
            f"{scenario['gross_exposure_pct_of_total_imports']:.2f}%",
        )

        st.divider()

        st.markdown("### Scenario interpretation")

        st.write(
            f"For {economy}, in {year}, the largest recorded "
            f"import source for HS {chapter} is "
            f"**{scenario['largest_partner_or_category']}**."
        )

        st.write(
            f"The associated gross import exposure is "
            f"**${scenario['gross_exposure_usd']:,.0f}**, "
            f"equivalent to "
            f"**{scenario['gross_exposure_pct_of_total_imports']:.2f}%** "
            "of total imports in this chapter."
        )

        st.markdown(
            f"""
            <div class="panel-note">
            <strong>Assumption</strong><br>
            {scenario['assumption']}
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.warning(
        "This is a hypothetical gross-exposure calculation, "
        "not a forecast, realised economic loss or comprehensive "
        "measure of economic resilience."
    )


# =========================================================
# 17. METHODOLOGY TAB
# =========================================================

with methodology_tab:

    st.markdown("## Research methodology")

    st.markdown("### Research scope")

    st.write(
        """
        The project compares Singapore and Hong Kong using annual
        UN Comtrade import records from 2020 to 2025.
        """
    )

    st.dataframe(
        pd.DataFrame(
            {
                "HS chapter": ["27", "84", "85"],
                "Product category": [
                    "Mineral fuels and oils",
                    "Machinery and mechanical appliances",
                    "Electrical machinery and equipment",
                ],
            }
        ),
        width="stretch",
        hide_index=True,
    )

    st.markdown("### Concentration measurement")

    st.latex(r"HHI = \sum_{i=1}^{n} s_i^2")

    st.write(
        """
        Import shares are expressed as percentages.
        HHI is measured on a scale from values approaching
        zero to 10,000.
        """
    )

    st.latex(
        r"Effective\ Partner\ Count = \frac{10,000}{HHI}"
    )

    st.markdown("### Analysis scopes")

    st.markdown(
        """
        **All partner categories:** Includes every recorded
        partner category, including residual groupings.

        **Identified countries only:** Excludes residual categories
        and renormalises the shares of identified countries.
        """
    )

    st.markdown("### Disruption scenario")

    st.write(
        """
        The scenario uses the import value of the largest
        recorded partner or category. It assumes no immediate
        substitution or inventory buffer. It does not model
        alternative suppliers, price changes, transport routes,
        inventories or wider economic effects.
        """
    )

    st.markdown("### Data limitations")

    st.markdown(
        """
        - Data are aggregated at HS chapter level rather than
          individual product level.
        - Classification changes from H5 to H6 during the period:
          H5 applies to 2020–2021 and H6 to 2022–2025.
        - Matching chapter descriptions do not prove perfectly
          identical product composition across classifications.
        - Records have `isReported = False`. This flag alone does
          not establish that the values are mirror estimates.
        - 2025 annual records are present, but this does not
          establish that they are final.
        - Residual categories may represent substantial import
          shares and cannot be treated as individual countries.
        - Import concentration alone does not measure inventories,
          domestic production, substitution capacity or overall
          economic resilience.
        """
    )

    st.markdown("### Source")

    st.write(
        "United Nations Comtrade Database — annual merchandise imports."
    )


# =========================================================
# 18. FOOTER
# =========================================================

st.divider()

left, right = st.columns(2)

with left:
    st.markdown(
        '<div class="brand" style="font-size:1.15rem;">Trade<span>Lens</span></div>',
        unsafe_allow_html=True,
    )

with right:
    st.markdown(
        '<p style="text-align:right;color:#71839A;font-size:0.8rem;">'
        'INDEPENDENT DATA RESEARCH · UN COMTRADE · 2020–2025'
        '</p>',
        unsafe_allow_html=True,
    )
