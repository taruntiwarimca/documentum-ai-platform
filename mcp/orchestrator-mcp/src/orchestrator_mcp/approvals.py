"""Human approval request persistence (ADR-005).

Approval decisions are made out-of-band by a human, never by the agent
itself — there is deliberately no ``approval.approve`` MCP tool (matches
``config/mcp-tools.yaml``, which only allowlists ``approval.request`` for
``orchestrator``). Use ``approve_cli.py`` to list/decide pending requests.
"""
from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA = """
CREATE TABLE IF NOT EXISTS approvals (
    approval_id  TEXT PRIMARY KEY,
    operation    TEXT NOT NULL,
    environment  TEXT NOT NULL,
    resource     TEXT,
    requested_by TEXT,
    reason       TEXT,
    status       TEXT NOT NULL CHECK (status IN ('PENDING','APPROVED','DENIED')),
    created_at   TEXT NOT NULL,
    decided_at   TEXT,
    decided_by   TEXT
);
"""

_COLUMNS = [
    "approval_id",
    "operation",
    "environment",
    "resource",
    "requested_by",
    "reason",
    "status",
    "created_at",
    "decided_at",
    "decided_by",
]


class ApprovalStore:
    def __init__(self, db_path: str | Path) -> None:
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        # See state_store.StateStore for why check_same_thread=False is needed.
        self._conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self._conn.execute(SCHEMA)
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    def request(
        self,
        operation: str,
        environment: str,
        resource: str | None,
        requested_by: str,
        reason: str,
    ) -> dict[str, Any]:
        approval_id = f"APR-{uuid.uuid4().hex[:12]}"
        self._conn.execute(
            "INSERT INTO approvals "
            "(approval_id, operation, environment, resource, requested_by, reason, status, created_at) "
            "VALUES (?,?,?,?,?,?, 'PENDING', ?)",
            (
                approval_id,
                operation,
                environment,
                resource,
                requested_by,
                reason,
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        self._conn.commit()
        return self.get(approval_id)

    def get(self, approval_id: str) -> dict[str, Any]:
        row = self._conn.execute(
            f"SELECT {', '.join(_COLUMNS)} FROM approvals WHERE approval_id=?",
            (approval_id,),
        ).fetchone()
        if row is None:
            raise KeyError(approval_id)
        return dict(zip(_COLUMNS, row))

    def list_pending(self) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            f"SELECT {', '.join(_COLUMNS)} FROM approvals WHERE status='PENDING' ORDER BY created_at"
        ).fetchall()
        return [dict(zip(_COLUMNS, r)) for r in rows]

    def find_latest(self, operation: str, environment: str) -> dict[str, Any] | None:
        """Most recent request (any status) for this operation+environment,
        used by deploy_cli.py to avoid re-filing a duplicate approval on
        every re-run once one already exists."""
        row = self._conn.execute(
            f"SELECT {', '.join(_COLUMNS)} FROM approvals "
            "WHERE operation=? AND environment=? ORDER BY created_at DESC LIMIT 1",
            (operation, environment),
        ).fetchone()
        return dict(zip(_COLUMNS, row)) if row else None

    def decide(self, approval_id: str, status: str, decided_by: str) -> dict[str, Any]:
        if status not in ("APPROVED", "DENIED"):
            raise ValueError("status must be APPROVED or DENIED")
        self._conn.execute(
            "UPDATE approvals SET status=?, decided_at=?, decided_by=? WHERE approval_id=?",
            (status, datetime.now(timezone.utc).isoformat(), decided_by, approval_id),
        )
        self._conn.commit()
        return self.get(approval_id)
