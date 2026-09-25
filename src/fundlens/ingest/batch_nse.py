"""Build the FundLens daily stock panel from a directory of NSE CSV exports."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from fundlens.ingest.nse import clean_nse_csv


CRITICAL_COLUMNS = [
    "close_price",
    "volume",
    "turnover",
    "trades",
    "delivery_quantity",
    "delivery_pct",
]


def build_daily_panel(raw_dir: Path, universe_path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return a validated daily panel and a per-stock quality report.

    Source files not represented in the locked universe are ignored. This keeps
    previously rejected downloads available for audit without contaminating the
    current analysis universe.
    """
    universe = pd.read_csv(universe_path)
    required_metadata = [
        "symbol",
        "company",
        "sector",
        "cap_category",
        "benchmark",
        "selection_date",
    ]
    missing_metadata = set(required_metadata).difference(universe.columns)
    if missing_metadata:
        raise ValueError(f"Universe file is missing columns: {sorted(missing_metadata)}")
    if universe["symbol"].duplicated().any():
        raise ValueError("Universe file contains duplicate symbols")

    files = sorted(raw_dir.glob("*.csv"))
    if not files:
        raise FileNotFoundError(f"No NSE CSV files found in {raw_dir}")

    frames = [clean_nse_csv(path) for path in files]
    all_observations = pd.concat(frames, ignore_index=True)
    panel = all_observations.loc[
        all_observations["symbol"].isin(universe["symbol"])
    ].copy()
    panel = panel.merge(universe[required_metadata], on="symbol", how="left", validate="many_to_one")

    if panel.duplicated(["symbol", "trade_date"]).any():
        duplicated = panel.loc[panel.duplicated(["symbol", "trade_date"], keep=False)]
        raise ValueError(
            "Duplicate stock/date observations after combining raw files: "
            f"{duplicated[['symbol', 'trade_date']].head().to_dict('records')}"
        )

    report = (
        panel.groupby("symbol", as_index=False)
        .agg(
            observations=("trade_date", "size"),
            first_trade_date=("trade_date", "min"),
            last_trade_date=("trade_date", "max"),
            missing_critical=("close_price", lambda values: int(values.isna().sum())),
        )
        .merge(universe[["symbol", "cap_category"]], on="symbol", how="right", validate="one_to_one")
    )
    critical_missing = panel[CRITICAL_COLUMNS].isna().sum(axis=1)
    critical_by_symbol = critical_missing.groupby(panel["symbol"]).sum().rename("missing_critical")
    report = report.drop(columns="missing_critical").merge(
        critical_by_symbol, on="symbol", how="left", validate="one_to_one"
    )
    report["missing_critical"] = report["missing_critical"].fillna(len(CRITICAL_COLUMNS)).astype(int)
    report["status"] = "PASS"
    report.loc[report["observations"].isna(), "status"] = "MISSING_SOURCE"
    report.loc[report["observations"].fillna(0).ne(248), "status"] = "UNEXPECTED_COVERAGE"
    report.loc[report["missing_critical"].gt(0), "status"] = "MISSING_VALUES"

    failures = report.loc[report["status"].ne("PASS")]
    if not failures.empty:
        raise ValueError(f"Panel quality check failed:\n{failures.to_string(index=False)}")

    panel = panel.sort_values(["symbol", "trade_date"]).reset_index(drop=True)
    report = report.sort_values("symbol").reset_index(drop=True)
    return panel, report


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the validated FundLens NSE daily panel.")
    parser.add_argument("--raw-dir", type=Path, default=Path("data/raw"))
    parser.add_argument("--universe", type=Path, default=Path("config/stock_universe.csv"))
    parser.add_argument("--output", type=Path, default=Path("data/staged/daily_prices.csv"))
    parser.add_argument(
        "--quality-report", type=Path, default=Path("data/staged/daily_prices_quality_report.csv")
    )
    args = parser.parse_args()

    panel, report = build_daily_panel(args.raw_dir, args.universe)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.quality_report.parent.mkdir(parents=True, exist_ok=True)
    panel.to_csv(args.output, index=False)
    report.to_csv(args.quality_report, index=False)
    print(f"Staged {len(panel):,} daily observations for {panel['symbol'].nunique()} stocks.")
    print(f"Daily panel: {args.output}")
    print(f"Quality report: {args.quality_report}")


if __name__ == "__main__":
    main()
