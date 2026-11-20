# TradeLens

**Import-origin concentration and hypothetical disruption exposure in Singapore and Hong Kong**

TradeLens is an independent data-analysis project examining the distribution of import origins in Singapore and Hong Kong. It compares the concentration of selected merchandise-import categories, identifies major trading-partner dependencies, and estimates the gross import value associated with the largest recorded source under a clearly defined hypothetical disruption scenario.

The project uses annual UN Comtrade data for 2020–2025 and presents the analysis through an interactive Streamlit dashboard.

## Research question

How does dependence on particular import partners differ between Singapore and Hong Kong, and what does import-origin concentration reveal about their exposure to potential trade disruptions?

The analysis focuses on:

- How concentrated are recorded import origins in selected product chapters?
- Which partner countries or partner categories account for the largest import shares?
- How do concentration measures differ between the two economies?
- How large is the gross import exposure associated with the largest recorded source?

## Data and scope

| Dimension | Coverage |
|---|---|
| Source | [UN Comtrade](https://comtradeplus.un.org/) |
| Period | 2020–2025 |
| Frequency | Annual |
| Trade flow | Merchandise imports |
| Reporting economies | Singapore and China, Hong Kong SAR |
| HS chapters | 27, 84 and 85 |
| Value field | UN Comtrade `primaryValue`, USD |

### Selected product chapters

| HS chapter | Product category |
|---|---|
| 27 | Mineral fuels, mineral oils and products of their distillation |
| 84 | Machinery and mechanical appliances |
| 85 | Electrical machinery and equipment |

The source records are chapter-level aggregates, not detailed product-level observations. The original combined source extract is retained at `data/raw/comtrade_combined.csv`.

## Methodology

### Import shares

For each economy, year and HS chapter, a partner's import share is:

`Partner share (%) = partner import value / total partner import value × 100`

The denominator is the sum of the recorded partner categories in the selected analysis scope. The cleaning workflow separately retains the UN Comtrade World benchmark and checks that partner totals reconcile with it.

### Import-origin concentration

The Herfindahl–Hirschman Index (HHI) is calculated from percentage shares:

`HHI = sum(partner share (%)²)`

The resulting scale ranges from values approaching zero to 10,000. A higher value indicates that imports are distributed across fewer or more unevenly sized recorded partner categories.

The effective number of equally sized partners is:

`Effective partner count = 10,000 / HHI`

The project also reports the combined shares of the largest one, three and five partner categories.

### Two analysis scopes

The project calculates concentration under two scopes:

1. **All partner categories** — includes every recorded partner category, including residual or regional groupings.
2. **Identified countries only** — excludes categories identified by the project as residual (including categories containing “nes” and categories beginning “Other ”), then recalculates shares over the remaining partner records.

The second scope is a sensitivity analysis. It should not be interpreted as a complete measure of geographic coverage if the source contains any non-country categories that are not captured by the residual-name rule.

### Hypothetical disruption exposure

For each group, the project identifies the largest recorded partner or category and reports its import value and share. The scenario assumes no immediate supplier substitution or inventory buffer.

This is a **gross exposure calculation**, not a forecast, probability estimate, realised loss, or comprehensive measure of economic resilience. It does not model inventories, supplier substitution, transport routes, price responses, domestic production or wider economic effects.

## Selected findings

### 2025 import-origin concentration

The table below shows HHI using **all recorded partner categories**.

| Economy | HS 27 | HS 84 | HS 85 |
|---|---:|---:|---:|
| Hong Kong | 3,668 | 2,595 | 2,426 |
| Singapore | 710 | 1,218 | 1,720 |

Hong Kong has higher measured import-origin concentration than Singapore in all three selected chapters in 2025. This is a statement about the recorded distribution of import origins, not a conclusion that one economy is categorically less resilient.

### Largest recorded sources in 2025

- **Hong Kong:** China accounts for approximately 58.0% of HS 27 imports, 48.0% of HS 84 imports and 44.1% of HS 85 imports.
- **Singapore:** The UAE accounts for approximately 17.6% of HS 27 imports; the United States accounts for approximately 23.6% of HS 84 imports.
- **Singapore, HS 85:** “Other Asia, nes” is the largest recorded category at approximately 33.35%. This is a residual grouping, not an individual country. Among identified countries, China is the largest partner at approximately 22.23%.

Residual categories are material in some groups. They are shown explicitly in the analysis and excluded from the country map because they cannot be assigned to one geographic country.

## Interactive dashboard

The Streamlit dashboard includes:

- A world choropleth showing identifiable import partner countries, with colour intensity based on import value.
- Economy, year, HS chapter and analysis-scope filters.
- HHI, effective partner count, top-partner share and residual-share indicators.
- Concentration trends and cross-economy comparisons.
- Largest partner/category tables.
- Residual-category analysis.
- Hypothetical gross-exposure scenarios.
- Methodology and data limitations.

The map uses a logarithmic colour scale to make smaller import sources visible. Hover details retain the original import value and import share. Residual and non-geographic categories are not plotted as countries.

## Run locally

Use Python 3.12 or a compatible version supported by the pinned dependencies.

```bash
git clone https://github.com/YashviBhansali/TradeLens.git
cd TradeLens

python -m venv .venv
source .venv/bin/activate       # macOS / Linux
# .venv\Scripts\activate      # Windows

python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Reproduce the analysis

Run the complete workflow from the repository root:

```bash
python scripts/run_pipeline.py
```

The pipeline runs the separation, validation, cleaning, source audits, metric calculations, independent validation and visualisation scripts in the required order. It stops if a step fails.

### Launch the dashboard

```bash
streamlit run dashboard/app.py
```

The dashboard reads the generated CSV files from `data/clean/`.

## Deploy on Streamlit Community Cloud

1. Sign in to [Streamlit Community Cloud](https://share.streamlit.io/).
2. Connect the GitHub repository `YashviBhansali/TradeLens`.
3. Select the branch to deploy.
4. Set the app file path to `dashboard/app.py`.
5. Deploy. The root-level `requirements.txt` supplies the Python dependencies.

The repository includes the cleaned data required by the dashboard, so the app does not need to call the UN Comtrade API at runtime.

## Repository structure

```text
TradeLens/
├── .github/
│   └── workflows/
│       └── ci.yml
├── .streamlit/
│   └── config.toml
├── data/
│   ├── raw/
│   │   └── comtrade_combined.csv
│   ├── processed/
│   └── clean/
├── dashboard/
│   └── app.py
├── figures/
│   └── *.html
├── scripts/
│   ├── split_comtrade.py
│   ├── validate_data.py
│   ├── clean_data.py
│   ├── audit_trade_data.py
│   ├── audit_partner_categories.py
│   ├── calculate_metrics.py
│   ├── validate_metrics.py
│   ├── create_visualisations.py
│   └── run_pipeline.py
├── .gitignore
├── README.md
└── requirements.txt
```

## Validation and reproducibility

The workflow includes source-data checks and an independent metrics-validation script. The latest recorded independent validation completed with **23 checks passed and 0 checks failed**. Running `python scripts/run_pipeline.py` regenerates the derived outputs and reruns the checks against the source extract.

A successful validation confirms the implemented arithmetic and internal consistency checks. It does not independently verify the completeness or accuracy of the underlying UN Comtrade observations.

## Data limitations

1. **Concentration is not resilience itself.** Import-origin shares do not measure inventories, substitutability, domestic production capacity, transport flexibility or the ability to absorb economic shocks.
2. **Residual partner groupings.** Categories such as “Other Asia, nes”, “Other Africa, nes”, “Oceania, nes”, “Other Europe, nes” and “LAIA, nes” can represent broad or unspecified origins. They are not individual countries and can materially affect concentration estimates.
3. **HS classification transition.** The source uses H5 (HS 2017) for 2020–2021 and H6 (HS 2022) for 2022–2025. Similar chapter descriptions do not prove perfectly identical product composition across the transition.
4. **Reporting flags.** The source contains `isReported` and `isOriginalClassification` fields. These flags are retained for audit purposes; `isReported = False` alone does not establish that a value is a mirror estimate or explain its provenance.
5. **2025 status.** Annual 2025 records are present in the extract, but their presence does not independently establish that every observation is final or complete.
6. **Scenario assumptions.** Gross exposure assumes no immediate substitution or inventory buffer. It is not a predicted or realised economic loss.

## Technology

Python · Pandas · NumPy · Plotly · Streamlit · UN Comtrade

## Author

Independent research project by Yashvi Bhansali.
