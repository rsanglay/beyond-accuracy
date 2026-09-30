# Phase 7b — Random Forest

## Meaning

A decision tree learns conditional feature thresholds. It can represent momentum behaving differently under high and low volatility without manually adding interaction columns. A forest fits many trees on bootstrap samples (training rows drawn with replacement), with random feature subsets considered at splits. Scikit-learn averages the trees' class probability estimates; it is not merely a count of hard class votes.

The output estimates probability of a positive next-session return. It is not expected percentage gain, guaranteed probability calibration, or a trading position. A threshold of 0.5 maps probability >= 0.5 to class 1. The same convention is used by Logistic Regression.

## Fixed initial settings

`configs/random_forest.json`: 200 trees, max_depth=5, min_samples_leaf=20, max_features=sqrt, threshold=0.5, random_seed=42. Bootstrap is enabled; criterion is gini; class weighting, warm start, and out-of-bag scoring are disabled; n_jobs=1 keeps resource use bounded. Settings were fixed before inspecting test performance. They are starting assumptions, not demonstrated optima.

Tree depth and leaf-size limits reduce the capacity to fit isolated observations but do not eliminate overfitting. More trees do not supply new independent market data. Bootstrap samples draw only from each permitted annual training slice. They do not replace chronological evaluation, and out-of-bag scores are not used as a substitute for walk-forward results. Daily observations remain dependent; this bootstrap is an algorithmic training mechanism, not a statistical confidence-interval method.

## Timing and isolation

Every annual fold fits a new forest using the same complete-feature training/test dates as the other methods, with no standardisation. Target/diagnostic columns, unknown or unavailable labels, misaligned schemas, and nonfinite values are rejected by shared `model_inputs.py` checks, now also used by Logistic Regression. Both classes are required. Test labels are never passed to fitting.

Ordinary threshold trees generally do not require scaling: monotonic standardisation preserves order, though finite-precision implementations can introduce small differences. No preprocessing is learned for this forest.

## Run and audit

Append `--forest-config configs/random_forest.json` to the walk-forward command. It can be used alone or alongside `--logistic-config configs/logistic.json`. The runner adds forest_probability_up and forest_class to the existing prediction dates, keeping outcomes separate. Reserved 2024–2025 remains excluded.

Per-fold metadata records training count, ordered columns, class order, bootstrap/settings, tree count, individual depths/leaf counts, minimum distinct training samples in each tree's leaves, and fit/inference time. A deterministic fingerprint of fitted tree arrays detects changed fitted state within the same environment; it is not a portable model serialisation. Config, code, data hashes, and pinned dependencies remain necessary for reproduction.

No performance ranking, tuning, feature-importance claim, or trading conclusion is made. We will evaluate those only after the relevant checkpoints.

## Local checks

Tests cover a synthetic conditional interaction, deterministic seed, valid probability/threshold mapping, tree limits, unchanged fitted fingerprints when test features change, unavailable/unknown labels, invalid inputs, and reserved-period independence. End-to-end runs confirm existing benchmark and Logistic Regression predictions are unchanged.

Primary reference: [scikit-learn RandomForestClassifier](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.RandomForestClassifier.html).
