"""Benchmark rules, training-label availability, and missing-input behaviour."""
import unittest

import numpy as np
import pandas as pd

from beyond_accuracy.benchmarks import MajorityBenchmark, predict_momentum, predict_previous_direction
from beyond_accuracy.benchmark_demo import benchmark_demo


def training(labels):
    sessions = pd.bdate_range('2020-01-02', periods=len(labels) + 1)
    return pd.DataFrame({'target_up': pd.array(labels, dtype='Int64'),
                         'outcome_session': sessions[1:]}, index=sessions[:-1])


class BenchmarkTests(unittest.TestCase):
    def test_training_majority_stays_positive_with_negative_test_majority(self):
        targets = training([1] * 6 + [0] * 4)
        cutoff = targets.outcome_session.iloc[-1]
        model = MajorityBenchmark.fit(targets, fit_after_session=cutoff)
        sessions = pd.bdate_range(cutoff, periods=10)
        predictions = model.predict(sessions)
        unseen_outcomes = pd.Series([1] * 4 + [0] * 6, index=sessions)
        self.assertTrue((predictions == 1).all())
        self.assertEqual(int((predictions == unseen_outcomes).sum()), 4)
        targets['target_up'] = 0  # Fitted state must not reference a mutable training frame.
        pd.testing.assert_series_equal(predictions, model.predict(sessions))

    def test_nonpositive_majority_and_tie_policy(self):
        for labels in [[0, 0, 1], [0, 1], [0, 0]]:
            targets = training(labels)
            model = MajorityBenchmark.fit(targets, fit_after_session=targets.outcome_session.iloc[-1])
            self.assertEqual(model.predicted_class, 0)

    def test_future_training_outcomes_rejected(self):
        targets = training([1, 0, 1])
        with self.assertRaisesRegex(ValueError, 'unavailable'):
            MajorityBenchmark.fit(targets, fit_after_session=targets.index[-1])

    def test_same_session_outcome_is_invalid(self):
        targets = training([1, 0])
        targets['outcome_session'] = targets.index
        with self.assertRaisesRegex(ValueError, 'follow'):
            MajorityBenchmark.fit(targets, fit_after_session=targets.index[-1])

    def test_unknown_empty_and_invalid_labels_rejected(self):
        for labels in [[1, pd.NA], [], [1, 2]]:
            with self.subTest(labels=labels), self.assertRaises(ValueError):
                MajorityBenchmark.fit(training(labels), fit_after_session=pd.Timestamp('2020-02-01'))

    def test_cannot_predict_before_fit_but_after_close_same_session_allowed(self):
        targets = training([1, 1, 0])
        cutoff = targets.outcome_session.iloc[-1]
        model = MajorityBenchmark.fit(targets, fit_after_session=cutoff)
        with self.assertRaisesRegex(ValueError, 'earlier'):
            model.predict(pd.DatetimeIndex([targets.index[0]]))
        self.assertEqual(model.predict(pd.DatetimeIndex([cutoff])).iloc[0], 1)

    def test_latest_direction_uses_current_not_extra_lag(self):
        features = pd.DataFrame({'return_current': [.02, -.01, 0., np.nan],
                                 'return_lag_1': [-.02, .01, .03, .02]},
                                index=pd.bdate_range('2020-01-02', periods=4))
        result = predict_previous_direction(features)
        self.assertEqual(result.iloc[:3].tolist(), [1, 0, 0])
        self.assertTrue(pd.isna(result.iloc[-1]))

    def test_rules_can_disagree_and_ignore_outcome_columns(self):
        features = pd.DataFrame({'return_current': [-.01], 'momentum_5': [.05], 'target_up': [0]},
                                index=pd.DatetimeIndex(['2020-01-02']))
        self.assertEqual(predict_previous_direction(features).iloc[0], 0)
        before = predict_momentum(features, window=5)
        self.assertEqual(before.iloc[0], 1)
        features['target_up'] = 1
        pd.testing.assert_series_equal(before, predict_momentum(features, window=5))

    def test_momentum_preserves_unknown_and_flat_is_nonpositive(self):
        features = pd.DataFrame({'momentum_5': [np.nan, 0., -.05, .05]},
                                index=pd.bdate_range('2020-01-02', periods=4))
        result = predict_momentum(features, window=5)
        self.assertTrue(pd.isna(result.iloc[0]))
        self.assertEqual(result.iloc[1:].tolist(), [0, 0, 1])

    def test_future_features_cannot_change_earlier_predictions(self):
        features = pd.DataFrame({'return_current': [.01, -.02, .03], 'momentum_5': [.05, .04, -.01]},
                                index=pd.bdate_range('2020-01-02', periods=3))
        original = features.copy(deep=True)
        for rule in [predict_previous_direction, lambda f: predict_momentum(f, window=5)]:
            before = rule(features)
            changed = features.copy()
            changed.iloc[-1] = [.99, .99]
            pd.testing.assert_series_equal(before.iloc[:-1], rule(changed).iloc[:-1])
        pd.testing.assert_frame_equal(features, original)

    def test_bad_direction_input_and_config_rejected(self):
        sessions = pd.bdate_range('2020-01-02', periods=2)
        for values in [[np.inf, 0.], [-1.1, 0.], ['up', 'down']]:
            with self.subTest(values=values), self.assertRaises(ValueError):
                predict_previous_direction(pd.DataFrame({'return_current': values}, index=sessions))
        for window in [True, 0, -1, 1.5]:
            with self.subTest(window=window), self.assertRaises(ValueError):
                predict_momentum(pd.DataFrame(index=sessions), window=window)
        with self.assertRaises(ValueError):
            predict_momentum(pd.DataFrame(index=sessions), window=5)

    def test_demo_is_explicitly_synthetic(self):
        result = benchmark_demo()
        self.assertIn('Synthetic', result['kind'])
        self.assertEqual([row['majority'] for row in result['rows']], [1, 1, 1])
        self.assertEqual([row['previous_direction'] for row in result['rows']], [1, 0, 0])
        self.assertEqual([row['momentum_5'] for row in result['rows']], [1, 1, 0])
