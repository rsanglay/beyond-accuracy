"""Hand-calculated examples, warm-up boundaries, and time-causality checks."""
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np
import pandas as pd

from beyond_accuracy.features import FeatureConfig, build_features, load_feature_config, wilder_rsi
from beyond_accuracy.feature_artifacts import prepare_features
from beyond_accuracy.market_data import DataConfig
from beyond_accuracy.snapshots import save_snapshot, sha256


def small_config():
    return FeatureConfig((1,), (2,), (3,), (3,), 2, (2,))


def example(prices, volume=None):
    return pd.DataFrame({"Adj Close": prices, "Volume": volume if volume is not None else [10.] * len(prices)},
                        index=pd.date_range("2020-01-01", periods=len(prices)))


class FeatureTests(unittest.TestCase):
    def test_taught_moving_average_momentum_and_lag(self):
        features = build_features(example([100., 102., 104., 108.]), small_config())
        self.assertAlmostEqual(features.sma_3_diagnostic.iloc[2], 102.)
        self.assertAlmostEqual(features.sma_3_diagnostic.iloc[3], 314 / 3)
        self.assertAlmostEqual(features.momentum_2.iloc[3], 108 / 102 - 1)
        self.assertAlmostEqual(features.return_lag_1.iloc[3], 104 / 102 - 1)

    def test_sample_volatility_known_returns(self):
        prices = 100 * np.cumprod([1., .97, 1.01, 1.05])
        result = build_features(example(prices), small_config())
        self.assertAlmostEqual(result.volatility_3.iloc[3], .04)

    def test_constant_returns_have_zero_volatility(self):
        result = build_features(example(100 * 1.02 ** np.arange(8)), small_config())
        np.testing.assert_allclose(result.volatility_3.iloc[3:], 0, atol=1e-14)

    def test_relative_volume_excludes_today(self):
        result = build_features(example([100., 101., 102.], [10., 10., 20.]), small_config())
        self.assertEqual(result.relative_volume_2.iloc[2], 2)

    def test_exact_first_valid_rows(self):
        config = FeatureConfig((1,), (5,), (5,), (5,), 14, (5,))
        bars = example(np.arange(100., 120.))
        result = build_features(bars, config)
        # Zero-based locations: row 5 is index 4, row 6 is index 5.
        first = {"return_current": 1, "return_lag_1": 2, "momentum_5": 5,
                 "sma_5_diagnostic": 4, "volatility_5": 5, "rsi_14": 14,
                 "relative_volume_5": 5}
        for column, location in first.items():
            with self.subTest(column=column):
                self.assertEqual(result[column].first_valid_index(), bars.index[location])

    def test_rsi_seed_and_next_recursive_update(self):
        # Changes +2,-1,+3; seed averages 1 and .5 => RSI 66 2/3.
        # Next averages 2 and .25 => RSI 88 8/9.
        result = wilder_rsi(pd.Series([100., 102., 101., 104.]), 2)
        self.assertTrue(result.iloc[:2].isna().all())
        self.assertAlmostEqual(result.iloc[2], 100 * 2 / 3)
        self.assertAlmostEqual(result.iloc[3], 100 * 2 / 2.25)

    def test_rsi_flat_gains_losses_and_equal_seed(self):
        for prices, expected in [([100., 100., 100.], 50), ([100., 101., 102.], 100),
                                 ([100., 99., 98.], 0), ([100., 102., 100.], 50)]:
            with self.subTest(prices=prices):
                self.assertEqual(wilder_rsi(pd.Series(prices), 2).iloc[-1], expected)

    def test_prefix_invariance_and_future_mutation(self):
        bars = example(100 + np.sin(np.arange(50)) * 4 + np.arange(50), np.arange(50) + 10.)
        original = bars.copy(deep=True)
        all_features = build_features(bars, small_config())
        for stop in [1, 2, 3, 10, 30]:
            with self.subTest(stop=stop):
                prefix = build_features(bars.iloc[:stop], small_config())
                pd.testing.assert_frame_equal(prefix, all_features.iloc[:stop])
        changed = bars.copy()
        changed.iloc[30:, 0] *= 10
        changed.iloc[30:, 1] *= 100
        pd.testing.assert_frame_equal(build_features(changed, small_config()).iloc[:30], all_features.iloc[:30])
        pd.testing.assert_frame_equal(bars, original)

    def test_uniform_price_rescaling_preserves_candidates(self):
        bars = example([100., 102., 101., 104., 103., 107.])
        rescaled = bars.copy()
        rescaled["Adj Close"] *= .5
        first, second = build_features(bars, small_config()), build_features(rescaled, small_config())
        candidate_columns = [c for c in first if not c.endswith("_diagnostic")]
        pd.testing.assert_frame_equal(first[candidate_columns], second[candidate_columns])
        np.testing.assert_allclose(second.sma_3_diagnostic, first.sma_3_diagnostic * .5, equal_nan=True)

    def test_zero_volume_baseline_stays_undefined(self):
        result = build_features(example([100., 101., 102.], [0., 0., 20.]), small_config())
        self.assertTrue(np.isnan(result.relative_volume_2.iloc[-1]))
        self.assertFalse(np.isinf(result.to_numpy()).any())

    def test_missing_input_and_bad_order_rejected(self):
        bad = example([100., np.nan, 102.])
        for bars in [bad, example([100., 101.]).iloc[::-1], example([100., 101.], [10., np.nan])]:
            with self.subTest(bars=bars), self.assertRaises(ValueError):
                build_features(bars, small_config())

    def test_invalid_window_config_rejected(self):
        for value in [0, -1, True, 1.5]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                FeatureConfig((value,), (2,), (3,), (3,), 2, (2,))
        with self.assertRaises(ValueError):
            FeatureConfig((1,), (2,), (3,), (1,), 2, (2,))
        with self.assertRaises(ValueError):
            FeatureConfig((1, 1), (2,), (3,), (3,), 2, (2,))

    def test_config_loader_rejects_misspelling(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.json"
            path.write_text('{"rsi_windows": 14}')
            with self.assertRaises(ValueError):
                load_feature_config(path)

    def test_offline_artifact_links_to_snapshot_and_preserves_warmup(self):
        bars = example([100., 102., 101.], [10., 10., 20.])
        bars.index = pd.DatetimeIndex(["2020-01-02", "2020-01-03", "2020-01-06"], name="Date")
        for column in ["Open", "High", "Low", "Close"]:
            bars[column] = bars["Adj Close"]
        bars["Dividends"] = bars["Stock Splits"] = 0.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            snapshot = save_snapshot(bars, DataConfig("SPY", "2020-01-01", "2020-01-07"), root / "data")
            artifact = prepare_features(snapshot, small_config(), root / "features")
            metadata = json.loads((artifact / "metadata.json").read_text())
            saved = pd.read_csv(artifact / "features.csv")
            self.assertEqual(metadata["source_metadata_sha256"], sha256(snapshot / "metadata.json"))
            self.assertEqual(metadata["sha256"]["features.csv"], sha256(artifact / "features.csv"))
            self.assertEqual(metadata["rows"], 3)
            self.assertEqual(metadata["complete_candidate_rows"], 0)
            self.assertNotIn("sma_3_diagnostic", metadata["candidate_columns"])
            self.assertTrue(saved.return_current.isna().iloc[0])
            (snapshot / "provider.csv").write_text("tampered")
            with self.assertRaisesRegex(ValueError, "checksum"):
                prepare_features(snapshot, small_config(), root / "features")
