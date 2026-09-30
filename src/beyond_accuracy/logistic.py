"""Train-only scaling and regularised binary Logistic Regression."""
from dataclasses import dataclass, fields
import json
from pathlib import Path
from time import perf_counter
import warnings

import numpy as np
import pandas as pd
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from beyond_accuracy.model_inputs import validate_model_inputs


@dataclass(frozen=True)
class LogisticConfig:
    C: float
    max_iter: int
    tolerance: float
    threshold: float
    random_seed: int

    def __post_init__(self):
        for name in ('C', 'tolerance', 'threshold'):
            value = getattr(self, name)
            if type(value) not in (int, float) or not np.isfinite(value) or value <= 0:
                raise ValueError(f'{name} must be positive and finite')
        if self.threshold >= 1:
            raise ValueError('threshold must be below 1')
        if type(self.max_iter) is not int or self.max_iter < 1:
            raise ValueError('max_iter must be a positive integer')
        if type(self.random_seed) is not int or not 0 <= self.random_seed <= 2**32 - 1:
            raise ValueError('random_seed must be a valid nonnegative 32-bit integer')


def load_logistic_config(path: Path) -> LogisticConfig:
    data = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data, dict) or set(data) != {f.name for f in fields(LogisticConfig)}:
        raise ValueError('Logistic configuration fields do not match the required schema')
    return LogisticConfig(**data)


def fit_predict_logistic(train_x: pd.DataFrame, training_targets: pd.DataFrame,
                         test_x: pd.DataFrame, *, fit_after_session: pd.Timestamp,
                         config: LogisticConfig) -> tuple[pd.DataFrame, dict]:
    """Fit a fresh pipeline using only explicit training inputs; never accept test labels."""
    labels = validate_model_inputs(train_x, training_targets, test_x, fit_after_session)
    pipeline = Pipeline([
        ('scale', StandardScaler()),
        ('model', LogisticRegression(C=config.C, l1_ratio=0.0, solver='lbfgs',
                                     max_iter=config.max_iter, tol=config.tolerance,
                                     random_state=config.random_seed, class_weight=None,
                                     fit_intercept=True, warm_start=False)),
    ])
    start = perf_counter()
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error', ConvergenceWarning)
            pipeline.fit(train_x, labels.astype(int))
    except ConvergenceWarning as exc:
        raise ValueError('Logistic Regression did not converge; no predictions were saved') from exc
    fit_seconds = perf_counter() - start
    start = perf_counter()
    model, scaler = pipeline.named_steps['model'], pipeline.named_steps['scale']
    positive_column = list(model.classes_).index(1)
    probabilities = pipeline.predict_proba(test_x)[:, positive_column]
    inference_seconds = perf_counter() - start
    if not np.isfinite(probabilities).all() or ((probabilities < 0) | (probabilities > 1)).any():
        raise ValueError('Invalid predicted probabilities')
    predictions = pd.DataFrame({
        'logistic_probability_up': probabilities,
        'logistic_class': (probabilities >= config.threshold).astype(int),
    }, index=test_x.index)
    audit = {
        'training_rows': len(train_x), 'feature_columns': train_x.columns.tolist(),
        'scaler_mean': scaler.mean_.tolist(), 'scaler_scale': scaler.scale_.tolist(),
        'scaler_variance': scaler.var_.tolist(), 'scaler_ddof': 0,
        'coefficients': model.coef_[0].tolist(), 'intercept': float(model.intercept_[0]),
        'iterations': model.n_iter_.tolist(), 'classes': model.classes_.tolist(),
        'solver': 'lbfgs', 'regularisation': 'L2', 'class_weight': None,
        'fit_seconds': fit_seconds, 'inference_seconds': inference_seconds,
        'converged': True,
    }
    return predictions, audit
