"""Shared model-input and label-availability checks."""
import numpy as np
import pandas as pd
from beyond_accuracy.benchmarks import _session_index, _session


def validate_model_inputs(train_x: pd.DataFrame, training_targets: pd.DataFrame,
                          test_x: pd.DataFrame, fit_after_session: pd.Timestamp) -> pd.Series:
    cutoff = _session(fit_after_session)
    for frame in (train_x, test_x):
        _session_index(frame.index)
        if frame.empty or len(frame.columns) == 0 or not frame.columns.is_unique:
            raise ValueError('Require nonempty features with unique columns')
        if any(c in {'target_up', 'next_return', 'outcome_session'} or c.endswith('_diagnostic') for c in frame.columns):
            raise ValueError('Targets and diagnostic prices are forbidden model inputs')
        if not np.isfinite(frame.to_numpy(dtype=float)).all():
            raise ValueError('Model features must be complete and finite')
    if not train_x.columns.equals(test_x.columns):
        raise ValueError('Training and test feature columns must match in order')
    if not train_x.index.equals(training_targets.index):
        raise ValueError('Training features and targets must align exactly')
    if not {'target_up', 'outcome_session'}.issubset(training_targets.columns):
        raise ValueError('Training target columns missing')
    labels = training_targets.target_up
    if labels.isna().any() or set(labels.unique()) != {0, 1}:
        raise ValueError('Classifier requires known labels from both classes')
    outcomes = pd.DatetimeIndex(training_targets.outcome_session)
    _session_index(outcomes)
    if (outcomes <= train_x.index).any() or (outcomes > cutoff).any():
        raise ValueError('Training outcomes must follow features and be known by fitting')
    if (test_x.index < cutoff).any() or not train_x.index.intersection(test_x.index).empty:
        raise ValueError('Test dates must follow training and cannot precede fitting')
    return labels.astype(int)
