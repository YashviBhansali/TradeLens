from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "processed"
OUTPUT_DIR = ROOT / "data" / "clean"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

EXPECTED_FILES = {
    "singapore_hs27.csv": ("Singapore", "27"),
    "singapore_hs84.csv": ("Singapore", "84"),
    "singapore_hs85.csv": ("Singapore", "85"),
    "hong_kong_hs27.csv": ("China, Hong Kong SAR", "27"),
    "hong_kong_hs84.csv": ("China, Hong Kong SAR", "84"),
    "hong_kong_hs85.csv": ("China, Hong Kong SAR", "85"),
}
EXPECTED_YEARS = set(range(2020, 2026))
REQUIRED_COLUMNS = {
    "period", "freqCode", "flowCode", "reporterDesc",
    "partnerCode", "partnerDesc", "cmdCode", "primaryValue",
    "classificationCode", "aggrLevel", "isAggregate", "isLeaf",
}

checks = []


def record(filename, check, passed, detail=""):
    checks.append({
        "file": filename,
        "check": check,
        "status": "PASS" if passed else "FAIL",
        "detail": str(detail),
    })


def normalise_codes(series):
    return (
        series.astype(str)
        .str.strip()
        .str.replace(r"\.0$", "", regex=True)
    )


def as_true(series):
    return series.astype(str).str.strip().str.casefold().isin(
        {"true", "1", "yes", "y"}
    )


def as_false(series):
    return series.astype(str).str.strip().str.casefold().isin(
        {"false", "0", "no", "n"}
    )


for filename, (expected_reporter, expected_hs) in EXPECTED_FILES.items():
    path = DATA_DIR / filename

    if not path.exists():
        record(filename, "File exists", False, path)
        continue

    df = pd.read_csv(path, low_memory=False)
    record(filename, "File is non-empty", not df.empty, f"{len(df)} rows")

    missing_columns = sorted(REQUIRED_COLUMNS - set(df.columns))
    record(
        filename,
        "Required columns present",
        not missing_columns,
        ", ".join(missing_columns) if missing_columns else "All required columns present",
    )
    if missing_columns:
        continue

    years = pd.to_numeric(df["period"], errors="coerce")
    year_set = set(years.dropna().astype(int).unique())
    record(
        filename,
        "Complete 2020–2025 year coverage",
        year_set == EXPECTED_YEARS,
        f"Found years: {sorted(year_set)}",
    )

    record(
        filename,
        "Annual frequency only",
        df["freqCode"].astype(str).str.strip().eq("A").all(),
        f"Frequency codes: {sorted(df['freqCode'].dropna().astype(str).unique())}",
    )

    record(
        filename,
        "Import flow only",
        df["flowCode"].astype(str).str.strip().eq("M").all(),
        f"Flow codes: {sorted(df['flowCode'].dropna().astype(str).unique())}",
    )

    reporter_values = set(df["reporterDesc"].dropna().astype(str).str.strip())
    record(
        filename,
        "Expected reporting economy",
        reporter_values == {expected_reporter},
        f"Found: {sorted(reporter_values)}",
    )

    hs_values = set(normalise_codes(df["cmdCode"]).dropna())
    record(
        filename,
        "Exact HS chapter",
        hs_values == {expected_hs},
        f"Found: {sorted(hs_values)}",
    )

    essential = ["period", "partnerCode", "partnerDesc", "cmdCode", "primaryValue"]
    missing_essential = int(df[essential].isna().any(axis=1).sum())
    record(
        filename,
        "No missing essential values",
        missing_essential == 0,
        f"Rows with missing essential values: {missing_essential}",
    )

    values = pd.to_numeric(df["primaryValue"], errors="coerce")
    invalid_values = int(values.isna().sum())
    negative_values = int(values.lt(0).sum())
    record(
        filename,
        "Import values numeric and non-negative",
        invalid_values == 0 and negative_values == 0,
        f"Invalid: {invalid_values}; negative: {negative_values}",
    )

    duplicate_keys = [
        "reporterCode", "partnerCode", "period",
        "cmdCode", "flowCode", "classificationCode",
    ]
    missing_duplicate_keys = sorted(set(duplicate_keys) - set(df.columns))
    if missing_duplicate_keys:
        record(
            filename,
            "Duplicate-key columns present",
            False,
            ", ".join(missing_duplicate_keys),
        )
    else:
        duplicate_count = int(
            df.assign(
                partnerCode=normalise_codes(df["partnerCode"]),
                cmdCode=normalise_codes(df["cmdCode"]),
            ).duplicated(subset=duplicate_keys).sum()
        )
        record(
            filename,
            "No duplicate trade records",
            duplicate_count == 0,
            f"Duplicates: {duplicate_count}",
        )

    aggregation_level = pd.to_numeric(df["aggrLevel"], errors="coerce")
    record(
        filename,
        "Chapter aggregation level is 2",
        aggregation_level.eq(2).all(),
        f"Levels: {sorted(aggregation_level.dropna().unique().tolist())}",
    )

    record(
        filename,
        "All records flagged as aggregate",
        as_true(df["isAggregate"]).all(),
        f"Values: {sorted(df['isAggregate'].astype(str).unique())}",
    )

    record(
        filename,
        "No records flagged as leaf",
        as_false(df["isLeaf"]).all(),
        f"Values: {sorted(df['isLeaf'].astype(str).unique())}",
    )

    classifications = df["classificationCode"].astype(str).str.strip()
    expected_classifications = years.map(
        lambda year: "H5" if year <= 2021 else "H6"
    )
    record(
        filename,
        "Expected HS classification by year",
        classifications.eq(expected_classifications).all(),
        f"Found: {sorted(classifications.unique())}",
    )

    world_mask = (
        df["partnerDesc"].astype(str).str.strip().str.casefold().eq("world")
        | normalise_codes(df["partnerCode"]).eq("0")
    )
    world_counts = (
        pd.DataFrame({"year": years[world_mask]})
        .groupby("year")
        .size()
    )
    world_ok = (
        set(world_counts.index.astype(int)) == EXPECTED_YEARS
        and world_counts.eq(1).all()
    )
    record(
        filename,
        "One World benchmark record per year",
        world_ok,
        f"Counts: {world_counts.to_dict()}",
    )

    if "refMonth" in df.columns:
        ref_month = pd.to_numeric(df["refMonth"], errors="coerce")
        rows_2025 = years.eq(2025)
        annual_marker_ok = ref_month[rows_2025].eq(52).all()
        record(
            filename,
            "2025 annual reference marker is 52",
            bool(rows_2025.any() and annual_marker_ok),
            f"2025 reference months: {sorted(ref_month[rows_2025].dropna().unique().tolist())}",
        )

report = pd.DataFrame(checks)
report_path = OUTPUT_DIR / "validation_report.csv"
report.to_csv(report_path, index=False)

passed = int(report["status"].eq("PASS").sum()) if not report.empty else 0
failed = int(report["status"].eq("FAIL").sum()) if not report.empty else 0

print("\n" + "=" * 70)
print("TRADELENS SOURCE-DATA VALIDATION")
print("=" * 70)
print(report.to_string(index=False))
print("\n" + "-" * 70)
print(f"Checks passed: {passed}")
print(f"Checks failed: {failed}")
print(f"Report saved: {report_path}")
print("-" * 70)

if failed:
    raise SystemExit("SOURCE-DATA VALIDATION FAILED. Review the report before continuing.")

print("\nALL SOURCE-DATA VALIDATION CHECKS PASSED.")
