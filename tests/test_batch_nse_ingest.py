from pathlib import Path

import pandas as pd

from fundlens.ingest.batch_nse import build_daily_panel


def test_batch_panel_rejects_a_symbol_without_248_observations(tmp_path: Path) -> None:
    universe = pd.DataFrame(
        {
            "symbol": ["HDFCBANK"],
            "company": ["HDFC Bank Ltd."],
            "sector": ["Financial Services"],
            "cap_category": ["Large Cap"],
            "benchmark": ["Nifty 100"],
            "selection_date": ["2026-09-24"],
        }
    )
    universe_path = tmp_path / "universe.csv"
    universe.to_csv(universe_path, index=False)
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    (raw_dir / "sample.csv").write_text(
        '\ufeff"Symbol  ","Series  ","Date  ","Prev Close  ","Open Price  ",'
        '"High Price  ","Low Price  ","Last Price  ","Close Price  ",'
        '"Average Price ","Total Traded Quantity  ","Turnover ₹  ",'
        '"No. of Trades  ","Deliverable Qty  ","% Dly Qt to Traded Qty  "\n'
        '"HDFCBANK","EQ","24-Sep-2026","737.25","725.00","734.85",'
        '"722.70","728.90","728.90","729.96","2,95,75,194",'
        '"21,58,86,97,572.30","2,81,991","1,66,49,331","56.29"\n',
        encoding="utf-8",
    )

    try:
        build_daily_panel(raw_dir, universe_path)
    except ValueError as error:
        assert "UNEXPECTED_COVERAGE" in str(error)
    else:
        raise AssertionError("Expected coverage validation to fail")
