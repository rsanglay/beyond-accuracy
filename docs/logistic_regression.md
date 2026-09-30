# Phase 7a — Logistic Regression

## Model and interpretation

The model estimates P(next adjusted close-to-close return > 0 | features). A probability of 0.58 means an estimated 58% probability of class 1, not a 58% price gain. At the configured threshold 0.50, probabilities >= 0.50 become class 1; smaller probabilities become class 0 (nonpositive). These are classification decisions, not trade instructions or calibrated guarantees.

A learned linear score z = intercept + sum(coefficient * scaled_feature) passes through sigmoid(z) = 1/(1+exp(-z)). Holding other inputs fixed, a positive coefficient increases estimated positive-class probability. Coefficients express conditional associations rather than causation, and correlated features can make their interpretation unstable.

## Training-only preprocessing

Every annual fold gets a new scikit-learn Pipeline containing StandardScaler and LogisticRegression. Only the explicit training rows are passed to fit. Test rows are passed only to predict_proba. Scaling settings and coefficients remain fixed throughout the test year. The next year fits a fresh pipeline on expanded training history.

StandardScaler uses (x - training_mean) / training_scale, with variance divisor n (`ddof=0`); a constant training feature uses scale 1. This differs from the sample standard deviation (`ddof=1`) used by our volatility feature. It is a documented preprocessing convention, not a replacement of that financial feature's formula.

## Fixed initial settings

`configs/logistic.json` records C=1, max_iter=2000, tolerance=1e-6, probability threshold=0.5, and seed=42. The solver is lbfgs, with an intercept, no class weighting, and L2 regularisation (`l1_ratio=0` in pinned scikit-learn 1.9.1). C is inverse regularisation strength: smaller C increases the penalty. These settings were not tuned on development test results. The seed is recorded for consistency; this solver is not using a random training split.

A convergence warning fails the run before artifacts are saved. A fold with only one known class is rejected rather than silently replaced by another model. Input schemas must match, training labels must be aligned and available, features must be finite, and target/diagnostic columns are forbidden. Test outcomes are not an argument to the fitting function.

## Run and audit

```bash
beyond-accuracy walk-forward \
  --snapshot data/snapshots/<snapshot-id> \
  --features-config configs/features.json \
  --config configs/walk_forward.json \
  --logistic-config configs/logistic.json
```

Without the optional argument, the existing benchmark-only behaviour is retained. With it, predictions.csv adds logistic_probability_up and logistic_class on exactly the benchmark dates. Fold metadata records scaling means/scales/variances, ordered feature names, coefficients, intercept, class order, iteration count, and observed fit/inference seconds. Timing is machine-dependent and is not a speed benchmark. Each run records model settings, dependencies, source/output hashes, and code state. No unsafe executable model serialisation is used.

The five development folds remain 2019–2023; reserved 2024–2025 prices remain excluded before development feature/target construction. No accuracy, calibration, profitability, or model superiority claim is made here. Those require later metrics and interpretation checkpoints.

## Local validation

Tests verify training-only means/variances, unchanged fitted parameters when test features change, finite probabilities with correct class mapping, threshold changes without refitting effects, constant-feature handling, label availability, aligned schemas, both-class requirements, nonconvergence failure, and reserved-period independence through the complete runner.

## Primary references

- [scikit-learn LogisticRegression](https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LogisticRegression.html)
- [scikit-learn leakage and preprocessing pitfalls](https://scikit-learn.org/stable/common_pitfalls.html)
- [scikit-learn StandardScaler](https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.StandardScaler.html)
