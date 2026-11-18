
from pathlib import Path
import pandas as pd

# --------------------------------------------------
# PATHS AND SETTINGS
# --------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = ROOT / "data" / "raw" / "comtrade_combined.csv"
OUTPUT_DIR = ROOT / "data" / "processed"

YEARS = list(range(2020, 2026))

REPORTERS = {
    "Singapore": ["Singapore", "SGP", "702"],
    "Hong Kong": [
        "China, Hong Kong SAR",
        "Hong Kong",
        "Hong Kong SAR",
        "HKG",
        "344"
    ],
}

HS_CODES = ["27", "84", "85"]


# --------------------------------------------------
# FIND COLUMNS
# --------------------------------------------------

def find_column(df, candidates):
    lookup = {str(col).lower(): col for col in df.columns}

    for candidate in candidates:
        if candidate.lower() in lookup:
            return lookup[candidate.lower()]

    raise ValueError(
        f"Could not find any of {candidates}.\n"
        f"Available columns: {list(df.columns)}"
    )


# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------

if not INPUT_FILE.exists():
    raise FileNotFoundError(
        f"Input file not found: {INPUT_FILE}"
    )

df = pd.read_csv(INPUT_FILE, low_memory=False)

print("\nOriginal dataset loaded.")
print("Rows:", len(df))
print("Columns:", list(df.columns))


# --------------------------------------------------
# IDENTIFY RELEVANT COLUMNS
# --------------------------------------------------

reporter_col = find_column(
    df,
    ["reporterDesc", "reporter", "reporterISO", "reporterCode"]
)

year_col = find_column(
    df,
    ["period", "year"]
)

hs_col = find_column(
    df,
    ["cmdCode", "cmd_code", "commodityCode", "commodity_code"]
)


# --------------------------------------------------
# STANDARDISE VALUES
# --------------------------------------------------

df[reporter_col] = df[reporter_col].astype(str).str.strip()

df["_year"] = pd.to_numeric(
    df[year_col], errors="coerce"
)

# Preserve leading zeroes and remove decimal suffixes.
df["_hs"] = (
    df[hs_col]
    .astype(str)
    .str.strip()
    .str.replace(r"\.0$", "", regex=True)
)

df = df[df["_year"].isin(YEARS)].copy()
df["_year"] = df["_year"].astype(int)


# --------------------------------------------------
# SEPARATE SIX DATASETS
# --------------------------------------------------

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

summary = []

for economy, aliases in REPORTERS.items():

    reporter_mask = (
        df[reporter_col]
        .astype(str)
        .str.strip()
        .str.casefold()
        .isin([x.casefold() for x in aliases])
    )

    economy_df = df[reporter_mask].copy()

    if economy_df.empty:
        print(f"\nWARNING: No records found for {economy}.")
        continue

    for hs in HS_CODES:

        # Select the exact two-digit HS chapter.
        # This avoids accidentally mixing chapter totals
        # with their individual subheadings.
        subset = economy_df[
            economy_df["_hs"] == hs
        ].copy()

        filename = (
            f"{economy.lower().replace(' ', '_')}"
            f"_hs{hs}.csv"
        )

        output_path = OUTPUT_DIR / filename

        if subset.empty:
            print(
                f"WARNING: No exact HS {hs} records "
                f"found for {economy}."
            )
            continue

        # Remove internal helper columns.
        subset = subset.drop(
            columns=["_year", "_hs"]
        )

        subset.to_csv(output_path, index=False)

        summary.append({
            "Economy": economy,
            "HS Chapter": hs,
            "Records": len(subset),
            "Years": sorted(
                pd.to_numeric(
                    subset[year_col], errors="coerce"
                ).dropna().unique().tolist()
            ),
            "Output": filename
        })

        print(
            f"Saved {filename}: {len(subset)} records"
        )


# --------------------------------------------------
# SUMMARY
# --------------------------------------------------

print("\n" + "=" * 55)
print("DATA SEPARATION SUMMARY")
print("=" * 55)

if summary:
    summary_df = pd.DataFrame(summary)
    print(summary_df.to_string(index=False))

    summary_df.to_csv(
        OUTPUT_DIR / "separation_summary.csv",
        index=False
    )
else:
    print("No datasets were created.")

print("\nFinished.")
