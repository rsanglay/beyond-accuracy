"""Forest reproducibility, tree limits, interactions, and time boundaries."""
from dataclasses import replace
import unittest
import numpy as np
import pandas as pd
from beyond_accuracy.random_forest import ForestConfig, fit_predict_forest


def example():
    dates = pd.bdate_range('2018-01-02', periods=86)
    # Synthetic interaction: positive momentum predicts up only with low volatility.
    values = np.tile([[-1., 0.], [-1., 1.], [1., 0.], [1., 1.]], (20, 1))
    x = pd.DataFrame(values, index=dates[:80], columns=['momentum_5', 'volatility_5'])
    y = pd.DataFrame({'target_up': np.tile([0, 1, 1, 0], 20), 'outcome_session': dates[1:81]}, index=x.index)
    test = pd.DataFrame(values[:4], index=dates[81:85], columns=x.columns)
    return x, y, test, dates[80], ForestConfig(40, 4, 3, 'sqrt', .5, 42)


def run(x, y, test, cutoff, config):
    return fit_predict_forest(x, y, test, fit_after_session=cutoff, config=config)


class ForestTests(unittest.TestCase):
    def test_interaction_probabilities_and_tree_limits(self):
        predictions, audit = run(*example())
        self.assertEqual(predictions.forest_class.tolist(), [0, 1, 1, 0])
        self.assertTrue(predictions.forest_probability_up.between(0, 1).all())
        self.assertEqual(audit['tree_count'], 40)
        self.assertLessEqual(max(audit['tree_depths']), 4)
        self.assertGreaterEqual(min(audit['tree_minimum_unique_leaf_samples']), 3)
        self.assertFalse(audit['oob_score'])

    def test_fixed_seed_reproduces_predictions_and_fitted_state(self):
        first, audit = run(*example())
        second, other = run(*example())
        pd.testing.assert_frame_equal(first, second)
        self.assertEqual(audit['model_fingerprint_sha256'], other['model_fingerprint_sha256'])

    def test_changed_test_features_cannot_change_fitted_forest(self):
        x, y, test, cutoff, config = example()
        original = x.copy()
        _, audit = run(x, y, test, cutoff, config)
        _, other = run(x, y, test * 100, cutoff, config)
        self.assertEqual(audit['model_fingerprint_sha256'], other['model_fingerprint_sha256'])
        pd.testing.assert_frame_equal(x, original)

    def test_threshold_does_not_change_fitted_state_or_probability(self):
        x, y, test, cutoff, config = example()
        first, audit = run(x, y, test, cutoff, config)
        second, other = run(x, y, test, cutoff, replace(config, threshold=.99))
        pd.testing.assert_series_equal(first.forest_probability_up, second.forest_probability_up)
        self.assertEqual(audit['model_fingerprint_sha256'], other['model_fingerprint_sha256'])
        self.assertEqual(second.forest_class.tolist(), (second.forest_probability_up >= .99).astype(int).tolist())

    def test_unknown_single_class_and_unavailable_labels_rejected(self):
        x, y, test, cutoff, config = example()
        unknown = y.copy(); unknown.iloc[0, 0] = np.nan
        future = y.copy(); future.iloc[-1, 1] = test.index[-1]
        for bad in [unknown, y.assign(target_up=1), future]:
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                run(x, bad, test, cutoff, config)

    def test_leaking_columns_bad_order_and_nonfinite_input_rejected(self):
        x, y, test, cutoff, config = example()
        with self.assertRaises(ValueError):
            run(x.assign(target_up=0), y, test.assign(target_up=0), cutoff, config)
        with self.assertRaises(ValueError):
            run(x, y, test[test.columns[::-1]], cutoff, config)
        invalid = test.copy(); invalid.iloc[0, 0] = np.inf
        with self.assertRaises(ValueError):
            run(x, y, invalid, cutoff, config)

    def test_invalid_config(self):
        config = example()[-1]
        for values in [{'n_estimators': 0}, {'max_depth': None}, {'min_samples_leaf': True},
                       {'max_features': 'all'}, {'threshold': np.nan}, {'random_seed': -1}]:
            with self.subTest(values=values), self.assertRaises(ValueError):
                replace(config, **values)
