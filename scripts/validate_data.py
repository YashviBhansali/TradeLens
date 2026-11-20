from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "processed"
OUTPUT_DIR = ROOT / "data" / "clean"

FILES = [
    "singapore_hs27.csv",
    "singapore_hs84.csv",
    "singapore_hs85.csv",
    "hong_kong_hs27.csv",
    "hong_kong_hs84.csv",
    "hong_kong_hs85.csv",
]
EXPECTED_YEARS = set(range(2020, 2026))
REQUIRED_COLUMNS = {
    "reporterDesc",
    "period",
    "flowCode",
    "partnerCode",
    "partnerDesc",
    "cmdCode",
    "primaryValue",
    "classificationCode",
}


def add_check(rows: list[dict], filename: str, check: str, passed: bool, detail: str = "") -> None:
    rows.append(
        {
            "file": filename,
            "check": check,
            "status": "PASS" if passed else "FAIL",
            "detail": detail,
        }
    )


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    results = []

    for filename in FILES:
        path = DATA_DIR / filename
        if not path.exists():
            add_check(results, filename, "File exists", False, str(path))
            continue

        df = pd.read_csv(path, low_memory=False)
        add_check(results, filename, "File exists", True, f"{len(df):,} rows")

        missing_columns = sorted(REQUIRED_COLUMNS - set(df.columns))
        add_check(
            results,
            filename,
            "Required columns present",
            not missing_columns,
            ", ".join(missing_columns),
        )
        if missing_columns:
            continue

        year_column = "refYear" if "refYear" in df.columns else "period"
        years = pd.to_numeric(df[year_column], errors="coerce")
        observed_years = set(years.dropna().astype(int).unique())
        add_check(
            results,
            filename,
            "Complete annual coverage 2020–2025",
            observed_years == EXPECTED_YEARS,
            f"Observed years: {sorted(observed_years)}",
        )

        expected_hs = filename.rsplit("hs", 1)[1].removesuffix(".csv")
        hs_values = (
            df["cmdCode"].astype("string").str.strip()
            .str.replace(r"\.0$", "", regex=True)
        )
        add_check(
            results,
            filename,
            "Correct HS chapter",
            set(hs_values.dropna().unique()) == {expected_hs},
            f"Observed chapters: {sorted(hs_values.dropna().unique())}",
        )

        flows = df["flowCode"].astype("string").str.upper()
        add_check(
            results,
            filename,
            "Import flow only",
            flows.eq("M").all(),
            f"Observed flow codes: {sorted(flows.dropna().unique())}",
        )

        if "freqCode" in df.columns:
            frequencies = df["freqCode"].astype("string").str.upper()
            annual_only = frequencies.eq("A").all()
        else:
            annual_only = True
        add_check(
            results,
            filename,
            "Annual frequency only",
            annual_only,
            (
                f"Observed frequency codes: "
                f"{sorted(df['freqCode'].dropna().astype(str).unique())}"
                if "freqCode" in df.columns
                else "Frequency field not supplied"
            ),
        )

        missing_values = int(df[list(REQUIRED_COLUMNS)].isna().sum().sum())
        add_check(
            results,
            filename,
            "No missing essential values",
            missing_values == 0,
            f"Missing cells: {missing_values}",
        )

        values = pd.to_numeric(df["primaryValue"], errors="coerce")
        invalid_values = int(values.isna().sum())
        add_check(
            results,
            filename,
            "Import values are numeric",
            invalid_values == 0,
            f"Invalid values: {invalid_values}",
        )

        negative_values = int(values.lt(0).sum())
        add_check(
            results,
            filename,
            "No negative import values",
            negative_values == 0,
            f"Negative values: {negative_values}",
        )

        duplicate_keys = [
            column
            for column in (
                "reporterCode",
                "partnerCode",
                "period",
                "cmdCode",
                "flowCode",
                "classificationCode",
            )
            if column in df.columns
        ]
        duplicate_count = int(df.duplicated(subset=duplicate_keys).sum())
        add_check(
            results,
            filename,
            "No duplicate trade records",
            duplicate_count == 0,
            f"Duplicates: {duplicate_count}",
        )

        if "classificationCode" in df.columns:
            classification_by_year = (
                df.assign(_year=years)
                .groupby("_year")["classificationCode"]
                .nunique()
            )
            consistent = bool(classification_by_year.le(1).all())
            detail = (
                "One classification per year"
                if consistent
                else "Multiple classifications found within a year"
            )
        else:
            consistent = False
            detail = "classificationCode missing"
        add_check(
            results,
            filename,
            "Classification consistent within each year",
            consistent,
            detail,
        )

    report = pd.DataFrame(results)
    report_path = OUTPUT_DIR / "validation_report.csv"
    report.to_csv(report_path, index=False)

    failures = report[report["status"].eq("FAIL")]
    passed = int(report["status"].eq("PASS").sum())

    print("\n" + "=" * 68)
    print("TRADELENS SOURCE-DATA VALIDATION")
    print("=" * 68)
    print(report.to_string(index=False))
    print(f"\nChecks passed: {passed}")
    print(f"Checks failed: {len(failures)}")
    print(f"Report saved to: {report_path}")

    if not failures.empty:
        raise SystemExit("Source-data validation failed.")

    print("\nAll source-data validation checks passed.")


if __name__ == "__main__":
    main()
