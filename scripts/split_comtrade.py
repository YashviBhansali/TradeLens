from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
INPUT_FILE = ROOT / "data" / "raw" / "comtrade_combined.csv"
OUTPUT_DIR = ROOT / "data" / "processed"

YEARS = set(range(2020, 2026))
HS_CODES = ("27", "84", "85")

REPORTERS = {
    "Singapore": {"singapore", "sgp", "702"},
    "Hong Kong": {
        "china, hong kong sar",
        "hong kong",
        "hong kong sar",
        "hkg",
        "344",
    },
}


def find_column(df: pd.DataFrame, candidates: tuple[str, ...]) -> str:
    lookup = {str(column).casefold(): column for column in df.columns}
    for candidate in candidates:
        if candidate.casefold() in lookup:
            return lookup[candidate.casefold()]
    raise ValueError(
        f"Could not find any of {candidates}. "
        f"Available columns: {list(df.columns)}"
    )


def normalise_code(series: pd.Series) -> pd.Series:
    return (
        series.astype("string")
        .str.strip()
        .str.replace(r"\.0$", "", regex=True)
    )


def main() -> None:
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Input file not found: {INPUT_FILE}")

    df = pd.read_csv(INPUT_FILE, low_memory=False)
    print(f"Loaded {len(df):,} source records.")

    reporter_col = find_column(
        df, ("reporterDesc", "reporterISO", "reporterCode")
    )
    year_col = find_column(df, ("refYear", "period", "year"))
    hs_col = find_column(
        df, ("cmdCode", "cmd_code", "commodityCode", "commodity_code")
    )

    df["_reporter"] = df[reporter_col].astype("string").str.strip().str.casefold()
    df["_year"] = pd.to_numeric(df[year_col], errors="coerce")
    df["_hs"] = normalise_code(df[hs_col])

    # This project uses annual import records only.
    if "freqCode" in df.columns:
        df = df[df["freqCode"].astype("string").str.upper().eq("A")].copy()

    if "flowCode" in df.columns:
        df = df[df["flowCode"].astype("string").str.upper().eq("M")].copy()

    df = df[df["_year"].isin(YEARS)].copy()
    df["_year"] = df["_year"].astype(int)

    if df.empty:
        raise ValueError("No annual import records were found for 2020–2025.")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    summary = []
    expected_outputs = []

    for economy, aliases in REPORTERS.items():
        economy_rows = df[df["_reporter"].isin(aliases)].copy()
        if economy_rows.empty:
            raise ValueError(f"No source records found for {economy}.")

        for hs_code in HS_CODES:
            subset = economy_rows[economy_rows["_hs"].eq(hs_code)].copy()
            if subset.empty:
                raise ValueError(f"No HS {hs_code} records found for {economy}.")

            observed_years = set(subset["_year"].unique())
            if observed_years != YEARS:
                missing = sorted(YEARS - observed_years)
                extra = sorted(observed_years - YEARS)
                raise ValueError(
                    f"{economy} HS {hs_code} has incorrect year coverage. "
                    f"Missing={missing}; unexpected={extra}"
                )

            filename = f"{economy.lower().replace(' ', '_')}_hs{hs_code}.csv"
            output_path = OUTPUT_DIR / filename
            subset = subset.drop(columns=["_reporter", "_year", "_hs"])
            subset.to_csv(output_path, index=False)

            expected_outputs.append(filename)
            summary.append(
                {
                    "economy": economy,
                    "hs_code": hs_code,
                    "records": len(subset),
                    "years": "2020–2025",
                    "output": filename,
                }
            )
            print(f"Saved {filename}: {len(subset):,} records")

    if len(expected_outputs) != 6:
        raise RuntimeError(
            f"Expected six processed files; created {len(expected_outputs)}."
        )

    summary_df = pd.DataFrame(summary)
    summary_df.to_csv(OUTPUT_DIR / "separation_summary.csv", index=False)

    print("\nData separation completed.")
    print(summary_df.to_string(index=False))


if __name__ == "__main__":
    main()
