"""Shared audit-log writer.

ADR-010: every consequential action is recorded as decision + evidence +
tool call + result. Reuses the event envelope shape from ADR-015
(event_id, source, event_type, environment, timestamp, payload).
"""
from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA = """
CREATE TABLE IF NOT EXISTS audit_log (
    event_id    TEXT PRIMARY KEY,
    source      TEXT NOT NULL,
    event_type  TEXT NOT NULL,
    environment TEXT,
    timestamp   TEXT NOT NULL,
    decision    TEXT,
    evidence    TEXT,
    tool_call   TEXT NOT NULL,
    result      TEXT NOT NULL
);
"""

_COLUMNS = [
    "event_id",
    "source",
    "event_type",
    "environment",
    "timestamp",
    "decision",
    "evidence",
    "tool_call",
    "result",
]


class AuditLog:
    def __init__(self, db_path: str | Path) -> None:
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        # See state_store.StateStore for why check_same_thread=False is needed.
        self._conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self._conn.execute(SCHEMA)
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    def record(
        self,
        *,
        source: str,
        event_type: str,
        environment: str | None,
        decision: str | None,
        evidence: dict[str, Any] | None,
        tool_call: dict[str, Any],
        result: dict[str, Any],
    ) -> str:
        event_id = f"EVT-{uuid.uuid4().hex[:12]}"
        self._conn.execute(
            f"INSERT INTO audit_log ({', '.join(_COLUMNS)}) VALUES (?,?,?,?,?,?,?,?,?)",
            (
                event_id,
                source,
                event_type,
                environment,
                datetime.now(timezone.utc).isoformat(),
                decision,
                json.dumps(evidence) if evidence is not None else None,
                json.dumps(tool_call),
                json.dumps(result),
            ),
        )
        self._conn.commit()
        return event_id

    def all(self) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            f"SELECT {', '.join(_COLUMNS)} FROM audit_log ORDER BY timestamp"
        ).fetchall()
        return [dict(zip(_COLUMNS, r)) for r in rows]
