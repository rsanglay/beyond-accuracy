"""Simple classification references; predictions are not trading positions."""
from dataclasses import dataclass

import numpy as np
import pandas as pd


def _session_index(index: pd.Index) -> None:
    if (not isinstance(index, pd.DatetimeIndex) or index.hasnans
            or index.tz is not None or not index.equals(index.normalize())
            or not index.is_unique or not index.is_monotonic_increasing):
        raise ValueError("Expected unique chronological timezone-naive session dates")


def _session(value: pd.Timestamp) -> pd.Timestamp:
    result = pd.Timestamp(value)
    if pd.isna(result) or result.tz is not None or result != result.normalize():
        raise ValueError("Expected a timezone-naive session date")
    return result


@dataclass(frozen=True)
class MajorityBenchmark:
    """Frozen rule fitted only from known training outcomes.

    fit_after_session means after that session's final data is available, never
    midnight. Phase 6 will construct the training slice; this class checks that
    its supplied labels are already available. Ties deterministically choose 0.
    """
    predicted_class: int
    training_rows: int
    fit_after_session: pd.Timestamp

    @classmethod
    def fit(cls, training_targets: pd.DataFrame, *, fit_after_session: pd.Timestamp):
        _session_index(training_targets.index)
        cutoff = _session(fit_after_session)
        if training_targets.empty or not {"target_up", "outcome_session"}.issubset(training_targets.columns):
            raise ValueError("Supply nonempty training targets with outcome sessions")
        labels = training_targets["target_up"]
        if labels.isna().any() or not labels.isin([0, 1]).all():
            raise ValueError("Training labels must be known binary outcomes; unknowns cannot be filled")
        outcomes = pd.DatetimeIndex(training_targets["outcome_session"])
        _session_index(outcomes)
        if (outcomes <= training_targets.index).any():
            raise ValueError("Each outcome must follow its feature session")
        if (outcomes > cutoff).any():
            raise ValueError("Training contains outcomes unavailable at the fit cutoff")
        positive = int((labels == 1).sum())
        return cls(int(positive > len(labels) - positive), len(labels), cutoff)

    def predict(self, sessions: pd.DatetimeIndex) -> pd.Series:
        _session_index(sessions)
        if (sessions < self.fit_after_session).any():
            raise ValueError("Cannot apply a fitted model to earlier prediction sessions")
        return pd.Series(self.predicted_class, index=sessions, dtype="Int64", name="majority")


def _direction(values: pd.Series, name: str) -> pd.Series:
    _session_index(values.index)
    if not pd.api.types.is_numeric_dtype(values.dtype):
        raise ValueError("Direction inputs must be numeric returns")
    if np.isinf(values.to_numpy(dtype=float, na_value=np.nan)).any():
        raise ValueError("Direction inputs cannot contain infinity")
    if (values.dropna() < -1).any():
        raise ValueError("Simple returns cannot be less than -1")
    return values.gt(0).astype("Int64").mask(values.isna()).rename(name)


def predict_previous_direction(features: pd.DataFrame) -> pd.Series:
    """After today's close, predict next direction from today's known return.

    return_current is the most recent return relative to the future outcome;
    return_lag_1 would introduce an unintended extra session of delay.
    """
    if "return_current" not in features:
        raise ValueError("Previous-direction benchmark requires return_current")
    return _direction(features["return_current"], "previous_direction")


def predict_momentum(features: pd.DataFrame, *, window: int) -> pd.Series:
    """Predict positive iff the supplied trailing window return is positive."""
    if type(window) is not int or window < 1:
        raise ValueError("Momentum window must be a positive integer")
    column = f"momentum_{window}"
    if column not in features:
        raise ValueError(f"Momentum benchmark requires {column}")
    return _direction(features[column], f"momentum_{window}")
