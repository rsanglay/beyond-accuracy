"""Annual time boundaries, common dates, and reserved-period independence."""
from dataclasses import replace
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np
import pandas as pd
import pandas_market_calendars as calendars

from beyond_accuracy.features import FeatureConfig, build_features
from beyond_accuracy.logistic import LogisticConfig
from beyond_accuracy.market_data import DataConfig
from beyond_accuracy.snapshots import save_snapshot
from beyond_accuracy.targets import build_targets
from beyond_accuracy.walk_forward import WalkForwardConfig, expanding_folds
from beyond_accuracy.walk_forward_run import run_walk_forward


def fixture():
    dates = calendars.get_calendar('NYSE').valid_days('2018-01-01', '2021-12-31').tz_localize(None)
    values = 100 + np.arange(len(dates)) * .01 + np.sin(np.arange(len(dates)))
    bars = pd.DataFrame({c: values for c in ['Open', 'High', 'Low', 'Close', 'Adj Close']}, index=dates)
    bars.index.name = 'Date'
    bars['Volume'] = 100
    bars['Dividends'] = bars['Stock Splits'] = 0.
    config = WalkForwardConfig('2018-01-01', 2019, 2020, '2021-01-01', 10, 2)
    feature_config = FeatureConfig((1,), (2,), (3,), (3,), 2, (2,))
    return bars, config, feature_config


def inputs():
    bars, config, feature_config = fixture()
    bars = bars.loc[bars.index < config.reserved_start]
    features = build_features(bars, feature_config)
    features = features[[c for c in features if not c.endswith('_diagnostic')]]
    return features, build_targets(bars['Adj Close']), config


class WalkForwardTests(unittest.TestCase):
    def test_expanding_history_and_unknown_boundary_exclusion(self):
        features, targets, config = inputs()
        first, second = expanding_folds(features, targets, config)
        self.assertEqual(first.training_sessions[0], second.training_sessions[0])
        self.assertTrue(first.training_sessions.isin(second.training_sessions).all())
        self.assertGreater(len(second.training_sessions), len(first.training_sessions))
        for fold in (first, second):
            self.assertTrue((targets.loc[fold.training_sessions, 'outcome_session'] <= fold.fit_after_session).all())
            self.assertNotIn(fold.fit_after_session, fold.training_sessions)
            self.assertEqual(fold.unavailable_training_labels, 1)
            self.assertTrue((fold.test_sessions.year == fold.test_year).all())
            self.assertTrue(fold.training_sessions.intersection(fold.test_sessions).empty)

    def test_test_labels_do_not_select_prediction_dates(self):
        features, targets, config = inputs()
        folds = expanding_folds(features, targets, config)
        self.assertIn(features.index[-1], folds[-1].test_sessions)
        self.assertTrue(pd.isna(targets.target_up.iloc[-1]))
        altered = targets.copy()
        known = altered.target_up.notna()
        altered.loc[known, 'target_up'] = 1 - altered.loc[known, 'target_up']
        changed = expanding_folds(features, altered, config)
        for before, after in zip(folds, changed):
            self.assertTrue(before.training_sessions.equals(after.training_sessions))
            self.assertTrue(before.test_sessions.equals(after.test_sessions))

    def test_missing_features_exclude_same_date_for_all_methods(self):
        features, targets, config = inputs()
        day = features.index[features.index.year == 2019][10]
        features.loc[day, 'rsi_2'] = np.nan
        self.assertNotIn(day, expanding_folds(features, targets, config)[0].test_sessions)

    def test_misaligned_or_leaking_inputs_rejected(self):
        features, targets, config = inputs()
        with self.assertRaises(ValueError):
            expanding_folds(features, targets.iloc[:-1], config)
        for name in ['target_up', 'next_return', 'outcome_session', 'sma_3_diagnostic']:
            with self.subTest(name=name), self.assertRaises(ValueError):
                expanding_folds(features.assign(**{name: 0}), targets, config)
        broken = targets.copy()
        broken.loc[broken.index[0], 'outcome_session'] = broken.index[0]
        with self.assertRaises(ValueError):
            expanding_folds(features, broken, config)

    def test_insufficient_history_and_overlapping_reserved_period_rejected(self):
        features, targets, config = inputs()
        with self.assertRaises(ValueError):
            expanding_folds(features, targets, replace(config, minimum_training_rows=10000))
        with self.assertRaises(ValueError):
            replace(config, reserved_start='2020-01-01')

    def test_current_test_prices_cannot_change_earlier_fold_training(self):
        features, targets, config = inputs()
        before = expanding_folds(features, targets, config)[0]
        changed = features.copy()
        changed.loc[changed.index.year >= 2019] *= 100
        after = expanding_folds(changed, targets, config)[0]
        self.assertTrue(before.training_sessions.equals(after.training_sessions))
        pd.testing.assert_frame_equal(features.loc[before.training_sessions], changed.loc[after.training_sessions])

    def test_runner_reserved_data_independence_and_common_predictions(self):
        bars, config, feature_config = fixture()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            outputs = []
            for multiplier in [1, 10]:
                changed = bars.copy()
                changed.loc[changed.index >= config.reserved_start, ['Open','High','Low','Close','Adj Close']] *= multiplier
                snapshot = save_snapshot(changed, DataConfig('SPY', '2018-01-01', '2022-01-01'), root/'data')
                run = run_walk_forward(snapshot, feature_config, config, root/'runs',
                                       LogisticConfig(1., 2000, 1e-6, .5, 42))
                predictions = pd.read_csv(run/'predictions.csv', index_col='Date', parse_dates=True)
                outcomes = pd.read_csv(run/'outcomes.csv', index_col='Date', parse_dates=True)
                self.assertTrue((predictions.index < config.reserved_start).all())
                self.assertFalse(predictions.isna().any().any())
                self.assertTrue(predictions.logistic_probability_up.between(0, 1).all())
                folds = json.loads((run/'folds.json').read_text())
                self.assertTrue(all(f['logistic']['converged'] for f in folds))
                self.assertTrue(outcomes.index.equals(predictions.index))
                self.assertFalse(outcomes.eligible_for_scoring.iloc[-1])
                outputs.append((predictions, outcomes))
            pd.testing.assert_frame_equal(outputs[0][0], outputs[1][0])
            pd.testing.assert_frame_equal(outputs[0][1], outputs[1][1])
