# Research and learning roadmap

Complete each conceptual checkpoint before implementing its phase. Workflow: explain, ask, wait, review, build, show, test, interpret. Record learner answers without inventing understanding.

1. Software architecture — checkpoint passed; foundation implemented.
2. Market data — implemented and merged (PR #2); output checkpoint passed. Percentage arithmetic remains a practice topic.
3. Feature engineering — implemented and merged (PR #3); output checkpoint passed; volatility and RSI arithmetic remain practice topics.
4. Targets — implemented and merged (PR #4); output checkpoint passed.
5. Benchmarks — prediction rules and output check completed; PR #5 merged. Buy-and-hold financial implementation deferred to execution/backtesting.
6. Expanding-window walk-forward validation — implemented and merged (PR #7); introductory/output checkpoints passed.
7. Models — Logistic Regression merged (PR #8), output checkpoint passed. Random Forest introductory checkpoint passed and implementation on a review branch; output check next. XGBoost and LightGBM remain future lessons.
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
Execution horizon and its relation to the fixed next-session close-to-close prediction target; holding/cash assumptions; parameter-search budget; protocol for the reserved 2024–2025 final evaluation; inference design. Resolve at the relevant teaching checkpoint before implementation.

## Reproducibility plan
Each research run will eventually capture the code commit and dirty state, configuration, data hashes, dependencies, Python/platform versions, seeds, and generated outputs. Phase 2 records data snapshot metadata; no model experiment runner exists yet.

The earlier external build specification was not available in this conversation. This roadmap records the supplied requirements without inventing missing choices.

## Deferred quantum extension

The classical sequence above remains the priority and must remain independently publishable. After completing it and passing the methodology/findings checkpoint, follow the separate [quantum extension roadmap](quantum_extension.md). No quantum implementation or dependencies are introduced before those teaching gates.
