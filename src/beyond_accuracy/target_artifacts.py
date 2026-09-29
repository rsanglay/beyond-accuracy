"""Save separately labelled outcomes from a verified local price snapshot."""
from datetime import datetime, timezone
from importlib.metadata import distributions
import json
from pathlib import Path
import platform
import tempfile
import uuid

import pandas as pd

from beyond_accuracy.snapshots import git_state, sha256, verify_snapshot
from beyond_accuracy.targets import TARGET_DEFINITION, build_targets


def prepare_targets(snapshot: Path, output: Path) -> Path:
    source = verify_snapshot(snapshot)
    bars = pd.read_csv(snapshot / "provider.csv", index_col="Date", parse_dates=True)
    targets = build_targets(bars["Adj Close"])
    created = datetime.now(timezone.utc)
    output.mkdir(parents=True, exist_ok=True)
    destination = output / (created.strftime("%Y%m%dT%H%M%S") + "-" + uuid.uuid4().hex[:12])
    with tempfile.TemporaryDirectory(prefix=".pending-", dir=output) as directory:
        staging = Path(directory)
        targets.to_csv(staging / "targets.csv", index_label="Date", date_format="%Y-%m-%d")
        metadata = {
            "schema_version": 1, "created_at_utc": created.isoformat(),
            "target_definition": TARGET_DEFINITION,
            "source_snapshot_id": snapshot.name,
            "source_metadata_sha256": sha256(snapshot / "metadata.json"),
            "source_file_sha256": source["sha256"], "source_config": source["config"],
            "rows": len(targets), "known_labels": int(targets.target_up.notna().sum()),
            "unknown_labels": int(targets.target_up.isna().sum()),
            "columns_forbidden_as_features": list(targets.columns),
            "limitation": "Historical adjusted close-to-close classification outcomes, not executable strategy returns. Session dates do not specify data publication latency. No split, model, or training-admission logic implemented yet.",
            "git": git_state(), "python": platform.python_version(), "platform": platform.platform(),
            "packages": dict(sorted((d.metadata["Name"], d.version) for d in distributions())),
            "sha256": {"targets.csv": sha256(staging / "targets.csv")},
        }
        (staging / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
        staging.rename(destination)
    return destination
