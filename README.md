# FundLens

> **NSE Cap-Tier Performance, Risk & Liquidity Analysis**

FundLens is an end-to-end analytics project that compares return, risk,
liquidity, market breadth, and sector behaviour across 90 NSE-listed stocks.
It turns daily market data into a reproducible PostgreSQL data model and an
interactive Power BI report.

## Business questions

1. How did large-, mid-, and small-cap stocks perform during the selected year?
2. How did each stock perform versus its cap-tier benchmark and the Nifty 50?
3. How do volatility, drawdown, and risk-adjusted returns differ by cap tier and sector?
4. How do liquidity conditions differ between stocks, sectors, and cap tiers?
5. What relationships exist between return, risk, and liquidity in the observed universe?

## V1 scope

- **Universe:** 90 NSE-listed stocks: 30 large cap, 30 mid cap, and 30 small cap.
- **History:** one year of daily stock and benchmark observations.
- **Benchmarks:** Nifty 50, Nifty 100, Nifty Midcap 150, and Nifty Smallcap 250.
- **Metadata:** company, symbol, sector, cap tier, and assigned cap-tier benchmark.
- **Outputs:** Power BI dashboard and a three-to-four-page findings note.
- **Out of scope:** PySpark, Databricks, and Delta Lake. The dataset does not justify them.

## Technology

- **Python:** ingestion, cleaning, validation, and metric calculation.
- **Pandas / NumPy / SciPy / Statsmodels:** returns, risk statistics, and relationship tests.
- **PostgreSQL:** relational model, transformation SQL, and Power BI source.
- **Power BI:** interactive report and cap-tier/sector drill-downs.
- **Git / GitHub:** version control and reproducibility.

## Data flow

```text
NSE stock data + index data + stock metadata
                    |
                    v
        Python ingestion and validation
                    |
                    v
      staged Parquet files + PostgreSQL tables
                    |
                    v
  SQL marts: performance, risk, liquidity, breadth
                    |
                    v
       Power BI dashboard + findings note
```

## Project status

**Current phase: data-source and universe design.** We will first lock a
reproducible 90-stock universe and confirm the daily-data source.
