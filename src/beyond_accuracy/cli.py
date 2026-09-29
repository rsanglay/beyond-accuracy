"""Command-line entry point; research commands arrive in later phases."""

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
    args = parser.parse_args()
    try:
        config = load_config(args.config)
    except (OSError, ValueError) as exc:
        parser.exit(2, f"Configuration error: {exc}\n")
    print(json.dumps(asdict(config), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
