"""Save isolated snapshots and verify saved bytes before reuse."""
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
from importlib.metadata import distributions
import json
from pathlib import Path
import platform
import subprocess
import tempfile
import uuid

import pandas as pd

from beyond_accuracy.market_data import DataConfig, PROVIDER_OPTIONS, validate_bars
from beyond_accuracy.returns import calculate_returns


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_state() -> dict:
    root = Path(__file__).resolve().parents[2]
    def run(*args):
        result = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)
        return result.stdout.strip() if result.returncode == 0 else None
    status = run("status", "--porcelain")
    return {"commit": run("rev-parse", "HEAD"), "dirty": None if status is None else bool(status)}


def save_snapshot(frame: pd.DataFrame, config: DataConfig, output: Path) -> Path:
    validate_bars(frame, config)
    output.mkdir(parents=True, exist_ok=True)
    created = datetime.now(timezone.utc)
    name = created.strftime("%Y%m%dT%H%M%S") + "-" + uuid.uuid4().hex[:12]
    destination = output / name
    with tempfile.TemporaryDirectory(prefix=".pending-", dir=output) as temp:
        staging = Path(temp)
        frame.to_csv(staging / "provider.csv", index_label="Date", date_format="%Y-%m-%d")
        returns = calculate_returns(frame["Adj Close"])
        returns.columns = ["adjusted_simple_return", "adjusted_log_return"]
        returns.to_csv(staging / "returns.csv", index_label="Date", date_format="%Y-%m-%d")
        metadata = {
            "schema_version": 1, "created_at_utc": created.isoformat(),
            "source": "Yahoo Finance via yfinance", "config": asdict(config),
            "provider_options": PROVIDER_OPTIONS, "calendar": "NYSE",
            "date_semantics": "Exchange session dates; start inclusive, end exclusive",
            "price_semantics": "Provider OHLC retained with auto_adjust=False; Yahoo OHLC may already be split-adjusted. Adj Close includes provider corporate-action adjustments. Neither is point-in-time vintage data.",
            "return_semantics": "Backward-looking Adj Close returns; first row undefined; not strategy returns or execution prices",
            "rows": len(frame), "first_session": str(frame.index[0].date()),
            "last_session": str(frame.index[-1].date()), "git": git_state(),
            "python": platform.python_version(), "platform": platform.platform(),
            "packages": dict(sorted((d.metadata["Name"], d.version) for d in distributions())),
            "sha256": {name: sha256(staging / name) for name in ("provider.csv", "returns.csv")},
        }
        (staging / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
        staging.rename(destination)
    return destination


def verify_snapshot(path: Path) -> dict:
    metadata = json.loads((path / "metadata.json").read_text(encoding="utf-8"))
    if metadata.get("schema_version") != 1:
        raise ValueError("Unsupported snapshot schema")
    for name in ("provider.csv", "returns.csv"):
        if sha256(path / name) != metadata["sha256"][name]:
            raise ValueError(f"Snapshot checksum mismatch: {name}")
    config = DataConfig(**metadata["config"])
    bars = pd.read_csv(path / "provider.csv", index_col="Date", parse_dates=True)
    validate_bars(bars, config)
    if len(bars) != metadata["rows"]:
        raise ValueError("Snapshot row count mismatch")
    expected = calculate_returns(bars["Adj Close"])
    expected.columns = ["adjusted_simple_return", "adjusted_log_return"]
    actual = pd.read_csv(path / "returns.csv", index_col="Date", parse_dates=True)
    try:
        pd.testing.assert_frame_equal(actual, expected, check_freq=False, rtol=1e-10, atol=1e-12)
    except AssertionError as exc:
        raise ValueError("Saved returns disagree with provider data") from exc
    return metadata
