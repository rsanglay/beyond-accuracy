# Phase 6 — Expanding annual validation

## Initial schedule

Configuration is explicit in `configs/walk_forward.json`: initial history starts 2010-01-01; annual development test years are 2019–2023; 2024–2025 is reserved for a later final evaluation. These choices were made before generating benchmark development predictions, not by selecting the best accuracy. No performance metrics or tuning are introduced in this phase.

| Test year | Nominal training history |
| --- | --- |
| 2019 | 2010–2018 |
| 2020 | 2010–2019 |
| 2021 | 2010–2020 |
| 2022 | 2010–2021 |
| 2023 | 2010–2022 |

Warm-up observations and unavailable labels reduce the actual training rows. Training starts at the same first complete-feature session and grows. Fitting happens once per year after the last preceding session's final data is available. A feature row from that final session is excluded from training because its next-session target is not yet known. Known outcomes with outcome_session <= fitting session may be used under this after-close contract. The prediction date is also an after-close feature date, not a trade execution timestamp.

## Input and output contracts

The runner verifies the local snapshot, then removes reserved-period prices BEFORE feature or target construction. The final development feature date therefore has an unknown target; its prediction is retained and its eligible_for_scoring flag is false. Target construction does not reach across the reserved boundary. Snapshot integrity verification reads the original snapshot, including its existing history, but no reserved outcomes enter fitting or reports.

All candidate feature columns must be complete for an observation to be used by any benchmark. Diagnostic price columns and target columns are forbidden inputs. Splitter indexes must match exactly, target outcomes must identify the next input session, and labels must be binary or unknown with matching missing outcome dates. Every benchmark predicts the same test dates. Target values do not determine which test feature dates are selected.

Current snapshots are historical data vintages, not point-in-time archives. This splitter cannot eliminate vendor revision risk or guarantee the caller has supplied causally constructed features. Tests address chronological alignment and known input contracts.

```bash
beyond-accuracy walk-forward \
  --snapshot data/snapshots/<snapshot-id> \
  --features-config configs/features.json \
  --config configs/walk_forward.json
```

Creates a unique local run with `predictions.csv`, separate `outcomes.csv`, `folds.json` (including exact train/test dates), and `metadata.json` (configuration, feature list, source/output hashes, versions, commit and dirty state). Outcomes are for later evaluation, not model inputs. Fold manifests permit auditing excluded labels and training cutoffs. Generated files remain outside Git.

## Preprocessing and model boundary

The three benchmarks do not need learned preprocessing, so none is fitted here. When Logistic Regression is added, its learned preprocessing must be instantiated and fitted inside each fold on training features only, then used unchanged on that fold's test features. This phase does not implement or claim to validate a scaler or model-selection pipeline. Hyperparameter tuning must use an inner chronological development procedure rather than these test outcomes.

Development years may inform later research choices; repeatedly inspecting them does not preserve a final untouched test. Keep reserved years separate until the final methodology is frozen. The reserved cutoff is configurable but should not be moved in response to results. In later folds it is legitimate to train on outcomes from previous test years once they are historical; it is not legitimate to revise predictions already made.

## Tests

Tests cover expanding history, training/test separation, unavailable boundary labels, common complete-feature dates, preserved unknown test labels, strict alignment, forbidden columns, minimum sample size, future-feature independence of prior training, and independence from reserved-period price changes. No cloud workflows are required.
