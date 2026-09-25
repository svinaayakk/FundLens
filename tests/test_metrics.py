import pandas as pd

from fundlens.analytics.metrics import build_analytics


def test_metrics_calculate_cumulative_and_excess_returns() -> None:
    dates = pd.date_range("2026-01-01", periods=3, freq="B")
    stocks = pd.DataFrame(
        {
            "trade_date": dates,
            "symbol": ["TEST"] * 3,
            "company": ["Test Ltd."] * 3,
            "sector": ["Test"] * 3,
            "cap_category": ["Large Cap"] * 3,
            "benchmark": ["Nifty 100"] * 3,
            "close_price": [100.0, 110.0, 121.0],
            "volume": [1000.0] * 3,
            "turnover": [100000.0] * 3,
            "trades": [100.0] * 3,
            "delivery_pct": [50.0] * 3,
        }
    )
    indices = pd.DataFrame(
        {
            "trade_date": dates,
            "index_name": ["Nifty 100"] * 3,
            "close_index_value": [100.0, 105.0, 110.25],
        }
    )

    daily, metrics, index_metrics, cap_summary, breadth = build_analytics(stocks, indices)

    assert round(daily["cumulative_return"].iloc[-1], 6) == 0.21
    assert round(metrics["benchmark_return"].iloc[0], 6) == 0.1025
    assert round(metrics["excess_return"].iloc[0], 6) == 0.1075
    assert round(index_metrics["cumulative_return"].iloc[0], 6) == 0.1025
    assert cap_summary["stock_count"].iloc[0] == 1
    assert len(breadth) == 3
