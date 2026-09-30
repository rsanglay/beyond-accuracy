"""Small command-line interface for explicit, reproducible data preparation."""
import argparse
from dataclasses import asdict
import json
from pathlib import Path

from beyond_accuracy.config import load_config


def main() -> None:
    parser = argparse.ArgumentParser(description="Beyond Accuracy research tools")
    commands = parser.add_subparsers(dest="command", required=True)
    check = commands.add_parser("check-config", help="Validate experiment settings")
    check.add_argument("--config", type=Path, required=True)
    download = commands.add_parser("download-data", help="Download and validate a new SPY snapshot")
    download.add_argument("--config", type=Path, required=True)
    download.add_argument("--output", type=Path, default=Path("data/snapshots"))
    verify = commands.add_parser("verify-data", help="Verify a snapshot offline")
    verify.add_argument("snapshot", type=Path)
    features = commands.add_parser("build-features", help="Build trailing features from a verified local snapshot")
    features.add_argument("--snapshot", type=Path, required=True)
    features.add_argument("--config", type=Path, required=True)
    features.add_argument("--output", type=Path, default=Path("results/features"))
    targets = commands.add_parser("build-targets", help="Build separate next-session labels from a verified snapshot")
    targets.add_argument("--snapshot", type=Path, required=True)
    targets.add_argument("--output", type=Path, default=Path("results/targets"))
    commands.add_parser("benchmark-demo", help="Show synthetic benchmark predictions (no market evaluation)")
    args = parser.parse_args()
    try:
        if args.command == "check-config":
            result = asdict(load_config(args.config))
        elif args.command == "download-data":
            from beyond_accuracy.market_data import download_bars, load_data_config
            from beyond_accuracy.snapshots import save_snapshot
            config = load_data_config(args.config)
            result = {"snapshot": str(save_snapshot(download_bars(config), config, args.output))}
        elif args.command == "build-features":
            from beyond_accuracy.features import load_feature_config
            from beyond_accuracy.feature_artifacts import prepare_features
            config = load_feature_config(args.config)
            result = {"features": str(prepare_features(args.snapshot, config, args.output))}
        elif args.command == "build-targets":
            from beyond_accuracy.target_artifacts import prepare_targets
            result = {"targets": str(prepare_targets(args.snapshot, args.output))}
        elif args.command == "benchmark-demo":
            from beyond_accuracy.benchmark_demo import benchmark_demo
            result = benchmark_demo()
        else:
            from beyond_accuracy.snapshots import verify_snapshot
            metadata = verify_snapshot(args.snapshot)
            result = {"verified": True, "rows": metadata["rows"],
                      "first_session": metadata["first_session"], "last_session": metadata["last_session"]}
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.exit(2, f"Data/configuration error: {exc}\n")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
