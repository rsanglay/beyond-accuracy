"""After-close features: trailing windows only, with explicit warm-up values."""
from dataclasses import dataclass, fields
import json
from pathlib import Path

import numpy as np
import pandas as pd

from beyond_accuracy.returns import calculate_returns


@dataclass(frozen=True)
class FeatureConfig:
    return_lags: tuple[int, ...]
    momentum_windows: tuple[int, ...]
    moving_average_windows: tuple[int, ...]
    volatility_windows: tuple[int, ...]
    rsi_window: int
    volume_windows: tuple[int, ...]

    def __post_init__(self):
        for field in fields(self):
            value = getattr(self, field.name)
            values = (value,) if field.name == "rsi_window" else value
            if not isinstance(values, tuple) or not values:
                raise ValueError(f"{field.name} must be a nonempty tuple of integers")
            minimum = 2 if field.name == "volatility_windows" else 1
            if any(type(v) is not int or v < minimum for v in values):
                raise ValueError(f"{field.name} requires integers >= {minimum}")
            if len(set(values)) != len(values):
                raise ValueError(f"{field.name} contains duplicates")


def load_feature_config(path: Path) -> FeatureConfig:
    payload = json.loads(path.read_text(encoding="utf-8"))
    expected = {field.name for field in fields(FeatureConfig)}
    if not isinstance(payload, dict) or set(payload) != expected:
        raise ValueError(f"Feature config requires exactly {sorted(expected)}")
    for name in expected - {"rsi_window"}:
        if not isinstance(payload[name], list):
            raise ValueError(f"{name} must be an array")
        payload[name] = tuple(payload[name])
    return FeatureConfig(**payload)


def wilder_rsi(prices: pd.Series, window: int) -> pd.Series:
    """Seed with n actual changes, then apply Wilder's recursive smoothing.

    Equal positive gains/losses yield 50; a completely flat history also uses 50.
    All gains yield 100 and all losses yield 0 after the initial warm-up.
    """
    if type(window) is not int or window < 1:
        raise ValueError("RSI window must be a positive integer")
    calculate_returns(prices)  # Enforce the same finite, positive, ordered input contract.
    result = pd.Series(np.nan, index=prices.index, dtype=float)
    if len(prices) <= window:
        return result
    changes = prices.diff()
    gains = changes.clip(lower=0)
    losses = -changes.clip(upper=0)
    average_gain = gains.iloc[1:window + 1].mean()
    average_loss = losses.iloc[1:window + 1].mean()
    for row in range(window, len(prices)):
        if row > window:
            average_gain = ((window - 1) * average_gain + gains.iloc[row]) / window
            average_loss = ((window - 1) * average_loss + losses.iloc[row]) / window
        # Algebraically identical to 100 - 100/(1 + gain/loss), without division by zero.
        total = average_gain + average_loss
        result.iloc[row] = 50.0 if total == 0 else 100 * average_gain / total
    return result


def build_features(bars: pd.DataFrame, config: FeatureConfig) -> pd.DataFrame:
    """Consume consecutive validated session rows; never fill or drop observations.

    The snapshot CLI validates the exchange calendar before calling this function.
    Moving-average price levels are diagnostics, not approved model inputs.
    """
    if not {"Adj Close", "Volume"}.issubset(bars.columns):
        raise ValueError("Features require Adj Close and Volume")
    prices = bars["Adj Close"].astype(float)
    returns = calculate_returns(prices)["simple_return"]
    volume = bars["Volume"].astype(float)
    if not np.isfinite(volume).all() or (volume < 0).any():
        raise ValueError("Volume must be finite and nonnegative")
    columns = {"return_current": returns}
    for lag in config.return_lags:
        columns[f"return_lag_{lag}"] = returns.shift(lag)
    for window in config.momentum_windows:
        columns[f"momentum_{window}"] = prices / prices.shift(window) - 1
    for window in config.moving_average_windows:
        columns[f"sma_{window}_diagnostic"] = prices.rolling(window, min_periods=window).mean()
    for window in config.volatility_windows:
        columns[f"volatility_{window}"] = returns.rolling(window, min_periods=window).std(ddof=1)
    columns[f"rsi_{config.rsi_window}"] = wilder_rsi(prices, config.rsi_window)
    for window in config.volume_windows:
        baseline = volume.shift(1).rolling(window, min_periods=window).mean()
        columns[f"relative_volume_{window}"] = volume / baseline.where(baseline > 0)
    result = pd.DataFrame(columns, index=bars.index)
    if np.isinf(result.to_numpy()).any():
        raise ValueError("Feature calculation overflowed")
    return result
