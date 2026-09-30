# Phase 5 — Prediction benchmarks

A benchmark is an explicit simple reference. Complexity is useful only if it produces a defensible improvement under the same evaluation conditions.

## Implemented rules

| Rule | Inputs | Prediction |
| --- | --- | --- |
| Majority | Known training labels and their outcome sessions | Most frequent class in the supplied training slice; ties choose 0 |
| Previous-session direction | `return_current` at prediction session t | 1 if positive, 0 if zero/negative; missing remains missing |
| Momentum | Explicit `momentum_n` feature, selected by window argument | 1 if positive, 0 if zero/negative; missing remains missing |

Prediction 0 means nonpositive next return, not automatically a short position or cash allocation. Predictions are class labels, not calibrated probabilities, trading signals, or returns. There is no automatic refitting when test outcomes are supplied; the prediction method does not accept test outcomes.

The previous-session rule uses `return_current` because today's completed return is the latest observed return relative to the next outcome. Using `return_lag_1` would add an unintended extra delay. Feature-based rules read only their explicitly named column. Future columns must still be kept out of later model inputs.

## Majority timing contract

`MajorityBenchmark.fit(training_targets, fit_after_session=...)` accepts already-selected training rows. It rejects unknown/nonbinary labels, malformed session dates, outcomes not later than their feature sessions, and outcomes later than the stated fitting session. That fitting date explicitly means **after its final closing data is available**, not midnight. A known outcome from that session can be used to fit a prediction for the next session after the close.

`predict(sessions)` returns the frozen class and rejects prediction sessions before fitting. These guards do not select a valid train/test split: chronological folds, common scoring dates, and permitted refits remain Phase 6. Fabricating a fit date or feeding mislabeled data cannot be prevented by these checks alone.

## Local illustration

```bash
beyond-accuracy benchmark-demo
```

This synthetic example fits six positive and four nonpositive training labels. All majority predictions are 1. The second scenario has a negative latest return but positive five-session momentum, so the two feature-based rules disagree. Dates are illustrative weekdays, not a market-data calendar. No SPY evaluation, performance metrics, trained ML model, or final test split is produced.

## Buy and hold: specified, financial implementation deferred

Buy SPY at the eventual feasible initial execution time and remain invested over the chosen evaluation period regardless of intervening daily losses. Selling because of a losing streak is a different strategy. The entry/exit, dividend, cost, and portfolio-return calculations will be implemented at the execution and backtesting checkpoints. Do not treat an always-positive classifier as a completed buy-and-hold backtest.

## Validation and limitations

Local tests cover majority and tie rules, a 60% positive training sample followed by a 40% positive test sample, unavailable labels, fit timing, flat/missing feature values, rule disagreement, future-data changes, and independence from added outcome columns. No cloud Actions runs are required.

When evaluated later, compare methods on identical eligible out-of-sample observations. Do not choose the majority class, momentum window, or tie rule using test results. Lower classification accuracy alone does not establish worse trading performance; financial comparisons come later.
