"""Load explicit experiment settings before any research work runs."""

from dataclasses import dataclass
import json
from pathlib import Path


@dataclass(frozen=True)
class ExperimentConfig:
    symbol: str
    random_seed: int


def load_config(path: Path) -> ExperimentConfig:
    """Reject missing, unknown, or invalid settings instead of guessing."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or set(payload) != {"symbol", "random_seed"}:
        raise ValueError("Config must contain exactly symbol and random_seed")
    if payload["symbol"] != "SPY":
        raise ValueError("This research project currently supports only SPY")
    seed = payload["random_seed"]
    if type(seed) is not int or not 0 <= seed <= 2**32 - 1:
        raise ValueError("random_seed must be an integer between 0 and 2**32 - 1")
    return ExperimentConfig(**payload)
