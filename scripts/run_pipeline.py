"""Run the complete TradeLens data and visualisation workflow."""

from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"

STEPS = [
    "split_comtrade.py",
    "validate_data.py",
    "clean_data.py",
    "audit_trade_data.py",
    "audit_partner_categories.py",
    "calculate_metrics.py",
    "validate_metrics.py",
    "create_visualisations.py",
]


def main() -> None:
    for step in STEPS:
        script = SCRIPTS / step
        print("\n" + "=" * 72, flush=True)
        print(f"TRADELENS PIPELINE: {step}", flush=True)
        print("=" * 72, flush=True)
        subprocess.run(
            [sys.executable, str(script)],
            cwd=ROOT,
            check=True,
        )

    print("\nTradeLens pipeline completed successfully.", flush=True)


if __name__ == "__main__":
    main()
