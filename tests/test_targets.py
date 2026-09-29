"""Known outcomes, next-session alignment, and separation from features."""
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np
import pandas as pd

from beyond_accuracy.features import FeatureConfig, build_features
from beyond_accuracy.market_data import DataConfig
from beyond_accuracy.snapshots import save_snapshot, sha256
from beyond_accuracy.targets import build_targets
from beyond_accuracy.target_artifacts import prepare_targets


def prices():
    return pd.Series([100., 103., 103., 100.],
                     index=pd.DatetimeIndex(['2020-01-02', '2020-01-03', '2020-01-06', '2020-01-07'], name='Date'))


class TargetTests(unittest.TestCase):
    def test_positive_flat_negative_and_unknown(self):
        result = build_targets(prices())
        self.assertEqual(result.target_up.iloc[:3].tolist(), [1, 0, 0])
        self.assertAlmostEqual(result.next_return.iloc[0], .03)
        self.assertEqual(result.next_return.iloc[1], 0)
        self.assertAlmostEqual(result.next_return.iloc[2], 100 / 103 - 1)
        self.assertTrue(result.iloc[-1].isna().all())
        self.assertEqual(str(result.target_up.dtype), 'Int64')

    def test_outcomes_follow_sessions_not_calendar_days(self):
        result = build_targets(prices())
        self.assertEqual(result.outcome_session.iloc[1], pd.Timestamp('2020-01-06'))
        self.assertTrue((result.outcome_session.iloc[:-1] > result.index[:-1]).all())

    def test_single_price_has_no_known_outcome(self):
        self.assertTrue(build_targets(prices().iloc[:1]).iloc[0].isna().all())

    def test_appending_a_session_only_resolves_previous_final_label(self):
        before = build_targets(prices().iloc[:3])
        after = build_targets(prices())
        pd.testing.assert_frame_equal(before.iloc[:2], after.iloc[:2])
        self.assertTrue(pd.isna(before.target_up.iloc[-1]))
        self.assertEqual(after.target_up.iloc[2], 0)

    def test_future_change_affects_target_but_not_current_features(self):
        bars = pd.DataFrame({'Adj Close': prices(), 'Volume': 100.})
        config = FeatureConfig((1,), (1,), (2,), (2,), 2, (2,))
        before = bars.copy(deep=True)
        features = build_features(bars, config)
        targets = build_targets(bars['Adj Close'])
        changed = bars.copy()
        changed.iloc[-1, 0] = 110.
        pd.testing.assert_frame_equal(features.iloc[:-1], build_features(changed, config).iloc[:-1])
        self.assertEqual(targets.target_up.iloc[-2], 0)
        self.assertEqual(build_targets(changed['Adj Close']).target_up.iloc[-2], 1)
        self.assertTrue(set(features.columns).isdisjoint(targets.columns))
        pd.testing.assert_frame_equal(bars, before)

    def test_missing_price_cannot_become_class_zero(self):
        series = prices()
        series.iloc[1] = np.nan
        with self.assertRaises(ValueError):
            build_targets(series)

    def test_invalid_index_rejected(self):
        for series in [prices().iloc[::-1], pd.concat([prices(), prices().iloc[:1]]),
                       prices().reset_index(drop=True)]:
            with self.subTest(series=series), self.assertRaises(ValueError):
                build_targets(series)

    def test_artifact_round_trip_and_source_tampering(self):
        bars = pd.DataFrame({'Adj Close': prices(), 'Volume': 100})
        for column in ['Open', 'High', 'Low', 'Close']:
            bars[column] = prices()
        bars['Dividends'] = bars['Stock Splits'] = 0.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            snapshot = save_snapshot(bars, DataConfig('SPY', '2020-01-02', '2020-01-08'), root / 'data')
            path = prepare_targets(snapshot, root / 'targets')
            metadata = json.loads((path / 'metadata.json').read_text())
            restored = pd.read_csv(path / 'targets.csv', index_col='Date', parse_dates=['Date', 'outcome_session'],
                                   dtype={'target_up': 'Int64'})
            pd.testing.assert_frame_equal(restored, build_targets(prices()), check_freq=False)
            self.assertEqual(metadata['known_labels'], 3)
            self.assertEqual(metadata['unknown_labels'], 1)
            self.assertEqual(metadata['source_metadata_sha256'], sha256(snapshot / 'metadata.json'))
            self.assertEqual(metadata['sha256']['targets.csv'], sha256(path / 'targets.csv'))
            self.assertFalse((path / 'features.csv').exists())
            (snapshot / 'provider.csv').write_text('corrupt')
            with self.assertRaisesRegex(ValueError, 'checksum'):
                prepare_targets(snapshot, root / 'targets')
