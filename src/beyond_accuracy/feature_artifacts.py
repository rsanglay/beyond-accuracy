"""Build local feature artifacts from checksum-verified data, without a network call."""
from dataclasses import asdict
from datetime import datetime, timezone
from importlib.metadata import distributions
import json
from pathlib import Path
import platform
import tempfile
import uuid

import pandas as pd

from beyond_accuracy.features import FeatureConfig, build_features
from beyond_accuracy.snapshots import git_state, sha256, verify_snapshot


def prepare_features(snapshot: Path, config: FeatureConfig, output: Path) -> Path:
    source = verify_snapshot(snapshot)
    bars = pd.read_csv(snapshot / "provider.csv", index_col="Date", parse_dates=True)
    features = build_features(bars, config)
    diagnostics = [column for column in features if column.endswith("_diagnostic")]
    candidates = [column for column in features if column not in diagnostics]
    complete = features[candidates].notna().all(axis=1)
    first_complete = str(features.index[complete][0].date()) if complete.any() else None
    created = datetime.now(timezone.utc)
    output.mkdir(parents=True, exist_ok=True)
    destination = output / (created.strftime("%Y%m%dT%H%M%S") + "-" + uuid.uuid4().hex[:12])
    with tempfile.TemporaryDirectory(prefix=".pending-", dir=output) as directory:
        staging = Path(directory)
        features.to_csv(staging / "features.csv", index_label="Date", date_format="%Y-%m-%d")
        metadata = {
            "schema_version": 1, "created_at_utc": created.isoformat(),
            "config": asdict(config), "source_snapshot_id": snapshot.name,
            "source_metadata_sha256": sha256(snapshot / "metadata.json"),
            "source_file_sha256": source["sha256"], "source_config": source["config"],
            "availability": "After the labelled session's final data is available; not an execution assumption",
            "rows": len(features), "complete_candidate_rows": int(complete.sum()),
            "first_complete_candidate_session": first_complete,
            "missing_by_column": features.isna().sum().to_dict(),
            "candidate_columns": candidates, "diagnostic_columns": diagnostics,
            "units": "Returns/momentum/volatility: decimals; volatility not annualised; RSI: 0-100; relative volume: ratio; SMA: adjusted price units",
            "limitation": "Causal transformations of a fixed historical vintage do not prove point-in-time provider data. SMA levels are diagnostic only; no model input selection or fitting yet.",
            "git": git_state(), "python": platform.python_version(), "platform": platform.platform(),
            "packages": dict(sorted((d.metadata["Name"], d.version) for d in distributions())),
            "sha256": {"features.csv": sha256(staging / "features.csv")},
        }
        (staging / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
        staging.rename(destination)
    return destination
