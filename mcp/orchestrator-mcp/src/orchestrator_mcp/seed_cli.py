"""CLI to seed the State Store's desired namespace from a desired-state.yaml file.

Example:
    python -m orchestrator_mcp.seed_cli \\
        --from ../../../documentum-ai-platform-poc/config/desired-state.yaml \\
        --environment DCTM-DEV
"""
from __future__ import annotations

import argparse
from pathlib import Path

from .state_store import StateStore


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Seed ORCHESTRATOR-MCP's desired state from a YAML file."
    )
    parser.add_argument("--from", dest="source", required=True, help="Path to desired-state.yaml")
    parser.add_argument("--environment", required=True, help="Environment name, e.g. DCTM-DEV")
    parser.add_argument(
        "--db", default=None, help="Path to the state.db file (defaults to ./data/state.db)"
    )
    args = parser.parse_args()

    db_path = (
        Path(args.db)
        if args.db
        else Path(__file__).resolve().parent.parent.parent / "data" / "state.db"
    )
    store = StateStore(db_path)
    count = store.load_desired_state_from_yaml(args.source, args.environment)
    print(f"Loaded {count} desired-state keys for {args.environment} into {db_path}")


if __name__ == "__main__":
    main()
