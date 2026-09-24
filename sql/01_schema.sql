CREATE SCHEMA IF NOT EXISTS fundlens;

CREATE TABLE IF NOT EXISTS fundlens.dim_stock (
    stock_id BIGSERIAL PRIMARY KEY,
    symbol TEXT NOT NULL UNIQUE,
    company TEXT NOT NULL,
    sector TEXT NOT NULL,
    cap_category TEXT NOT NULL CHECK (cap_category IN ('Large Cap', 'Mid Cap', 'Small Cap')),
    benchmark TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS fundlens.dim_index (
    index_id BIGSERIAL PRIMARY KEY,
    index_name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS fundlens.fact_daily_prices (
    trade_date DATE NOT NULL,
    stock_id BIGINT NOT NULL REFERENCES fundlens.dim_stock(stock_id),
    open_price NUMERIC,
    high_price NUMERIC,
    low_price NUMERIC,
    close_price NUMERIC NOT NULL,
    vwap NUMERIC,
    volume NUMERIC,
    turnover NUMERIC,
    trades NUMERIC,
    delivery_quantity NUMERIC,
    delivery_pct NUMERIC,
    PRIMARY KEY (trade_date, stock_id)
);

CREATE TABLE IF NOT EXISTS fundlens.fact_index_prices (
    trade_date DATE NOT NULL,
    index_id BIGINT NOT NULL REFERENCES fundlens.dim_index(index_id),
    close_price NUMERIC NOT NULL,
    PRIMARY KEY (trade_date, index_id)
);

CREATE TABLE IF NOT EXISTS fundlens.fact_stock_metrics (
    stock_id BIGINT NOT NULL REFERENCES fundlens.dim_stock(stock_id),
    as_of_date DATE NOT NULL,
    window_days INTEGER NOT NULL,
    cumulative_return NUMERIC,
    benchmark_return NUMERIC,
    excess_return NUMERIC,
    annualised_volatility NUMERIC,
    downside_volatility NUMERIC,
    max_drawdown NUMERIC,
    beta NUMERIC,
    alpha NUMERIC,
    sharpe_ratio NUMERIC,
    avg_daily_volume NUMERIC,
    avg_daily_turnover NUMERIC,
    avg_delivery_pct NUMERIC,
    PRIMARY KEY (stock_id, as_of_date, window_days)
);
