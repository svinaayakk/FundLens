# FundLens methodology

## Analysis window

The v1 analysis uses 248 NSE trading dates from 24 September 2025 through
24 September 2026. The universe is a static, curated sample of 30 stocks from
each of the Nifty 100, Nifty Midcap 150, and Nifty Smallcap 250 constituent
snapshots dated 24 September 2026.

## Benchmarking

Each stock is evaluated against the index matching its cap tier: Nifty 100,
Nifty Midcap 150, or Nifty Smallcap 250. Nifty 50 is retained as the overall
market reference. All return calculations use daily close prices and simple
close-to-close returns.

## Risk and performance

- Cumulative return = final close / first close − 1.
- Excess return = stock cumulative return − assigned benchmark cumulative return.
- Annualised volatility = standard deviation of daily returns × √252.
- Downside volatility uses only negative daily returns.
- Maximum drawdown is the deepest decline from a preceding closing-price peak.
- Beta = covariance of stock and assigned benchmark daily returns / benchmark variance.
- Annualised alpha is the daily regression intercept × 252.
- Sharpe ratio is annualised using a 0% risk-free-rate scenario in v1.

## Liquidity

Average daily volume, turnover, number of trades, delivery percentage, 20/63-day
turnover, and the Amihud illiquidity measure are calculated from NSE daily data.
The Amihud measure is absolute daily return divided by daily turnover; a higher
value indicates lower trading liquidity.

## Limitation

This is a selected 90-stock sample, not a reconstruction of the full index.
The fixed 0% risk-free-rate scenario is a simplification to make the v1 results
reproducible; a future version can use a dated Treasury-bill series.
