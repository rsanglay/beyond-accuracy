# Phase 2: market data

## Scope and settings

Download SPY daily data using Yahoo Finance through yfinance. The fixed initial acquisition range is 2010-01-01 inclusive to 2026-01-01 exclusive. This does not assign training, validation, or test periods. Data settings live in `configs/market_data.json`; the earlier experiment settings remain in `configs/baseline.json`. They are separate schemas and are not yet combined into a model experiment runner.

Set adjustment, corporate-action, timezone, repair, and missing-row options explicitly. Preserve all returned provider columns in the snapshot, including any additional action columns. The provider response is a parsed table, not a preserved HTTP response.

## Price and timing conventions

- `Open`, `High`, `Low`, `Close`, `Volume`: provider values with `auto_adjust=False`. Do not call these historically unadjusted execution quotes: Yahoo prices can already reflect splits.
- `Adj Close`: provider-adjusted history accounting for corporate actions. Returns calculated from it are a historical total-return proxy, not guaranteed executable trade returns.
- `Dividends`, `Stock Splits`: retained action records. Do not add dividends again to returns already computed from an adjusted series.
- Dates label US exchange sessions, not the timestamp at which all columns became available. A daily close and final volume can only be used after that session is complete.
- The downloaded series is a current historical vintage, not a point-in-time archive. Future feature construction must avoid adjustment-dependent price levels and audit information availability. This pipeline alone does not prove absence of leakage.

## Returns

`adjusted_simple_return[t] = AdjClose[t] / AdjClose[t-1] - 1`

`adjusted_log_return[t] = ln(AdjClose[t] / AdjClose[t-1])`

Both are decimals and backward-looking. Multiply a simple return by 100 to display its percentage. Keep log and simple returns distinctly labelled. The first row remains missing. Returns are not targets, signals, or strategy P&L; those phases come later.

## Validation and preservation

Reject empty responses, duplicate or unordered dates, missing required columns, missing expected sessions, extra sessions, nonfinite/nonpositive prices, negative volume or action values, fractional volume, and inconsistent OHLC bounds. Use the NYSE regular-session calendar as a documented SPY session-date proxy; it is not a venue-specific execution model. Holidays and weekends are not missing sessions.

Each snapshot is staged and then moved into a unique directory. File SHA-256 hashes detect changed bytes; they do not certify that the provider data is economically correct. Verification is offline and recalculates returns. Metadata records request settings, dependency versions, code commit, and dirty state. A dirty working tree means the commit alone cannot reconstruct the generating code, so research snapshots should be generated from committed clean code.

## Limitations and sources

Yahoo history can be revised, unavailable, or rate-limited. yfinance is an independent open-source client, not an official Yahoo service. Its project describes personal-use restrictions for Yahoo data. Downloaded data remains local and is excluded from Git; the public repository contains code and synthetic tests, not redistributed market history.

- [Yahoo adjusted-close definition](https://help.yahoo.com/kb/SLN28256.html)
- [yfinance download API: date bounds and options](https://ranaroussi.github.io/yfinance/reference/api/yfinance.download.html)
- [yfinance project and data-use notes](https://github.com/ranaroussi/yfinance)
- [Trading-calendar usage and schedules](https://pandas-market-calendars.readthedocs.io/en/latest/usage.html)

No model or financial performance conclusions can be drawn from successfully downloading prices.
