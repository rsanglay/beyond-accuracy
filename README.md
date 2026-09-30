# Beyond Accuracy

**Evaluating Machine Learning Trading Strategies Under Realistic Market Frictions**

An incremental quantitative research and learning project investigating whether better market-direction predictions translate into better trading outcomes after costs.

**Status: Phase 7b Random Forest. Logistic Regression and Random Forest development predictions are available; no backtests or strategy performance findings yet.**

## Planned research
SPY; Logistic Regression, Random Forest, XGBoost, and LightGBM; simple benchmarks; expanding-window walk-forward evaluation; realistic execution timing; 0/5/10/25 bps transaction costs; predictive and financial metrics; yearly stability, regime analysis, statistical uncertainty, and robustness checks. All choices and claims will be documented as the project progresses.

## Run the foundation
Requires Python 3.12 or newer. From this directory:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.lock
python -m pip install --no-deps -e .
beyond-accuracy check-config --config configs/baseline.json
python -m unittest discover -s tests -v
```

The CLI validates settings and prepares market-data snapshots. It does not run a trading experiment. A misspelled or unsupported setting fails explicitly rather than silently changing assumptions.

## Layout
| Path | Responsibility |
| --- | --- |
| `src/beyond_accuracy/` | Shared Python implementation and CLI |
| `tests/` | Automated checks; financial invariants added with their implementations |
| `configs/` | Explicit experiment settings |
| `data/` | Local data snapshots, excluded from Git |
| `notebooks/` | Exploration and teaching, importing shared code |
| `results/` | Generated outputs and future experiment metadata |
| `paper/` | Research report based on real results |
| `docs/` | Learning log, concept checklist, and roadmap |

## Reproducibility
`requirements.lock` pins resolved dependency versions. Snapshots record input-file hashes, request settings, code commit and dirty status, Python/platform details, and installed package versions. Retain the actual snapshot: downloading again can yield revised history. A random seed alone does not reproduce a study. The lock does not contain artifact hashes, and the container base is not pinned by digest.

Run tests locally and record their results in each PR. GitHub Actions is disabled; its workflow supports manual dispatch only and must not be enabled or run without an explicit owner request. The Dockerfile provides the same configuration-check entry point:

```bash
docker build -t beyond-accuracy .
docker run --rm beyond-accuracy
```

The container is a starting environment, not a claim of bit-for-bit reproducibility; image digests and the research environment will be fixed before experiments.

See [the learning log](docs/learning_log.md), [concept checklist](docs/concepts.md), and [roadmap](docs/roadmap.md).

## Contributing

Changes follow feature branches, pull requests, local validation, and owner review before merging. See [the development workflow](CONTRIBUTING.md).

## Prepare market data

```bash
beyond-accuracy download-data --config configs/market_data.json
beyond-accuracy verify-data data/snapshots/<snapshot-id>
```

The initial request covers 2010-01-01 inclusive through 2026-01-01 exclusive. This is a data acquisition window, not a selected train/test split. Each download creates a separate snapshot with `provider.csv`, `returns.csv`, and `metadata.json`. Offline verification checks file hashes, data validity, and recomputed returns.

The first return is missing because the snapshot has no preceding price. No missing prices or sessions are filled. CI uses synthetic fixtures and does not require Yahoo access. See [market-data conventions and limitations](docs/market_data.md).

## Build features locally

```bash
beyond-accuracy build-features --snapshot data/snapshots/<snapshot-id> --config configs/features.json
```

This verifies the existing snapshot and calculates trailing returns, momentum, moving-average diagnostics, sample volatility, Wilder RSI, and relative volume. No network request is needed. Early undefined values are preserved, and each output directory records settings and provenance. See [feature definitions and timing](docs/features.md). Targets are prepared separately from model features.

## Build next-session targets

```bash
beyond-accuracy build-targets --snapshot data/snapshots/<snapshot-id>
```

Creates separate historical outcomes and records the session after which each becomes known. Positive next-session adjusted returns are class 1; zero/negative returns are class 0; the final unknown stays missing. See [target alignment and timing](docs/targets.md). These labels are not trading returns.

## Inspect the benchmark rules

```bash
beyond-accuracy benchmark-demo
```

Shows synthetic predictions from a frozen training-majority classifier, the latest observed return's direction, and trailing momentum. It does not evaluate SPY or run a strategy. See [benchmark rules and timing](docs/benchmarks.md). Chronological prediction generation is implemented; buy-and-hold financial calculations remain a later phase.

## Generate chronological benchmark predictions

```bash
beyond-accuracy walk-forward --snapshot data/snapshots/<snapshot-id> --features-config configs/features.json --config configs/walk_forward.json
```

Uses annual expanding training windows for 2019–2023 development predictions, with 2024–2025 reserved. All benchmarks share eligible test dates; training labels must already be available. This command produces benchmark predictions; add the optional Logistic Regression configuration below to fit the first ML model. No performance report or trading returns are produced. See [validation timing and limitations](docs/walk_forward.md).

## Add Logistic Regression

Append `--logistic-config configs/logistic.json` to the walk-forward command. Each annual fold fits a fresh training-only scaler and regularised model, then saves positive-class probabilities and classes on the shared test dates. See [model meaning, settings, and audit records](docs/logistic_regression.md). Install the updated `requirements.lock` before running.

## Add Random Forest

Append `--forest-config configs/random_forest.json` to the walk-forward command, optionally alongside Logistic Regression. Each fold fits an unscaled forest on the same eligible training rows and saves probabilities/classes on the same test dates. See [forest rules, complexity limits, and timing](docs/random_forest.md). No model-performance comparison has been reported yet.
