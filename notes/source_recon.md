# FundLens source reconnaissance

## Objective

Confirm reproducible sources for the 90-stock universe, daily market data,
index prices, and stock-sector metadata before building the ingestion pipeline.

## Locked universe decision

The project uses a static, curated universe of 90 stocks selected from the
official constituent snapshot dated 2026-09-24: 30 Nifty 100 constituents, 30
Nifty Midcap 150 constituents, and 30 Nifty Smallcap 250 constituents.

This is a deliberate point-in-time classification. Constituents can move across
cap-tier indices at rebalances, so the project will not reclassify stocks using
today's membership while analysing the preceding 12 months. This reduces
classification drift but retains survivorship bias; both choices will be stated
in the final methodology.

The source file is `config/stock_universe.csv`. Before final publication, save
or link the three underlying official constituent extracts and their as-of date.

## Required checks

1. Capture the as-of date for official Nifty 100, Nifty Midcap 150, and Nifty
   Smallcap 250 constituent lists.
2. Select 30 liquid, sector-representative stocks from each cap tier.
3. Save the final universe in `config/stock_universe.csv`.
4. Confirm availability of OHLC, volume, turnover, trade count, delivery
   quantity, and delivery percentage for a sample stock and date.
5. Confirm daily close history for all four benchmark indices.
6. Record source URLs, data gaps, access restrictions, and fallback choices.

## Confirmed NSE daily-file contract

The primary daily security-wise NSE CSV provides 15 fields: symbol, series,
date, previous close, open, high, low, last, close, average price, traded
quantity, turnover, number of trades, deliverable quantity, and deliverable
percentage. FundLens will retain the raw fields and standardise them using the
mapping in `config/sources.yaml`.

Only records with `Series = EQ` will enter the V1 equity panel. The ingestion
job will validate the header names and reject a file whose expected columns are
missing, rather than silently producing incomplete data.

### Observed sample: HDFCBANK, 17–24 September 2026

- File contains 6 trading-day records and all 15 expected fields.
- The file is encoded with a UTF-8 BOM and has trailing spaces in headers.
- Actual headers use `Prev Close`, `Deliverable Qty`, and `% Dly Qt to Traded
  Qty`, not the longer labels assumed initially.
- Quantity, turnover, trade-count, and delivery-quantity values use Indian
  comma grouping and must be converted to numeric values after commas are
  removed.
- Rows are reverse chronological. Ingestion will parse the date and sort
  ascending before calculating returns.

### 12-month ingestion validation: 24 September 2025 to 24 September 2026

| Cap tier | Validation symbol | EQ observations | Missing critical fields | Result |
|---|---:|---:|---:|---|
| Large Cap | HDFCBANK | 248 | 0 | Pass |
| Mid Cap | BSE | 248 | 0 | Pass |
| Small Cap | CUB | 248 | 0 | Pass |

All three representative exports contain a complete daily panel from
2025-09-24 to 2026-09-24, with no duplicate symbol/date records and complete
close, volume, turnover, trade-count, delivery-quantity, and delivery-percent
fields. The source format is approved for the remaining 87 stocks.

## Universe amendment: ABB replaces TMPV

TMPV was removed from the one-year universe because its export joins 20 legacy
`TATAMOTORS` observations to 228 `TMPV` observations around a demerger, creating
a non-comparable price discontinuity. ABB India (`ABB`) replaces TMPV in the
Large Cap sample. ABB has 248 complete `EQ` observations from 2025-09-24 to
2026-09-24 with no duplicate dates or missing critical liquidity fields.

## Universe amendment: final Mid Cap replacements

The original candidate list included Cummins India, HDFC Asset Management,
Indian Hotels, Max Healthcare, Muthoot Finance, and Solar Industries. Those
stocks had moved to Nifty 100 by the official constituent snapshot and were
not retained in the Mid Cap sample. The approved Nifty Midcap 150 replacements
are 3M India, ACC, AIA Engineering, Ajanta Pharma, Alkem Laboratories, and
Apollo Tyres.

`AIAENG` was already present in the interim file. To apply the final selection
without changing the 30-stock Mid Cap count, the interim symbols `IRCTC`,
`MEDANTA`, `NMDC`, `WAAREEENER`, and `360ONE` were replaced with `3MINDIA`,
`ACC`, `AJANTPHARM`, `ALKEM`, and `APOLLOTYRE`. All six final additions have
248 complete `EQ` observations for 2025-09-24 to 2026-09-24.

## Universe amendment: final Small Cap list

The Small Cap panel is a final user-approved list of 30 unique Nifty Smallcap
250 symbols. Each selected symbol has a complete NSE `EQ` export containing
248 observations from 2025-09-24 to 2026-09-24, with no missing critical
price or liquidity fields. The definitive list is maintained in
`config/stock_universe.csv` rather than inferred from earlier replacement
tables.

## Exit criteria

- A versioned 90-stock universe exists.
- One week of daily data has been validated for three stocks.
- All four benchmark series have a confirmed source.
- Known source limitations are documented.
