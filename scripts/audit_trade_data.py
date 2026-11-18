
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
FILE = ROOT / "data" / "raw" / "comtrade_combined.csv"

df = pd.read_csv(FILE, low_memory=False)

print("\n" + "=" * 65)
print("TRADELENS DATA COMPLETENESS AND PARTNER AUDIT")
print("=" * 65)

# 1. Frequency codes
print("\n1. FREQUENCY CODES")
print(df["freqCode"].value_counts(dropna=False))

# 2. Reporting periods in 2025
print("\n2. 2025 REPORTING PERIODS")
data_2025 = df[df["refYear"] == 2025]

print("Records:", len(data_2025))
print("\nReference months:")
print(data_2025["refMonth"].value_counts(dropna=False).sort_index())

# 3. Reporting periods by economy and HS chapter
print("\n3. 2025 PERIOD COVERAGE")
print(
    data_2025.groupby(
        ["reporterDesc", "cmdCode", "freqCode"]
    )["refMonth"]
    .nunique()
    .to_string()
)

# 4. Special or residual partner categories
print("\n4. SPECIAL PARTNER CATEGORIES")

special = df[
    df["partnerDesc"].astype(str).str.contains(
        r"other|not elsewhere|areas|free zone|bunker|special",
        case=False,
        na=False
    )
]

print(
    special[["partnerCode", "partnerDesc"]]
    .drop_duplicates()
    .sort_values("partnerDesc")
    .to_string(index=False)
)

# 5. Classification and reporting status
print("\n5. CLASSIFICATION AND REPORTING STATUS")
for column in [
    "classificationCode",
    "isReported",
    "isOriginalClassification",
]:
    if column in df.columns:
        print(f"\n{column}:")
        print(df[column].value_counts(dropna=False).to_string())


# 6. Classification by economy, year and HS chapter
print("\n6. CLASSIFICATION BREAKDOWN")

classification_audit = (
    df.groupby(
        ["reporterDesc", "refYear", "cmdCode", "classificationCode"],
        dropna=False
    )
    .size()
    .reset_index(name="records")
)

print(classification_audit.to_string(index=False))

# 7. Reporting status by economy and year
print("\n7. ISREPORTED BY ECONOMY AND YEAR")

reported_audit = (
    df.groupby(
        ["reporterDesc", "refYear", "isReported"],
        dropna=False
    )
    .size()
    .reset_index(name="records")
)

print(reported_audit.to_string(index=False))

# 8. Original classification status by economy and year
print("\n8. ORIGINAL CLASSIFICATION STATUS")

original_audit = (
    df.groupby(
        ["reporterDesc", "refYear", "isOriginalClassification"],
        dropna=False
    )
    .size()
    .reset_index(name="records")
)

print(original_audit.to_string(index=False))


print("\nAudit completed.")
