"""SQLite-backed desired/current state store.

ADR-004: desired state is declarative; runtime (current) state is stored
separately. ``get`` reads ``current`` if present, else falls back to
``desired`` — a standard reconciliation read.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

SCHEMA = """
CREATE TABLE IF NOT EXISTS state (
    environment TEXT NOT NULL,
    namespace   TEXT NOT NULL CHECK (namespace IN ('desired', 'current')),
    key         TEXT NOT NULL,
    value       TEXT NOT NULL,
    updated_at  TEXT NOT NULL,
    PRIMARY KEY (environment, namespace, key)
);
"""


class StateNotFoundError(KeyError):
    """Raised when neither current nor desired state has the requested key."""


class StateStore:
    def __init__(self, db_path: str | Path) -> None:
        self._db_path = str(db_path)
        Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)
        # MCPServer runs sync tool functions in a worker thread pool; this
        # connection is created once at import time but called from those
        # worker threads, so the default same-thread check must be disabled.
        self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
        self._conn.execute(SCHEMA)
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    def get(self, environment: str, key: str) -> Any:
        row = self._conn.execute(
            "SELECT value FROM state WHERE environment=? AND namespace='current' AND key=?",
            (environment, key),
        ).fetchone()
        if row is None:
            row = self._conn.execute(
                "SELECT value FROM state WHERE environment=? AND namespace='desired' AND key=?",
                (environment, key),
            ).fetchone()
        if row is None:
            raise StateNotFoundError(f"{environment}:{key}")
        return json.loads(row[0])

    def set(self, environment: str, key: str, value: Any, namespace: str = "current") -> None:
        if namespace not in ("desired", "current"):
            raise ValueError("namespace must be 'desired' or 'current'")
        self._conn.execute(
            "INSERT INTO state (environment, namespace, key, value, updated_at) VALUES (?,?,?,?,?) "
            "ON CONFLICT(environment, namespace, key) "
            "DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at",
            (
                environment,
                namespace,
                key,
                json.dumps(value),
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        self._conn.commit()

    def load_desired_state_from_yaml(self, path: str | Path, environment: str) -> int:
        """Flatten a desired-state.yaml into dotted keys and seed the 'desired' namespace.

        Returns the number of leaf keys loaded.
        """
        data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
        count = 0
        for dotted_key, value in _flatten(data):
            self.set(environment, dotted_key, value, namespace="desired")
            count += 1
        return count


def _flatten(obj: Any, prefix: str = "") -> list[tuple[str, Any]]:
    items: list[tuple[str, Any]] = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            new_prefix = f"{prefix}.{k}" if prefix else str(k)
            items.extend(_flatten(v, new_prefix))
    else:
        items.append((prefix, obj))
    return items
