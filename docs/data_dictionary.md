# FundLens data dictionary

## Dimensions

| Field | Type | Definition |
|---|---|---|
| `stock_id` | integer | Stable internal stock identifier. |
| `symbol` | text | NSE trading symbol. |
| `company` | text | Listed-company name. |
| `sector` | text | Standardised economic sector. |
| `cap_category` | text | Large Cap, Mid Cap, or Small Cap. |
| `benchmark` | text | Cap-tier benchmark assigned to the stock. |

## Daily market data

| Field | Type | Definition |
|---|---|---|
| `trade_date` | date | NSE trading date. |
| `open`, `high`, `low`, `close` | numeric | Daily OHLC prices. |
| `vwap` | numeric | Volume-weighted average price, where supplied. |
| `volume` | numeric | Shares traded. |
| `turnover` | numeric | Daily traded value. |
| `trades` | numeric | Number of trades. |
| `delivery_quantity` | numeric | Shares delivered. |
| `delivery_pct` | numeric | Delivered shares as a percentage of volume. |

## Derived metrics

| Field | Definition |
|---|---|
| `daily_return` | Percentage change in close from the prior trading day. |
| `cumulative_return` | Growth from the selected period's first close. |
| `excess_return` | Stock return minus its relevant cap-tier benchmark return. |
| `annualised_volatility` | Standard deviation of daily returns × √252. |
| `max_drawdown` | Largest peak-to-trough loss in the selected period. |
| `beta` | Sensitivity of stock returns to its benchmark returns. |
| `alpha` | Regression intercept annualised from daily excess returns. |
| `avg_daily_turnover` | Mean daily turnover over the selected analysis window. |
