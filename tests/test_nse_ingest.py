from pathlib import Path

import pandas as pd

from fundlens.ingest.nse import clean_nse_csv


def test_clean_nse_csv_normalises_real_export_format(tmp_path: Path) -> None:
    source = tmp_path / "sample.csv"
    source.write_text(
        '\ufeff"Symbol  ","Series  ","Date  ","Prev Close  ","Open Price  ",'
        '"High Price  ","Low Price  ","Last Price  ","Close Price  ",'
        '"Average Price ","Total Traded Quantity  ","Turnover ₹  ",'
        '"No. of Trades  ","Deliverable Qty  ","% Dly Qt to Traded Qty  "\n'
        '"HDFCBANK","EQ","24-Sep-2026","737.25","725.00","734.85",'
        '"722.70","728.90","728.90","729.96","2,95,75,194",'
        '"21,58,86,97,572.30","2,81,991","1,66,49,331","56.29"\n',
        encoding="utf-8",
    )

    actual = clean_nse_csv(source)

    assert actual.shape == (1, 16)
    assert actual.loc[0, "symbol"] == "HDFCBANK"
    assert actual.loc[0, "trade_date"] == pd.Timestamp("2026-09-24")
    assert actual.loc[0, "volume"] == 29_575_194
    assert actual.loc[0, "turnover"] == 21_588_697_572.30
    assert actual.loc[0, "delivery_pct"] == 56.29
