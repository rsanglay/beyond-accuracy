"""Expanding annual folds with explicit after-close label availability."""
from dataclasses import dataclass, fields
import json
from pathlib import Path

import numpy as np
import pandas as pd

from beyond_accuracy.benchmarks import _session_index


@dataclass(frozen=True)
class WalkForwardConfig:
    training_start: str
    first_test_year: int
    last_test_year: int
    reserved_start: str
    minimum_training_rows: int
    momentum_window: int

    def __post_init__(self):
        for name in ('first_test_year', 'last_test_year', 'minimum_training_rows', 'momentum_window'):
            value = getattr(self, name)
            if type(value) is not int or value < 1:
                raise ValueError(f'{name} must be a positive integer')
        for value in (self.training_start, self.reserved_start):
            if not isinstance(value, str) or pd.Timestamp(value).strftime('%Y-%m-%d') != value:
                raise ValueError('Dates must be YYYY-MM-DD')
        if not 1900 <= self.first_test_year <= self.last_test_year <= 2200:
            raise ValueError('Invalid test years')
        if pd.Timestamp(self.training_start) >= pd.Timestamp(self.first_test_year, 1, 1):
            raise ValueError('Training must begin before testing')
        if pd.Timestamp(self.last_test_year + 1, 1, 1) > pd.Timestamp(self.reserved_start):
            raise ValueError('Development test years overlap the reserved period')


def load_walk_forward_config(path: Path) -> WalkForwardConfig:
    payload = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(payload, dict) or set(payload) != {f.name for f in fields(WalkForwardConfig)}:
        raise ValueError('Walk-forward config fields do not match the required schema')
    return WalkForwardConfig(**payload)


@dataclass(frozen=True)
class AnnualFold:
    test_year: int
    fit_after_session: pd.Timestamp
    training_sessions: pd.DatetimeIndex
    test_sessions: pd.DatetimeIndex
    unavailable_training_labels: int


def expanding_folds(features: pd.DataFrame, targets: pd.DataFrame,
                    config: WalkForwardConfig) -> list[AnnualFold]:
    """Use identical complete-feature dates for all methods; retain unknown test labels.

    Targets must have been built on the same session index as features. Dates mean
    final data available after close. No fitted transforms are performed here.
    """
    _session_index(features.index)
    if features.empty or len(features.columns) == 0 or not features.columns.is_unique:
        raise ValueError('Require nonempty feature data with unique columns')
    if not features.index.equals(targets.index):
        raise ValueError('Feature and target session indexes must match exactly')
    if any(c in {'target_up', 'next_return', 'outcome_session'} or c.endswith('_diagnostic') for c in features.columns):
        raise ValueError('Targets and diagnostic prices are forbidden model inputs')
    if np.isinf(features.to_numpy(dtype=float, na_value=np.nan)).any():
        raise ValueError('Features contain infinity')
    if not {'target_up', 'outcome_session'}.issubset(targets.columns):
        raise ValueError('Missing target columns')
    labels, outcomes = targets.target_up, targets.outcome_session
    if not labels.dropna().isin([0, 1]).all() or not labels.isna().equals(outcomes.isna()):
        raise ValueError('Labels must be binary and missing exactly when outcome session is missing')
    expected = pd.Series(features.index, index=features.index).shift(-1)
    if not outcomes.equals(expected.rename(outcomes.name)):
        raise ValueError('Outcome sessions must identify the next observation, with a missing final row')
    complete = features.notna().all(axis=1)
    start, reserved = pd.Timestamp(config.training_start), pd.Timestamp(config.reserved_start)
    folds = []
    for year in range(config.first_test_year, config.last_test_year + 1):
        boundary, end = pd.Timestamp(year, 1, 1), pd.Timestamp(year + 1, 1, 1)
        prior = features.index[(features.index >= start) & (features.index < boundary)]
        if prior.empty:
            raise ValueError(f'No prior sessions for {year}')
        cutoff = prior[-1]
        available = labels.notna() & outcomes.le(cutoff)
        train_pool = (features.index >= start) & (features.index <= cutoff) & complete
        train = features.index[train_pool & available]
        test = features.index[(features.index >= boundary) & (features.index < end)
                              & (features.index < reserved) & complete]
        if len(train) < config.minimum_training_rows or test.empty:
            raise ValueError(f'Insufficient training or testing rows for {year}')
        folds.append(AnnualFold(year, cutoff, train, test, int((train_pool & ~available).sum())))
    return folds
