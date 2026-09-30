"""Training-only preprocessing, explicit schema, and probability checks."""
from dataclasses import replace
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd
from sklearn.exceptions import ConvergenceWarning

from beyond_accuracy.logistic import LogisticConfig, fit_predict_logistic


def example():
    dates = pd.bdate_range('2018-01-02', periods=13)
    train_x = pd.DataFrame({'momentum_5': [-3., -2., -1., 1., 2., 3., -2., 2.],
                            'rsi_14': [30., 40., 45., 55., 60., 70., 40., 60.]}, index=dates[:8])
    targets = pd.DataFrame({'target_up': [0, 0, 0, 1, 1, 1, 0, 1],
                            'outcome_session': dates[1:9]}, index=train_x.index)
    test_x = pd.DataFrame({'momentum_5': [-2., 0., 2.], 'rsi_14': [40., 50., 60.]}, index=dates[9:12])
    return train_x, targets, test_x, dates[8], LogisticConfig(1., 2000, 1e-6, .5, 42)


def run(x, y, test, cutoff, config):
    return fit_predict_logistic(x, y, test, fit_after_session=cutoff, config=config)


class LogisticTests(unittest.TestCase):
    def test_scaler_matches_training_only_and_prediction_does_not_refit(self):
        x, y, test, cutoff, config = example()
        before = x.copy()
        predictions, audit = run(x, y, test, cutoff, config)
        np.testing.assert_allclose(audit['scaler_mean'], x.mean())
        np.testing.assert_allclose(audit['scaler_variance'], x.var(ddof=0))
        shifted = test * 1000
        _, second = run(x, y, shifted, cutoff, config)
        for field in ['scaler_mean', 'scaler_scale', 'coefficients', 'intercept']:
            np.testing.assert_allclose(audit[field], second[field])
        pd.testing.assert_frame_equal(x, before)
        self.assertTrue(predictions.index.equals(test.index))

    def test_probability_direction_bounds_and_threshold(self):
        predictions, _ = run(*example())
        probabilities = predictions.logistic_probability_up
        self.assertTrue(probabilities.between(0, 1).all())
        self.assertLess(probabilities.iloc[0], probabilities.iloc[-1])
        self.assertEqual(predictions.logistic_class.tolist(), (probabilities >= .5).astype(int).tolist())

    def test_threshold_changes_classes_not_fit_or_probabilities(self):
        x, y, test, cutoff, config = example()
        first, audit = run(x, y, test, cutoff, config)
        second, other = run(x, y, test, cutoff, replace(config, threshold=.99))
        pd.testing.assert_series_equal(first.logistic_probability_up, second.logistic_probability_up)
        self.assertNotEqual(first.logistic_class.tolist(), second.logistic_class.tolist())
        self.assertEqual(audit['coefficients'], other['coefficients'])

    def test_single_class_unknown_or_future_labels_fail(self):
        x, y, test, cutoff, config = example()
        single = y.assign(target_up=1)
        unknown = y.copy(); unknown.loc[unknown.index[0], 'target_up'] = np.nan
        future = y.copy(); future.loc[future.index[-1], 'outcome_session'] = test.index[0]
        for bad in [single, unknown, future]:
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                run(x, bad, test, cutoff, config)

    def test_schema_alignment_and_leaking_columns_fail(self):
        x, y, test, cutoff, config = example()
        with self.assertRaises(ValueError):
            run(x, y, test[test.columns[::-1]], cutoff, config)
        with self.assertRaises(ValueError):
            run(x, y.iloc[::-1], test, cutoff, config)
        with self.assertRaises(ValueError):
            run(x.assign(target_up=y.target_up), y, test.assign(target_up=0), cutoff, config)

    def test_constant_feature_is_safe_and_has_unit_scale(self):
        x, y, test, cutoff, config = example()
        _, audit = run(x.assign(constant=5.), y, test.assign(constant=5.), cutoff, config)
        self.assertEqual(audit['scaler_scale'][-1], 1.)
        self.assertEqual(audit['coefficients'][-1], 0.)

    def test_nonconvergence_is_an_error(self):
        with patch('beyond_accuracy.logistic.Pipeline.fit', side_effect=ConvergenceWarning('not converged')):
            with self.assertRaisesRegex(ValueError, 'did not converge'):
                run(*example())

    def test_invalid_config(self):
        config = example()[-1]
        for updates in [{'C': 0}, {'C': np.inf}, {'threshold': 1}, {'max_iter': True}, {'random_seed': -1}]:
            with self.subTest(updates=updates), self.assertRaises(ValueError):
                replace(config, **updates)
