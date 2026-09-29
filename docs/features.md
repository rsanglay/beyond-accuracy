# Phase 3 — Trailing features

## Information contract

Row t is calculated only after session t has completed and its final data is available. It uses inputs through t, never t+1. This is not permission to trade at t's closing price. Execution and targets remain separate future checkpoints.

The CLI verifies a Phase 2 snapshot (including calendar completeness and checksums) before calling the feature functions. Direct Python callers must supply consecutive, validated trading-session rows. The functions reject missing/invalid prices or volume and unordered/duplicate indexes; they do not independently infer which exchange sessions are missing.

## Definitions

P denotes provider-adjusted close, V volume, and r[t] = P[t]/P[t-1] - 1. Windows count trading observations, not calendar days. All unspecified early values remain NaN; no filling, row dropping, fitting, scaling, or target construction occurs.

| Column | Calculation | First valid one-based row |
| --- | --- | --- |
| return_current | r[t], known after session t | 2 |
| return_lag_k | r[t-k] | k+2 |
| momentum_n | P[t]/P[t-n] - 1 | n+1 |
| sma_n_diagnostic | Mean of n prices ending at t | n |
| volatility_n | Sample standard deviation of n returns ending at t, divisor n-1 | n+1 |
| rsi_n | Wilder RSI seeded with n changes | n+1 |
| relative_volume_n | V[t] divided by mean of V[t-n] through V[t-1] | n+1 |

Return, momentum, and volatility values are decimals. Volatility is not annualised. RSI is on a 0–100 scale. Relative volume is a ratio: 2 means twice the prior average. SMA is in adjusted-price units and is explicitly diagnostic, excluded from the candidate-column list. We have not yet taught or selected a scale-free moving-average model feature.

## Wilder RSI

For each price change, gain = max(change, 0), loss = max(-change, 0). Seed each average with the first n changes, then update with ((n-1)*previous_average + new_value)/n. This preserves the specified initial arithmetic mean rather than relying on a library's implicit exponential initialisation.

RSI = 100 - 100/(1 + average_gain/average_loss). Code uses the equivalent 100*average_gain/(average_gain+average_loss) to handle one-sided histories without dividing by zero. Both zero gives 50 by project convention; gains only gives 100, losses only gives 0. A high RSI does not guarantee reversal. A zero volume baseline gives an undefined relative-volume value, not infinity or an invented zero.

## Configuration and outputs

`configs/features.json` fixes a small initial set of windows for illustration, not windows selected for predictive performance. RSI uses 14 changes. Later robustness work must account for trying alternative settings.

```bash
beyond-accuracy build-features --snapshot data/snapshots/<snapshot-id> --config configs/features.json
```

Creates a unique local directory containing `features.csv` and `metadata.json`. Metadata includes complete settings, source snapshot hashes, output hash, dependency versions, generating commit/dirty state, missing counts, and separate candidate/diagnostic columns. No incomplete rows are deleted. Candidate completeness is informational and is not a training split or target-availability check. Outputs remain ignored by Git.

## Verification and limits

Tests check known averages, momentum, return lags, sample volatility, RSI seeds and updates, flat and one-sided RSI, all warm-up boundaries, zero-volume handling, and snapshot linkage. Prefix tests calculate on truncated history and compare with the same rows from full-history calculations; mutation tests change future prices and volume and require earlier features to remain identical.

These tests establish time causality within a fixed input vintage. They do not establish point-in-time accuracy of provider revisions. A uniform rescaling of adjusted historical prices preserves candidate values but changes SMA levels; a separate test records this distinction. Real historical revisions can be more complex. Models must not silently ingest diagnostic price levels. SPY split events or different assets require a further audit of volume adjustment conventions.

Rolling windows explicitly require complete observations, matching [pandas rolling-window semantics](https://pandas.pydata.org/docs/reference/api/pandas.Series.rolling.html). There is no predictive-performance claim at this phase.
