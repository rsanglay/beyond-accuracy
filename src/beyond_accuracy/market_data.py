"""Explicit provider request and strict daily SPY validation."""
from dataclasses import dataclass
from datetime import date, datetime
import json
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import pandas_market_calendars as calendars
import yfinance as yf

COLUMNS = ["Open", "High", "Low", "Close", "Adj Close", "Volume", "Dividends", "Stock Splits"]
PROVIDER_OPTIONS = dict(interval="1d", auto_adjust=False, back_adjust=False,
                        actions=True, repair=False, keepna=True, prepost=False,
                        rounding=False, threads=False, progress=False,
                        ignore_tz=True, multi_level_index=False, timeout=30)


@dataclass(frozen=True)
class DataConfig:
    symbol: str
    start: str
    end: str

    def __post_init__(self):
        if self.symbol != "SPY":
            raise ValueError("Only SPY is supported")
        for value in (self.start, self.end):
            if not isinstance(value, str) or date.fromisoformat(value).isoformat() != value:
                raise ValueError("Dates must use YYYY-MM-DD")
        if self.start >= self.end:
            raise ValueError("start must precede exclusive end")
        today = datetime.now(ZoneInfo("America/New_York")).date().isoformat()
        if self.end > today:
            raise ValueError("end must exclude today's possibly incomplete session")


def load_data_config(path: Path) -> DataConfig:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or set(payload) != {"symbol", "start", "end"}:
        raise ValueError("Data config requires exactly symbol, start, end")
    return DataConfig(**payload)


def validate_bars(frame: pd.DataFrame, config: DataConfig) -> None:
    """Never sort, fill, drop, or repair bad observations silently."""
    if frame is None or frame.empty or not set(COLUMNS).issubset(frame.columns):
        raise ValueError("Empty data or missing required OHLCV/action columns")
    index = frame.index
    if not isinstance(index, pd.DatetimeIndex) or index.tz is not None:
        raise ValueError("Expected timezone-naive daily session dates")
    if index.hasnans or not index.is_unique or not index.is_monotonic_increasing:
        raise ValueError("Dates must be present, unique, and chronological")
    if not index.equals(index.normalize()):
        raise ValueError("Expected session dates, not intraday timestamps")
    expected = calendars.get_calendar("NYSE").valid_days(
        config.start, pd.Timestamp(config.end) - pd.Timedelta(days=1)
    ).tz_localize(None)
    missing, extra = expected.difference(index), index.difference(expected)
    if len(missing) or len(extra):
        raise ValueError(f"Session mismatch: missing={list(missing.strftime('%Y-%m-%d'))}, "
                         f"unexpected={list(extra.strftime('%Y-%m-%d'))}")
    numeric = frame[COLUMNS].to_numpy(dtype=float)
    if not np.isfinite(numeric).all():
        raise ValueError("Missing or nonfinite market values")
    if (frame[COLUMNS[:5]] <= 0).any().any():
        raise ValueError("Prices must be positive")
    if (frame[COLUMNS[5:]] < 0).any().any():
        raise ValueError("Volume and action values cannot be negative")
    if (frame["Volume"] % 1 != 0).any():
        raise ValueError("Volume must contain whole shares")
    if ((frame["High"] < frame[["Open", "Close", "Low"]].max(axis=1)).any()
            or (frame["Low"] > frame[["Open", "Close", "High"]].min(axis=1)).any()):
        raise ValueError("Inconsistent OHLC bounds")


def download_bars(config: DataConfig) -> pd.DataFrame:
    frame = yf.download(tickers=config.symbol, start=config.start, end=config.end,
                        **PROVIDER_OPTIONS)
    validate_bars(frame, config)
    return frame.rename_axis("Date")
