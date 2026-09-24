"""Clean NSE security-wise daily CSV exports into the FundLens canonical schema."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


RAW_TO_CANONICAL = {
    "Symbol": "symbol",
    "Series": "series",
    "Date": "trade_date",
    "Prev Close": "previous_close",
    "Open Price": "open_price",
    "High Price": "high_price",
    "Low Price": "low_price",
    "Last Price": "last_price",
    "Close Price": "close_price",
    "Average Price": "vwap",
    "Total Traded Quantity": "volume",
    "Turnover ₹": "turnover",
    "No. of Trades": "trades",
    "Deliverable Qty": "delivery_quantity",
    "% Dly Qt to Traded Qty": "delivery_pct",
}

NUMERIC_COLUMNS = [
    "previous_close",
    "open_price",
    "high_price",
    "low_price",
    "last_price",
    "close_price",
    "vwap",
    "volume",
    "turnover",
    "trades",
    "delivery_quantity",
    "delivery_pct",
]

CANONICAL_COLUMNS = [
    "trade_date",
    "symbol",
    "series",
    "previous_close",
    "open_price",
    "high_price",
    "low_price",
    "last_price",
    "close_price",
    "vwap",
    "volume",
    "turnover",
    "trades",
    "delivery_quantity",
    "delivery_pct",
]


def clean_nse_csv(path: Path) -> pd.DataFrame:
    """Read one NSE CSV export and return validated EQ observations.

    The NSE export uses a UTF-8 BOM, padded headers, reverse-chronological
    rows, and Indian digit-grouping commas. All are normalised here.
    """
    raw = pd.read_csv(path, encoding="utf-8-sig", dtype=str)
    raw.columns = raw.columns.str.strip()

    missing = set(RAW_TO_CANONICAL).difference(raw.columns)
    if missing:
        raise ValueError(f"Missing required NSE columns in {path.name}: {sorted(missing)}")

    frame = raw.loc[:, list(RAW_TO_CANONICAL)].rename(columns=RAW_TO_CANONICAL).copy()
    frame["symbol"] = frame["symbol"].str.strip().str.upper()
    frame["series"] = frame["series"].str.strip().str.upper()
    frame = frame.loc[frame["series"].eq("EQ")].copy()

    if frame.empty:
        raise ValueError(f"No EQ observations found in {path.name}")

    frame["trade_date"] = pd.to_datetime(
        frame["trade_date"].str.strip(), format="%d-%b-%Y", errors="raise"
    )
    for column in NUMERIC_COLUMNS:
        frame[column] = pd.to_numeric(
            frame[column].str.replace(",", "", regex=False).str.strip(), errors="coerce"
        )

    critical = ["symbol", "trade_date", "close_price", "volume", "turnover"]
    if frame[critical].isna().any().any():
        bad_rows = frame.index[frame[critical].isna().any(axis=1)].tolist()
        raise ValueError(f"Missing critical values in {path.name}; source rows: {bad_rows}")

    if frame.duplicated(["symbol", "trade_date"]).any():
        raise ValueError(f"Duplicate symbol/date records found in {path.name}")

    frame["source_file"] = path.name
    return frame.loc[:, CANONICAL_COLUMNS + ["source_file"]].sort_values(
        ["symbol", "trade_date"]
    ).reset_index(drop=True)


def stage_nse_csv(input_path: Path, output_path: Path) -> pd.DataFrame:
    """Clean one export, save its staged CSV, and return the cleaned frame."""
    cleaned = clean_nse_csv(input_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cleaned.to_csv(output_path, index=False)
    return cleaned


def main() -> None:
    parser = argparse.ArgumentParser(description="Clean one NSE daily security CSV for FundLens.")
    parser.add_argument("input", type=Path, help="Path to the downloaded NSE CSV export.")
    parser.add_argument("output", type=Path, help="Path for the staged FundLens CSV.")
    args = parser.parse_args()

    cleaned = stage_nse_csv(args.input, args.output)
    print(
        f"Staged {len(cleaned)} records for {cleaned['symbol'].nunique()} symbol(s) "
        f"to {args.output}"
    )


if __name__ == "__main__":
    main()
