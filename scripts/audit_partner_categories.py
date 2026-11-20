"""Audit residual partner groupings using cleaned partner-level imports."""

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
INPUT_FILE = ROOT / "data" / "clean" / "trade_data.csv"
OUTPUT_FILE = ROOT / "data" / "clean" / "residual_partner_audit.csv"
RESIDUAL_PATTERN = r"\bnes\b|^Other\s"

OUTPUT_COLUMNS = [
    "economy",
    "year",
    "hs_code",
    "product",
    "partner_code",
    "partner",
    "residual_imports_usd",
    "total_partner_imports_usd",
    "individual_residual_share_pct",
    "total_residual_share_pct",
    "classificationCode",
]


def main() -> None:
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"{INPUT_FILE} not found. Run clean_data.py first."
        )

    df = pd.read_csv(INPUT_FILE, low_memory=False)
    df["import_value_usd"] = pd.to_numeric(
        df["import_value_usd"], errors="raise"
    )
    df["is_residual"] = df["partner"].astype("string").str.contains(
        RESIDUAL_PATTERN,
        case=False,
        regex=True,
        na=False,
    )

    group_columns = ["economy", "year", "hs_code"]
    totals = (
        df.groupby(group_columns)["import_value_usd"]
        .sum()
        .rename("total_partner_imports_usd")
    )
    residual = df.loc[df["is_residual"]].copy()
    residual_totals = (
        residual.groupby(group_columns)["import_value_usd"]
        .sum()
        .rename("_total_residual_imports_usd")
    )

    if residual.empty:
        result = pd.DataFrame(columns=OUTPUT_COLUMNS)
    else:
        result = residual.merge(
            totals.reset_index(),
            on=group_columns,
            how="left",
            validate="many_to_one",
        ).merge(
            residual_totals.reset_index(),
            on=group_columns,
            how="left",
            validate="many_to_one",
        )
        result["individual_residual_share_pct"] = (
            result["import_value_usd"]
            / result["total_partner_imports_usd"]
            * 100
        )
        result["total_residual_share_pct"] = (
            result["_total_residual_imports_usd"]
            / result["total_partner_imports_usd"]
            * 100
        )
        result = result.rename(
            columns={"import_value_usd": "residual_imports_usd"}
        )[OUTPUT_COLUMNS]

    result = result.sort_values(
        ["economy", "hs_code", "year", "partner"]
    )
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(OUTPUT_FILE, index=False)

    print("\n" + "=" * 68)
    print("TRADELENS RESIDUAL PARTNER AUDIT")
    print("=" * 68)
    print(f"Residual partner records: {len(result):,}")
    if not result.empty:
        print(
            result[
                [
                    "economy",
                    "year",
                    "hs_code",
                    "partner",
                    "individual_residual_share_pct",
                    "total_residual_share_pct",
                ]
            ].to_string(index=False)
        )
    print(f"\nSaved: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
