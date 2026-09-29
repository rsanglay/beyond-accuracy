"""Check mistakes that could silently alter an experiment."""

import json
from pathlib import Path
import tempfile
import unittest

from beyond_accuracy.config import load_config


class ConfigTests(unittest.TestCase):
    def load(self, payload):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "experiment.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            return load_config(path)

    def test_preserves_explicit_settings(self):
        config = self.load({"symbol": "SPY", "random_seed": 7})
        self.assertEqual(config.symbol, "SPY")
        self.assertEqual(config.random_seed, 7)

    def test_rejects_misspelled_setting(self):
        with self.assertRaises(ValueError):
            self.load({"symbol": "SPY", "random_sead": 42})

    def test_rejects_extra_setting(self):
        with self.assertRaises(ValueError):
            self.load({"symbol": "SPY", "random_seed": 42, "unknown": 1})

    def test_rejects_invalid_seeds(self):
        for seed in [True, -1, 2**32, 1.5, "42"]:
            with self.subTest(seed=seed), self.assertRaises(ValueError):
                self.load({"symbol": "SPY", "random_seed": seed})

    def test_rejects_unplanned_asset(self):
        with self.assertRaises(ValueError):
            self.load({"symbol": "QQQ", "random_seed": 42})

    def test_rejects_non_object_config(self):
        with self.assertRaises(ValueError):
            self.load([])
