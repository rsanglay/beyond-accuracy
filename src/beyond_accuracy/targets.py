"""Next-session outcomes, kept separate from prediction inputs."""
import pandas as pd

from beyond_accuracy.returns import calculate_returns


TARGET_DEFINITION = {
    "price_column": "Adj Close",
    "horizon_sessions": 1,
    "return": "P[t+1] / P[t] - 1",
    "positive_class": "1 when next_return > 0",
    "nonpositive_class": "0 when next_return <= 0",
    "unknown": "Missing, never class 0",
    "availability": "Only after outcome_session has closed and its final data is available",
}


def build_targets(prices: pd.Series) -> pd.DataFrame:
    """Attach tomorrow's outcome to today's session; never invent a final label.

    Input must contain consecutive validated exchange sessions. Session dates are
    not intraday availability timestamps. Walk-forward validation must enforce the
    after-close availability contract before admitting a label to training.
    """
    if not isinstance(prices.index, pd.DatetimeIndex) or prices.index.hasnans:
        raise ValueError("Targets require a DatetimeIndex of session dates")
    if prices.index.tz is not None or not prices.index.equals(prices.index.normalize()):
        raise ValueError("Targets require timezone-naive daily session dates")
    next_return = calculate_returns(prices)["simple_return"].shift(-1)
    target_up = next_return.gt(0).astype("Int64").mask(next_return.isna())
    outcome_session = pd.Series(prices.index, index=prices.index).shift(-1)
    return pd.DataFrame({
        "next_return": next_return,
        "target_up": target_up,
        "outcome_session": outcome_session,
    }, index=prices.index)
