"""Clean and combine NSE index-history CSV exports for FundLens."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


INDEX_FILE_NAMES = {
    "NIFTY 50-24-09-2025-to-24-09-2026.csv": "Nifty 50",
    "NIFTY 100-24-09-2025-to-24-09-2026.csv": "Nifty 100",
    "NIFTY MIDCAP 150-24-09-2025-to-24-09-2026.csv": "Nifty Midcap 150",
    "NIFTY SMALLCAP 250-24-09-2025-to-24-09-2026.csv": "Nifty Smallcap 250",
}

RAW_TO_CANONICAL = {
    "Date": "trade_date",
    "Open": "open_index_value",
    "High": "high_index_value",
    "Low": "low_index_value",
    "Close": "close_index_value",
    "Shares Traded": "shares_traded",
    "Turnover (₹ Cr)": "turnover_crore",
}

CANONICAL_COLUMNS = [
    "trade_date",
    "index_name",
    "open_index_value",
    "high_index_value",
    "low_index_value",
    "close_index_value",
    "shares_traded",
    "turnover_crore",
]


def clean_index_csv(path: Path, index_name: str) -> pd.DataFrame:
    """Read one NSE index-history export into FundLens' canonical schema."""
    raw = pd.read_csv(path, encoding="utf-8-sig", dtype=str)
    raw.columns = raw.columns.str.strip()
    missing = set(RAW_TO_CANONICAL).difference(raw.columns)
    if missing:
        raise ValueError(f"Missing required index columns in {path.name}: {sorted(missing)}")

    frame = raw.loc[:, list(RAW_TO_CANONICAL)].rename(columns=RAW_TO_CANONICAL).copy()
    frame["trade_date"] = pd.to_datetime(
        frame["trade_date"].str.strip(), format="%d-%b-%Y", errors="raise"
    )
    for column in RAW_TO_CANONICAL.values():
        if column != "trade_date":
            frame[column] = pd.to_numeric(
                frame[column].str.replace(",", "", regex=False).str.strip(), errors="coerce"
            )
    frame["index_name"] = index_name

    critical = ["trade_date", "close_index_value"]
    if frame[critical].isna().any().any():
        raise ValueError(f"Missing critical values in {path.name}")
    if frame["trade_date"].duplicated().any():
        raise ValueError(f"Duplicate trade dates found in {path.name}")

    frame["source_file"] = path.name
    return frame.loc[:, CANONICAL_COLUMNS + ["source_file"]].sort_values("trade_date").reset_index(drop=True)


def build_index_panel(raw_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return a validated four-index daily panel and per-index quality report."""
    missing_files = [name for name in INDEX_FILE_NAMES if not (raw_dir / name).exists()]
    if missing_files:
        raise FileNotFoundError(f"Missing index-history files: {missing_files}")

    frames = [
        clean_index_csv(raw_dir / file_name, index_name)
        for file_name, index_name in INDEX_FILE_NAMES.items()
    ]
    panel = pd.concat(frames, ignore_index=True)
    report = (
        panel.groupby("index_name", as_index=False)
        .agg(
            observations=("trade_date", "size"),
            first_trade_date=("trade_date", "min"),
            last_trade_date=("trade_date", "max"),
            missing_close=("close_index_value", lambda values: int(values.isna().sum())),
        )
        .sort_values("index_name")
        .reset_index(drop=True)
    )
    report["status"] = "PASS"
    report.loc[report["observations"].ne(248), "status"] = "UNEXPECTED_COVERAGE"
    report.loc[report["missing_close"].gt(0), "status"] = "MISSING_VALUES"

    date_sets = panel.groupby("index_name")["trade_date"].agg(set)
    if len({frozenset(dates) for dates in date_sets}) != 1:
        report["status"] = "DATE_MISMATCH"

    failures = report.loc[report["status"].ne("PASS")]
    if not failures.empty:
        raise ValueError(f"Index panel quality check failed:\n{failures.to_string(index=False)}")
    return panel.sort_values(["index_name", "trade_date"]).reset_index(drop=True), report


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the validated FundLens index-price panel.")
    parser.add_argument("--raw-dir", type=Path, default=Path("data/raw/indices"))
    parser.add_argument("--output", type=Path, default=Path("data/staged/index_prices.csv"))
    parser.add_argument(
        "--quality-report", type=Path, default=Path("data/staged/index_prices_quality_report.csv")
    )
    args = parser.parse_args()

    panel, report = build_index_panel(args.raw_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    panel.to_csv(args.output, index=False)
    report.to_csv(args.quality_report, index=False)
    print(f"Staged {len(panel):,} daily observations for {panel['index_name'].nunique()} indices.")
    print(f"Index panel: {args.output}")
    print(f"Quality report: {args.quality_report}")


if __name__ == "__main__":
    main()
