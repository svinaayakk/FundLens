from pathlib import Path

import pandas as pd

from fundlens.ingest.indices import build_index_panel


def test_index_panel_rejects_mismatched_date_sets(tmp_path: Path) -> None:
    raw_dir = tmp_path / "indices"
    raw_dir.mkdir()
    names = [
        "NIFTY 50-24-09-2025-to-24-09-2026.csv",
        "NIFTY 100-24-09-2025-to-24-09-2026.csv",
        "NIFTY MIDCAP 150-24-09-2025-to-24-09-2026.csv",
        "NIFTY SMALLCAP 250-24-09-2025-to-24-09-2026.csv",
    ]
    for position, name in enumerate(names):
        dates = pd.bdate_range("2025-09-24", periods=248)
        if position == 3:
            dates = dates[:-1].append(pd.DatetimeIndex([pd.Timestamp("2026-09-25")]))
        pd.DataFrame(
            {
                "Date": dates.strftime("%d-%b-%Y"),
                "Open": [100] * 248,
                "High": [101] * 248,
                "Low": [99] * 248,
                "Close": [100] * 248,
                "Shares Traded": [1_000] * 248,
                "Turnover (₹ Cr)": [10] * 248,
            }
        ).to_csv(raw_dir / name, index=False)

    try:
        build_index_panel(raw_dir)
    except ValueError as error:
        assert "DATE_MISMATCH" in str(error)
    else:
        raise AssertionError("Expected date alignment validation to fail")
