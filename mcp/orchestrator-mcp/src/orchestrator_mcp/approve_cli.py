"""Human-facing CLI to list/decide pending approval requests (ADR-005).

Deliberately not exposed as an MCP tool — approvals are a human decision made
out-of-band from the agent. Examples:

    python -m orchestrator_mcp.approve_cli list
    python -m orchestrator_mcp.approve_cli decide APR-xxxxxxxxxxxx APPROVED --by "jane.doe"
"""
from __future__ import annotations

import argparse
from pathlib import Path

from .approvals import ApprovalStore


def main() -> None:
    parser = argparse.ArgumentParser(
        description="List or decide pending ORCHESTRATOR-MCP approval requests."
    )
    parser.add_argument(
        "--db", default=None, help="Path to the approvals.db file (defaults to ./data/approvals.db)"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list", help="List pending approval requests")

    decide = sub.add_parser("decide", help="Approve or deny a pending request")
    decide.add_argument("approval_id")
    decide.add_argument("status", choices=["APPROVED", "DENIED"])
    decide.add_argument("--by", required=True, dest="decided_by", help="Name of the human deciding")

    args = parser.parse_args()
    db_path = (
        Path(args.db)
        if args.db
        else Path(__file__).resolve().parent.parent.parent / "data" / "approvals.db"
    )
    store = ApprovalStore(db_path)

    if args.command == "list":
        pending = store.list_pending()
        if not pending:
            print("No pending approvals.")
        for record in pending:
            print(
                f"{record['approval_id']}  {record['operation']}  "
                f"env={record['environment']}  by={record['requested_by']}  "
                f"reason={record['reason']}"
            )
    elif args.command == "decide":
        record = store.decide(args.approval_id, args.status, args.decided_by)
        print(f"{record['approval_id']} -> {record['status']} (by {record['decided_by']})")


if __name__ == "__main__":
    main()
