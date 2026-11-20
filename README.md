# TradeLens
### Import-origin concentration and disruption exposure in Singapore and Hong Kong

TradeLens is an independent data-analysis project examining the concentration of import origins in Singapore and Hong Kong and the gross exposure of selected import categories to a hypothetical disruption involving a major import source.

The project uses annual merchandise-import data from the United Nations Comtrade database for 2020–2025. It combines reproducible Python data-processing scripts, independent calculation checks, interactive Plotly visualisations and a Streamlit dashboard.

**Research question:** How does dependence on particular import-source categories differ between Singapore and Hong Kong, and what does that imply about their exposure to a disruption in selected goods categories?

---

## Research scope

| Dimension | Coverage |
|---|---|
| Source | [UN Comtrade](https://comtradeplus.un.org/) |
| Period | 2020–2025 |
| Frequency | Annual |
| Flow | Imports |
| Reporting economies | Singapore and Hong Kong SAR |
| Product chapters | HS 27, HS 84 and HS 85 |
| Value field | Primary trade value, USD |

### Product chapters

| HS chapter | Description |
|---|---|
| 27 | Mineral fuels, mineral oils and products of their distillation |
| 84 | Machinery and mechanical appliances |
| 85 | Electrical machinery and equipment |

The data are analysed at HS chapter level. The project does not claim to measure individual product-level supply chains.

## Methodology

### Import-source shares

For each economy, year and HS chapter, partner-category import values are divided by the sum of partner-category values in the relevant analysis scope.

### Herfindahl–Hirschman Index

Import-origin concentration is measured using the HHI. Import shares are expressed as percentages and squared before summation:

**HHI = sum of squared import shares**

The resulting index ranges from values approaching zero to 10,000. A higher value indicates that imports are distributed across fewer or more unequal source categories.

### Effective number of partners

The effective number of equally sized source categories corresponding to the observed HHI is:

**Effective partner count = 10,000 / HHI**

### Top-partner dependence

The project calculates the combined shares of the largest one, three and five partner categories.

### Two analysis scopes

To show how broad residual categories affect concentration estimates, the analysis reports two scopes:

1. **All partner categories:** includes all recorded partner categories, including regional and unspecified residual groupings.
2. **Identified countries only:** excludes the residual groupings identified in the data and recalculates shares across the remaining identified-country records.

These scopes answer different questions and should be interpreted separately.

### Hypothetical gross-exposure scenario

For each group, the scenario reports the import value represented by its largest recorded partner or category. It assumes no immediate substitution and no inventory buffer.

This is a static gross-exposure calculation. It is **not** a forecast, a probability estimate, a realised loss or a measure of the economy-wide cost of a disruption.

---

## Selected findings

### 2025 import-origin concentration

The table reports HHI using **all partner categories**.

| Economy | HS 27 | HS 84 | HS 85 |
|---|---:|---:|---:|
| Hong Kong | 3,668 | 2,595 | 2,426 |
| Singapore | 710 | 1,218 | 1,720 |

Hong Kong has higher measured import-origin concentration than Singapore in all three selected chapters in 2025. The result is descriptive of the recorded import-source distribution; it does not by itself establish which economy would experience greater economic damage from a disruption.

### Largest recorded source categories in 2025

- **Hong Kong:** China accounts for approximately 58.0% of HS 27 imports, 48.0% of HS 84 imports and 44.1% of HS 85 imports.
- **Singapore:** the UAE accounts for approximately 17.6% of HS 27 imports; the United States accounts for approximately 23.6% of HS 84 imports.
- **Singapore HS 85:** the largest category is “Other Asia, nes” at approximately 33.35% of total imports. This is a residual grouping, not an individual country. Among identified countries, China is the largest source at approximately 22.23%.

These examples show why residual partner categories need to be identified explicitly rather than treated as individual countries.

---

## Interactive dashboard

The Streamlit dashboard includes:

- An interactive world choropleth of identifiable import origins.
- Data-driven country colour intensity based on import value, displayed on a logarithmic scale.
- HHI and effective-partner indicators.
- Concentration trends and a Singapore–Hong Kong comparison.
- Leading partner-category rankings.
- A separate residual-category analysis.
- Hypothetical gross-exposure scenarios.
- Methodology and data-limitations notes.

Residual categories are excluded from the map because they cannot reliably be assigned to one country. Original import values and shares remain available in the dashboard tables and hover information.

### Run locally

Clone the repository and enter the project directory:

~~~bash
git clone https://github.com/YashviBhansali/TradeLens.git
cd TradeLens
~~~

Create and activate a virtual environment:

~~~bash
python -m venv .venv
source .venv/bin/activate
~~~

Install the project dependencies:

~~~bash
pip install -r requirements.txt
~~~

Launch the dashboard from the repository root:

~~~bash
streamlit run dashboard/app.py
~~~

---

## Reproduce the analysis

Run the scripts from the repository root, in this order:

~~~bash
python scripts/split_comtrade.py
python scripts/validate_data.py
python scripts/clean_data.py
python scripts/audit_trade_data.py
python scripts/audit_partner_categories.py
python scripts/calculate_metrics.py
python scripts/validate_metrics.py
python scripts/create_visualisations.py
~~~

The scripts separate the source data, validate the six economy–chapter datasets, create clean partner and World-total tables, audit source-data characteristics, calculate concentration and exposure metrics, independently validate the outputs, and generate interactive HTML visualisations.

The original combined source file is retained under data/raw. The analysis scripts do not require an API key.

---

## Repository structure

~~~text
TradeLens/
├── data/
│   ├── raw/
│   │   └── comtrade_combined.csv
│   ├── processed/
│   └── clean/
├── scripts/
│   ├── split_comtrade.py
│   ├── validate_data.py
│   ├── clean_data.py
│   ├── audit_trade_data.py
│   ├── audit_partner_categories.py
│   ├── calculate_metrics.py
│   ├── validate_metrics.py
│   └── create_visualisations.py
├── dashboard/
│   └── app.py
├── figures/
├── .streamlit/
│   └── config.toml
├── .github/
│   └── workflows/
│       └── analysis.yml
├── .gitignore
├── requirements.txt
└── README.md
~~~

---

## Data limitations and interpretation

1. **Import concentration is not a complete measure of resilience.** The analysis does not directly measure inventory buffers, domestic production, supplier substitution, transport-route flexibility, price responses or the wider economic consequences of a disruption.
2. **Residual partner categories are not countries.** Categories such as “Other Asia, nes”, “Other Africa, nes” and “Oceania, nes” can represent broad or unspecified groupings. Their inclusion can materially affect concentration estimates.
3. **The HS classification changes during the study period.** The source uses H5 (HS 2017) for 2020–2021 and H6 (HS 2022) for 2022–2025. Similar chapter descriptions do not prove perfectly identical product composition across the transition.
4. **Reporting and aggregation flags require care.** The source flags are retained for audit purposes. A flag alone is not treated as proof of the provenance or estimation method of an observation.
5. **2025 records are annual records, not proof of finality.** The dataset contains annual 2025 observations (with the annual reference-month marker), but this does not independently establish that all values are final or complete.
6. **The scenario is deliberately static.** It assumes no immediate substitution or inventory buffer and must not be presented as a forecast or realised economic loss.

## Validation

The project contains separate source-data and metrics-validation scripts. The latest recorded independent metrics-validation run passed **23 checks with zero failures**. Re-running the pipeline regenerates the validation report; the result should be checked after any change to the source data or calculation code.

Validation checks internal consistency and arithmetic. It does not remove limitations in the underlying source data.

## Tools

Python · Pandas · NumPy · Plotly · Streamlit · UN Comtrade

## Author

Independent research and data-science project by Yashvi Bhansali.
