"""Human-facing CLI to populate the local vault store (ADR-006).

Not exposed as an MCP tool — agents may only resolve secrets, never write
them. Example:

    python -m security_mcp.seed_cli put dctm/oracle/admin "not-a-real-secret"
"""
from __future__ import annotations

import argparse

from agent_common.paths import repo_root_from_agent_package, vault_path

from .vault_store import put_secret


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed the local vault store.")
    sub = parser.add_subparsers(dest="command", required=True)
    put = sub.add_parser("put", help="Set a secret at a vault path")
    put.add_argument("ref_path", help="e.g. dctm/oracle/admin (no vault:// prefix)")
    put.add_argument("value")
    args = parser.parse_args()

    path = vault_path(repo_root_from_agent_package(__file__))
    if args.command == "put":
        put_secret(path, args.ref_path, args.value)
        print(f"Set vault://{args.ref_path} in {path}")


if __name__ == "__main__":
    main()
