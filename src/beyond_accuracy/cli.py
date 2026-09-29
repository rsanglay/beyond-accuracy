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
    args = parser.parse_args()
    try:
        if args.command == "check-config":
            result = asdict(load_config(args.config))
        elif args.command == "download-data":
            from beyond_accuracy.market_data import download_bars, load_data_config
            from beyond_accuracy.snapshots import save_snapshot
            config = load_data_config(args.config)
            result = {"snapshot": str(save_snapshot(download_bars(config), config, args.output))}
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
