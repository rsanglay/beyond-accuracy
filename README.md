# Beyond Accuracy

**Evaluating Machine Learning Trading Strategies Under Realistic Market Frictions**

An incremental quantitative research and learning project investigating whether better market-direction predictions translate into better trading outcomes after costs.

**Status: Phase 1 foundation. No market data, trained models, backtests, or empirical findings yet.**

## Planned research
SPY; Logistic Regression, Random Forest, XGBoost, and LightGBM; simple benchmarks; expanding-window walk-forward evaluation; realistic execution timing; 0/5/10/25 bps transaction costs; predictive and financial metrics; yearly stability, regime analysis, statistical uncertainty, and robustness checks. All choices and claims will be documented as the project progresses.

## Run the foundation
Requires Python 3.12 or newer. From this directory:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --no-deps -e .
beyond-accuracy check-config --config configs/baseline.json
python -m unittest discover -s tests -v
```

The CLI validates settings only. It does not run a trading experiment. A misspelled or unsupported setting fails explicitly rather than silently changing assumptions.

## Layout
| Path | Responsibility |
| --- | --- |
| `src/beyond_accuracy/` | Shared Python implementation and CLI |
| `tests/` | Automated checks; financial invariants added with their implementations |
| `configs/` | Explicit experiment settings |
| `data/` | Local data snapshots; no data committed yet |
| `notebooks/` | Exploration and teaching, importing shared code |
| `results/` | Generated outputs and future experiment metadata |
| `paper/` | Research report based on real results |
| `docs/` | Learning log, concept checklist, and roadmap |

## Reproducibility
The current package has no runtime dependencies and pins its build backend. Future research phases will add a dependency lock and capture input data hashes, code versions, settings, seeds, and environment metadata. A random seed alone does not reproduce a study.

GitHub Actions installs the package and checks the tests and CLI on Python 3.12. The Dockerfile provides the same configuration-check entry point:

```bash
docker build -t beyond-accuracy .
docker run --rm beyond-accuracy
```

The container is a starting environment, not a claim of bit-for-bit reproducibility; image digests and the research environment will be fixed before experiments.

See [the learning log](docs/learning_log.md), [concept checklist](docs/concepts.md), and [roadmap](docs/roadmap.md).
