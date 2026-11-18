
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

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

audit_results = []

for filename in FILES:

    path = DATA_DIR / filename

    print("\n" + "=" * 65)
    print(f"VALIDATING: {filename}")
    print("=" * 65)

    if not path.exists():
        print("FILE NOT FOUND")
        continue

    df = pd.read_csv(path, low_memory=False)

    # Convert numeric fields safely
    df["period"] = pd.to_numeric(
        df["period"], errors="coerce"
    )

    df["primaryValue"] = pd.to_numeric(
        df["primaryValue"], errors="coerce"
    )

    df["partnerCode"] = pd.to_numeric(
        df["partnerCode"], errors="coerce"
    )

    print("Records:", len(df))

    # 1. Year coverage
    print("\nYear coverage:")
    print(df["period"].value_counts().sort_index())

    # 2. Trade flow
    print("\nTrade flow:")
    print(df["flowDesc"].value_counts(dropna=False))
    print("Flow codes:", df["flowCode"].unique())

    # 3. Commodity classification
    print("\nCommodity codes:")
    print(df["cmdCode"].value_counts().head(10))

    print("Aggregation levels:")
    print(df["aggrLevel"].value_counts(dropna=False))

    print("Is aggregate:")
    print(df["isAggregate"].value_counts(dropna=False))

    print("Is leaf:")
    print(df["isLeaf"].value_counts(dropna=False))

    # 4. Trading partners
    print("\nNumber of unique partners:")
    print(df["partnerCode"].nunique())

    print("World / aggregate partner records:")
    world = df[
        df["partnerDesc"]
        .astype(str)
        .str.contains("world", case=False, na=False)
    ]

    print(len(world))
    print(world["partnerDesc"].value_counts())

    # 5. Missing values
    print("\nMissing values:")
    print(
        df[
            ["period", "partnerCode", "partnerDesc",
             "cmdCode", "primaryValue"]
        ].isna().sum()
    )

    # 6. Duplicate records
    key_columns = [
        "reporterCode",
        "partnerCode",
        "period",
        "cmdCode",
        "flowCode",
        "classificationCode",
    ]

    duplicate_count = df.duplicated(
        subset=key_columns
    ).sum()

    print("\nDuplicate records:", duplicate_count)

    # 7. Trade value checks
    print("\nTrade value:")
    print(df["primaryValue"].describe())

    negative_values = (df["primaryValue"] < 0).sum()
    print("Negative trade values:", negative_values)

    # 8. Save audit summary
    audit_results.append({
        "file": filename,
        "records": len(df),
        "years": ", ".join(
            map(
                str,
                sorted(
                    df["period"].dropna().unique()
                )
            )
        ),
        "unique_partners": df["partnerCode"].nunique(),
        "trade_flows": ", ".join(
            df["flowCode"].dropna().astype(str).unique()
        ),
        "duplicate_records": duplicate_count,
        "missing_trade_values": df["primaryValue"].isna().sum(),
        "world_records": len(world),
        "negative_values": negative_values,
    })


# Save audit report
audit_df = pd.DataFrame(audit_results)

audit_df.to_csv(
    OUTPUT_DIR / "validation_report.csv",
    index=False
)

print("\n" + "=" * 65)
print("VALIDATION FINISHED")
print("=" * 65)

print(audit_df.to_string(index=False))

print("\nReport saved to:")
print(OUTPUT_DIR / "validation_report.csv")
