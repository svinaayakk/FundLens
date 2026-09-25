"""Produce FundLens performance, risk, liquidity, and breadth outputs."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


STOCK_METADATA = ["symbol", "company", "sector", "cap_category", "benchmark"]


def _max_drawdown(close_prices: pd.Series) -> float:
    """Return the largest peak-to-trough close-price loss as a decimal."""
    drawdowns = close_prices.div(close_prices.cummax()).sub(1)
    return float(drawdowns.min())


def _downside_volatility(returns: pd.Series, trading_days: int) -> float:
    """Annualise the standard deviation of negative daily returns."""
    downside = returns.loc[returns.lt(0)].dropna()
    if len(downside) < 2:
        return np.nan
    return float(downside.std(ddof=1) * np.sqrt(trading_days))


def build_analytics(
    stock_prices: pd.DataFrame,
    index_prices: pd.DataFrame,
    trading_days: int = 252,
    risk_free_rate_annual: float = 0.0,
    moving_average_days: int = 50,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Build daily returns, stock/index metrics, cap summaries, and daily breadth.

    Returns are close-to-close simple returns. Alpha and beta use an OLS-equivalent
    covariance calculation against the stock's assigned cap-tier benchmark.
    The v1 risk-free-rate scenario is deliberately explicit and defaults to 0%.
    """
    required_stock_columns = {
        "trade_date", "close_price", "volume", "turnover", "trades", "delivery_pct", *STOCK_METADATA
    }
    required_index_columns = {"trade_date", "index_name", "close_index_value"}
    missing_stock = required_stock_columns.difference(stock_prices.columns)
    missing_index = required_index_columns.difference(index_prices.columns)
    if missing_stock:
        raise ValueError(f"Stock panel is missing columns: {sorted(missing_stock)}")
    if missing_index:
        raise ValueError(f"Index panel is missing columns: {sorted(missing_index)}")

    stocks = stock_prices.copy()
    indices = index_prices.copy()
    stocks["trade_date"] = pd.to_datetime(stocks["trade_date"])
    indices["trade_date"] = pd.to_datetime(indices["trade_date"])
    if stocks.duplicated(["symbol", "trade_date"]).any():
        raise ValueError("Stock panel has duplicate stock/date observations")
    if indices.duplicated(["index_name", "trade_date"]).any():
        raise ValueError("Index panel has duplicate index/date observations")

    stocks = stocks.sort_values(["symbol", "trade_date"]).reset_index(drop=True)
    indices = indices.sort_values(["index_name", "trade_date"]).reset_index(drop=True)
    stocks["daily_return"] = stocks.groupby("symbol")["close_price"].pct_change(fill_method=None)
    stocks["cumulative_return"] = stocks["close_price"].div(
        stocks.groupby("symbol")["close_price"].transform("first")
    ).sub(1)
    stocks["moving_average_50d"] = stocks.groupby("symbol")["close_price"].transform(
        lambda values: values.rolling(moving_average_days, min_periods=moving_average_days).mean()
    )
    stocks["close_above_50d_ma"] = stocks["close_price"].gt(stocks["moving_average_50d"])

    indices["benchmark_daily_return"] = indices.groupby("index_name")["close_index_value"].pct_change(
        fill_method=None
    )
    indices["benchmark_cumulative_return"] = indices["close_index_value"].div(
        indices.groupby("index_name")["close_index_value"].transform("first")
    ).sub(1)
    benchmark_daily = indices.loc[
        :, ["trade_date", "index_name", "close_index_value", "benchmark_daily_return", "benchmark_cumulative_return"]
    ].rename(columns={"index_name": "benchmark", "close_index_value": "benchmark_close_index_value"})
    daily = stocks.merge(benchmark_daily, on=["trade_date", "benchmark"], how="left", validate="many_to_one")
    benchmark_columns = ["benchmark_close_index_value", "benchmark_daily_return", "benchmark_cumulative_return"]
    if daily[benchmark_columns].isna().all(axis=1).any():
        missing = daily.loc[daily[benchmark_columns].isna().all(axis=1), ["symbol", "trade_date", "benchmark"]]
        raise ValueError(f"Missing assigned benchmark observations: {missing.head().to_dict('records')}")
    daily["daily_excess_return"] = daily["daily_return"].sub(daily["benchmark_daily_return"])
    daily["cumulative_excess_return"] = daily["cumulative_return"].sub(daily["benchmark_cumulative_return"])
    daily["amihud_illiquidity_x1e6"] = (
        daily["daily_return"].abs().div(daily["turnover"].replace(0, np.nan)).mul(1_000_000)
    )

    metric_rows: list[dict[str, object]] = []
    for symbol, group in daily.groupby("symbol", sort=True):
        group = group.sort_values("trade_date")
        valid = group.dropna(subset=["daily_return", "benchmark_daily_return"])
        stock_return = valid["daily_return"]
        benchmark_return = valid["benchmark_daily_return"]
        benchmark_variance = benchmark_return.var(ddof=1)
        beta = np.nan if pd.isna(benchmark_variance) or benchmark_variance == 0 else stock_return.cov(benchmark_return) / benchmark_variance
        alpha_daily = np.nan if pd.isna(beta) else stock_return.mean() - beta * benchmark_return.mean()
        return_std = stock_return.std(ddof=1)
        daily_risk_free = (1 + risk_free_rate_annual) ** (1 / trading_days) - 1
        sharpe = np.nan if pd.isna(return_std) or return_std == 0 else ((stock_return.mean() - daily_risk_free) / return_std) * np.sqrt(trading_days)
        metadata = group.iloc[-1]
        metric_rows.append(
            {
                "symbol": symbol,
                "company": metadata["company"],
                "sector": metadata["sector"],
                "cap_category": metadata["cap_category"],
                "benchmark": metadata["benchmark"],
                "as_of_date": group["trade_date"].max(),
                "window_days": len(group),
                "return_observations": len(valid),
                "cumulative_return": group["cumulative_return"].iloc[-1],
                "benchmark_return": group["benchmark_cumulative_return"].iloc[-1],
                "excess_return": group["cumulative_excess_return"].iloc[-1],
                "annualised_volatility": return_std * np.sqrt(trading_days),
                "downside_volatility": _downside_volatility(stock_return, trading_days),
                "max_drawdown": _max_drawdown(group["close_price"]),
                "beta": beta,
                "alpha_annualised": alpha_daily * trading_days,
                "sharpe_ratio": sharpe,
                "avg_daily_volume": group["volume"].mean(),
                "avg_daily_turnover": group["turnover"].mean(),
                "avg_daily_trades": group["trades"].mean(),
                "avg_delivery_pct": group["delivery_pct"].mean(),
                "avg_turnover_20d": group["turnover"].tail(20).mean(),
                "avg_turnover_63d": group["turnover"].tail(63).mean(),
                "amihud_illiquidity_x1e6": group["amihud_illiquidity_x1e6"].mean(),
            }
        )
    stock_metrics = pd.DataFrame(metric_rows)

    index_metric_rows: list[dict[str, object]] = []
    for index_name, group in indices.groupby("index_name", sort=True):
        group = group.sort_values("trade_date")
        returns = group["benchmark_daily_return"].dropna()
        return_std = returns.std(ddof=1)
        daily_risk_free = (1 + risk_free_rate_annual) ** (1 / trading_days) - 1
        sharpe = np.nan if pd.isna(return_std) or return_std == 0 else ((returns.mean() - daily_risk_free) / return_std) * np.sqrt(trading_days)
        index_metric_rows.append(
            {
                "index_name": index_name,
                "as_of_date": group["trade_date"].max(),
                "window_days": len(group),
                "return_observations": len(returns),
                "cumulative_return": group["benchmark_cumulative_return"].iloc[-1],
                "annualised_volatility": return_std * np.sqrt(trading_days),
                "max_drawdown": _max_drawdown(group["close_index_value"]),
                "sharpe_ratio": sharpe,
            }
        )
    index_metrics = pd.DataFrame(index_metric_rows)

    cap_tier_summary = (
        stock_metrics.groupby("cap_category", as_index=False)
        .agg(
            stock_count=("symbol", "nunique"),
            mean_cumulative_return=("cumulative_return", "mean"),
            median_cumulative_return=("cumulative_return", "median"),
            mean_excess_return=("excess_return", "mean"),
            median_annualised_volatility=("annualised_volatility", "median"),
            mean_max_drawdown=("max_drawdown", "mean"),
            median_sharpe_ratio=("sharpe_ratio", "median"),
            median_avg_daily_turnover=("avg_daily_turnover", "median"),
            median_amihud_illiquidity_x1e6=("amihud_illiquidity_x1e6", "median"),
        )
        .merge(
            stock_metrics.groupby("cap_category", as_index=False)["benchmark_return"].first(),
            on="cap_category",
            how="left",
            validate="one_to_one",
        )
        .sort_values("cap_category")
        .reset_index(drop=True)
    )

    breadth = (
        daily.groupby(["trade_date", "cap_category"], as_index=False)
        .agg(
            stock_count=("symbol", "nunique"),
            advancers=("daily_return", lambda values: int(values.gt(0).sum())),
            decliners=("daily_return", lambda values: int(values.lt(0).sum())),
            unchanged=("daily_return", lambda values: int(values.eq(0).sum())),
            median_daily_return=("daily_return", "median"),
            stocks_above_50d_ma=("close_above_50d_ma", "sum"),
        )
        .sort_values(["cap_category", "trade_date"])
        .reset_index(drop=True)
    )
    breadth["advance_decline_ratio"] = breadth["advancers"].div(breadth["decliners"].replace(0, np.nan))
    breadth["pct_above_50d_ma"] = breadth["stocks_above_50d_ma"].div(breadth["stock_count"])
    return daily, stock_metrics, index_metrics, cap_tier_summary, breadth


def main() -> None:
    parser = argparse.ArgumentParser(description="Build FundLens analytics outputs from staged price panels.")
    parser.add_argument("--stocks", type=Path, default=Path("data/staged/daily_prices.csv"))
    parser.add_argument("--indices", type=Path, default=Path("data/staged/index_prices.csv"))
    parser.add_argument("--output-dir", type=Path, default=Path("data/staged"))
    parser.add_argument("--trading-days", type=int, default=252)
    parser.add_argument("--risk-free-rate", type=float, default=0.0)
    args = parser.parse_args()

    daily, metrics, index_metrics, cap_summary, breadth = build_analytics(
        pd.read_csv(args.stocks),
        pd.read_csv(args.indices),
        trading_days=args.trading_days,
        risk_free_rate_annual=args.risk_free_rate,
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    outputs = {
        "daily_returns.csv": daily,
        "stock_metrics.csv": metrics,
        "index_metrics.csv": index_metrics,
        "cap_tier_summary.csv": cap_summary,
        "market_breadth.csv": breadth,
    }
    for file_name, frame in outputs.items():
        frame.to_csv(args.output_dir / file_name, index=False)
    print(f"Created analytics for {metrics['symbol'].nunique()} stocks through {metrics['as_of_date'].max():%Y-%m-%d}.")
    for file_name in outputs:
        print(f"Output: {args.output_dir / file_name}")


if __name__ == "__main__":
    main()
