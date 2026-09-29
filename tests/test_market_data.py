"""Offline financial examples and corrupt-data checks."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd

from beyond_accuracy.market_data import DataConfig, download_bars, validate_bars
from beyond_accuracy.returns import calculate_returns
from beyond_accuracy.snapshots import save_snapshot, verify_snapshot


def example_bars():
    # January 1 is a holiday; January 4 and 5 are a weekend.
    return pd.DataFrame({
        "Open": [100., 102., 103.], "High": [101., 104., 104.],
        "Low": [99., 101., 102.], "Close": [100., 103., 103.],
        "Adj Close": [100., 103., 103.], "Volume": [1000, 1200, 1100],
        "Dividends": [0., 0., 0.], "Stock Splits": [0., 0., 0.],
    }, index=pd.DatetimeIndex(["2020-01-02", "2020-01-03", "2020-01-06"], name="Date"))


class ReturnTests(unittest.TestCase):
    def test_manual_gain_and_unchanged_price(self):
        result = calculate_returns(pd.Series([100., 103., 103.]))
        self.assertTrue(result.iloc[0].isna().all())
        self.assertAlmostEqual(result.simple_return.iloc[1], .03)
        self.assertAlmostEqual(result.log_return.iloc[1], np.log(1.03))
        self.assertEqual(result.simple_return.iloc[2], 0)
        self.assertEqual(result.log_return.iloc[2], 0)

    def test_loss(self):
        self.assertAlmostEqual(calculate_returns(pd.Series([100., 90.])).simple_return.iloc[1], -.1)

    def test_no_fill_or_invalid_prices(self):
        for values in ([100, np.nan, 103], [100, 0], [-1, 2], [100, np.inf]):
            with self.subTest(values=values), self.assertRaises(ValueError):
                calculate_returns(pd.Series(values))

    def test_future_price_cannot_change_past_returns(self):
        prices = pd.Series([100., 103., 90.])
        before = calculate_returns(prices)
        prices.iloc[-1] = 999
        pd.testing.assert_frame_equal(before.iloc[:2], calculate_returns(prices).iloc[:2])


class DataTests(unittest.TestCase):
    def setUp(self):
        self.config = DataConfig("SPY", "2020-01-01", "2020-01-07")
        self.bars = example_bars()

    def test_holiday_and_weekend_are_not_missing_sessions(self):
        validate_bars(self.bars, self.config)

    def test_rejects_missing_session_including_boundaries(self):
        for row in range(3):
            with self.subTest(row=row), self.assertRaisesRegex(ValueError, "Session mismatch"):
                validate_bars(self.bars.drop(self.bars.index[row]), self.config)

    def test_rejects_duplicates_disorder_and_invalid_values(self):
        bad_frames = [pd.concat([self.bars, self.bars.iloc[:1]]), self.bars.iloc[::-1]]
        for column, value in [("Close", np.nan), ("Adj Close", 0), ("Volume", -1), ("High", 1)]:
            bad = self.bars.copy()
            bad.loc[bad.index[0], column] = value
            bad_frames.append(bad)
        for bad in bad_frames:
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                validate_bars(bad, self.config)

    def test_empty_provider_response_fails(self):
        with patch("beyond_accuracy.market_data.yf.download", return_value=pd.DataFrame()):
            with self.assertRaises(ValueError):
                download_bars(self.config)

    def test_provider_options_are_explicit(self):
        with patch("beyond_accuracy.market_data.yf.download", return_value=self.bars) as call:
            download_bars(self.config)
        self.assertFalse(call.call_args.kwargs["auto_adjust"])
        self.assertTrue(call.call_args.kwargs["actions"])
        self.assertTrue(call.call_args.kwargs["keepna"])
        self.assertEqual(call.call_args.kwargs["end"], "2020-01-07")

    def test_date_config_rejects_bad_ranges(self):
        for start, end in [("2020-01-07", "2020-01-01"), ("20200101", "2020-01-07"), ("2020-01-01", "2999-01-01")]:
            with self.subTest(start=start, end=end), self.assertRaises(ValueError):
                DataConfig("SPY", start, end)

    def test_snapshot_round_trip_and_tamper_detection(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = save_snapshot(self.bars, self.config, Path(tmp))
            self.assertEqual(verify_snapshot(path)["rows"], 3)
            other = save_snapshot(self.bars, self.config, Path(tmp))
            self.assertNotEqual(path, other)
            with (path / "provider.csv").open("a") as stream:
                stream.write("corrupted")
            with self.assertRaisesRegex(ValueError, "checksum"):
                verify_snapshot(path)

    def test_adjusted_series_avoids_synthetic_split_drop(self):
        bars = self.bars.copy()
        bars.loc[bars.index[0], ["Open", "High", "Low", "Close"]] = [100, 101, 99, 100]
        bars.loc[bars.index[1:], ["Open", "High", "Low", "Close"]] = [50, 51, 49, 50]
        bars["Adj Close"] = 50.
        bars.loc[bars.index[1], "Stock Splits"] = 2.
        with tempfile.TemporaryDirectory() as tmp:
            path = save_snapshot(bars, self.config, Path(tmp))
            returns = pd.read_csv(path / "returns.csv")
            self.assertEqual(returns.adjusted_simple_return.iloc[1], 0)
