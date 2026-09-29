# Beyond Accuracy

**Evaluating Machine Learning Trading Strategies Under Realistic Market Frictions**

An incremental quantitative research and learning project investigating whether better market-direction predictions translate into better trading outcomes after costs.

**Status: Phase 3 feature-engineering pipeline. No trained models, backtests, or strategy performance findings yet.**

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

This verifies the existing snapshot and calculates trailing returns, momentum, moving-average diagnostics, sample volatility, Wilder RSI, and relative volume. No network request is needed. Early undefined values are preserved, and each output directory records settings and provenance. See [feature definitions and timing](docs/features.md). No targets or models are implemented yet.
