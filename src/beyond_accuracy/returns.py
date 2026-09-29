"""Backward-looking returns, labelled by the ending session."""
import numpy as np
import pandas as pd


def calculate_returns(prices: pd.Series) -> pd.DataFrame:
    """Require complete positive prices; leave the first return undefined."""
    if prices.empty or not prices.index.is_unique or not prices.index.is_monotonic_increasing:
        raise ValueError("Prices must be nonempty, unique, and chronological")
    values = prices.to_numpy(dtype=float)
    if not np.isfinite(values).all() or (values <= 0).any():
        raise ValueError("Prices must be finite and strictly positive; no filling allowed")
    ratio = prices / prices.shift(1)
    return pd.DataFrame({"simple_return": ratio - 1, "log_return": np.log(ratio)})
