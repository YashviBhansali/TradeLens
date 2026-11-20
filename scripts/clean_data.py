from pathlib import Path
import math

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
INPUT_DIR = ROOT / "data" / "processed"
OUTPUT_DIR = ROOT / "data" / "clean"

FILES = [
    "singapore_hs27.csv",
    "singapore_hs84.csv",
    "singapore_hs85.csv",
    "hong_kong_hs27.csv",
    "hong_kong_hs84.csv",
    "hong_kong_hs85.csv",
]
PRODUCTS = {
    "27": "Mineral fuels and oils",
    "84": "Machinery and mechanical appliances",
    "85": "Electrical machinery and equipment",
}
GROUP_COLUMNS = ["economy", "hs_code", "year"]
OUTPUT_COLUMNS = [
    "economy",
    "year",
    "hs_code",
    "product",
    "partner_code",
    "partner",
    "import_value_usd",
    "classificationCode",
    "isReported",
    "isAggregate",
]


def normalise_code(series: pd.Series) -> pd.Series:
    return (
        series.astype("string")
        .str.strip()
        .str.replace(r"\.0$", "", regex=True)
    )


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    partner_frames = []
    world_frames = []

    for filename in FILES:
        path = INPUT_DIR / filename
        if not path.exists():
            raise FileNotFoundError(
                f"Required processed file is missing: {path}"
            )

        df = pd.read_csv(path, low_memory=False)
        required = {
            "period",
            "cmdCode",
            "primaryValue",
            "partnerCode",
            "partnerDesc",
            "flowCode",
            "classificationCode",
            "isReported",
            "isAggregate",
        }
        missing = sorted(required - set(df.columns))
        if missing:
            raise ValueError(f"{filename} is missing columns: {missing}")

        economy = "Singapore" if filename.startswith("singapore") else "Hong Kong"
        year_source = df["refYear"] if "refYear" in df.columns else df["period"]

        df["year"] = pd.to_numeric(year_source, errors="coerce")
        df["hs_code"] = normalise_code(df["cmdCode"])
        df["import_value_usd"] = pd.to_numeric(
            df["primaryValue"], errors="coerce"
        )
        df["partner_code"] = normalise_code(df["partnerCode"])
        df["partner"] = df["partnerDesc"].astype("string").str.strip()
        df["economy"] = economy
        df["product"] = df["hs_code"].map(PRODUCTS)

        if not df["flowCode"].astype("string").str.upper().eq("M").all():
            raise ValueError(f"Non-import records found in {filename}.")
        if df[["year", "hs_code", "partner_code", "partner", "import_value_usd"]].isna().any().any():
            raise ValueError(f"Missing essential trade values in {filename}.")
        if df["import_value_usd"].lt(0).any():
            raise ValueError(f"Negative import values found in {filename}.")
        if df["product"].isna().any():
            raise ValueError(f"Unexpected HS chapter found in {filename}.")

        df["year"] = df["year"].astype(int)
        is_world = (
            df["partner"].str.casefold().eq("world")
            | df["partner_code"].eq("0")
        )

        partner_frames.append(df.loc[~is_world, OUTPUT_COLUMNS].copy())
        world_frames.append(df.loc[is_world, OUTPUT_COLUMNS].copy())

    partners = pd.concat(partner_frames, ignore_index=True)
    world = pd.concat(world_frames, ignore_index=True)

    duplicate_keys = [
        "economy",
        "year",
        "hs_code",
        "partner_code",
        "classificationCode",
    ]
    duplicate_count = int(partners.duplicated(duplicate_keys).sum())
    if duplicate_count:
        raise ValueError(
            f"Found {duplicate_count} duplicate partner records. "
            "Resolve duplicates before analysis."
        )

    world_counts = world.groupby(GROUP_COLUMNS).size()
    if world_counts.empty or not world_counts.eq(1).all():
        raise ValueError(
            "Expected exactly one World benchmark record per economy, "
            "year and HS chapter."
        )

    partners = partners.sort_values(
        ["economy", "hs_code", "year", "partner"]
    ).reset_index(drop=True)
    world = world.sort_values(
        ["economy", "hs_code", "year"]
    ).reset_index(drop=True)

    partner_summary = (
        partners.groupby(GROUP_COLUMNS)
        .agg(
            partner_records=("partner", "size"),
            unique_partners=("partner_code", "nunique"),
            sum_partner_imports_usd=("import_value_usd", "sum"),
        )
        .reset_index()
    )
    world_summary = (
        world.groupby(GROUP_COLUMNS)["import_value_usd"]
        .sum()
        .reset_index(name="world_imports_usd")
    )
    summary = partner_summary.merge(
        world_summary,
        on=GROUP_COLUMNS,
        how="outer",
        validate="one_to_one",
        indicator=True,
    )

    if not summary["_merge"].eq("both").all():
        raise ValueError(
            "Partner totals and World benchmark groups do not match."
        )
    summary = summary.drop(columns="_merge")
    summary["difference_usd"] = (
        summary["world_imports_usd"] - summary["sum_partner_imports_usd"]
    )
    summary["partner_coverage_pct"] = (
        summary["sum_partner_imports_usd"]
        / summary["world_imports_usd"]
        * 100
    )

    tolerances = summary.apply(
        lambda row: max(1.0, abs(row["world_imports_usd"]) * 1e-8),
        axis=1,
    )
    if not summary["difference_usd"].abs().le(tolerances).all():
        raise ValueError(
            "Partner import values do not reconcile with World totals.\n"
            + summary.to_string(index=False)
        )

    partners.to_csv(OUTPUT_DIR / "trade_data.csv", index=False)
    world.to_csv(OUTPUT_DIR / "world_totals.csv", index=False)
    summary.to_csv(OUTPUT_DIR / "trade_summary.csv", index=False)

    print("\n" + "=" * 68)
    print("TRADELENS CLEANING AND RECONCILIATION")
    print("=" * 68)
    print(f"Individual partner records: {len(partners):,}")
    print(f"World benchmark records: {len(world):,}")
    print(f"Groups reconciled: {len(summary)}")
    print(f"Maximum absolute difference (USD): {summary['difference_usd'].abs().max():,.6f}")
    print("\nPartner coverage:")
    print(summary.to_string(index=False))
    print("\nClean data saved to data/clean/.")


if __name__ == "__main__":
    main()
