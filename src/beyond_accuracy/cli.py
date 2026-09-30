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
    walk = commands.add_parser("walk-forward", help="Generate annual development benchmark predictions locally")
    walk.add_argument("--snapshot", type=Path, required=True)
    walk.add_argument("--features-config", type=Path, required=True)
    walk.add_argument("--config", type=Path, required=True)
    walk.add_argument("--logistic-config", type=Path, help="Optionally add fold-fitted Logistic Regression")
    walk.add_argument("--forest-config", type=Path, help="Optionally add fold-fitted Random Forest")
    walk.add_argument("--output", type=Path, default=Path("results/walk_forward"))
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
        elif args.command == "walk-forward":
            from beyond_accuracy.features import load_feature_config
            from beyond_accuracy.walk_forward import load_walk_forward_config
            from beyond_accuracy.walk_forward_run import run_walk_forward
            from beyond_accuracy.logistic import load_logistic_config
            from beyond_accuracy.random_forest import load_forest_config
            result = {"run": str(run_walk_forward(args.snapshot, load_feature_config(args.features_config),
                                                 load_walk_forward_config(args.config), args.output,
                                                 load_logistic_config(args.logistic_config) if args.logistic_config else None,
                                                 load_forest_config(args.forest_config) if args.forest_config else None))}
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
