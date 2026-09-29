# Research and learning roadmap

Complete each conceptual checkpoint before implementing its phase. Workflow: explain, ask, wait, review, build, show, test, interpret. Record learner answers without inventing understanding.

1. Software architecture — checkpoint passed; foundation implemented.
2. Market data — next checkpoint; OHLCV, adjustments, simple and log returns.
3. Feature engineering — lagged returns, momentum, moving averages, volatility, RSI, volume, rolling windows, information availability.
4. Targets — shifted outcomes and leakage checks.
5. Benchmarks — buy and hold, majority classifier, momentum, naive predictions.
6. Expanding-window walk-forward validation — chronology and label availability.
7. Models — separate checkpoints for Logistic Regression, Random Forest, XGBoost, LightGBM.
8. ML metrics — accuracy, precision, recall, F1, ROC-AUC, log loss, Brier score.
9. Signals and execution — predictions, signals, positions, trades, feasible timing.
10. Backtesting — positions, compounding, turnover, costs; inactive-portfolio invariant.
11. Transaction costs — 0/5/10/25 bps sensitivity and turnover.
12. Financial metrics — CAGR, volatility, Sharpe, Sortino, drawdowns.
13. Results — learner interprets first; cost sensitivity, yearly stability, simple regimes.
14. Statistical analysis — uncertainty, dependence-aware bootstrap, economic vs statistical significance.
15. Robustness — thresholds, periods, costs, multiple testing and regime dependence.
16. Research interpretation — interview learner before writing findings.
17. Paper — explain section purpose; review claims and real citations together.
18. LinkedIn and CV — ask for learner's key finding before drafting.
19. Interview practice — one question at a time; reasoning over scripts.

## Decisions still open
Data source and date range; adjustment conventions; exact prediction target and execution horizon; holding/cash assumptions; validation boundaries; parameter-search budget; final untouched evaluation period; inference design. Resolve at the relevant teaching checkpoint before implementation.

## Reproducibility plan
Each research run will eventually capture the code commit and dirty state, configuration, data hashes, dependencies, Python/platform versions, seeds, and generated outputs. Phase 1 only validates configuration; no experiment runner exists yet.

The earlier external build specification was not available in this conversation. This roadmap records the supplied requirements without inventing missing choices.
