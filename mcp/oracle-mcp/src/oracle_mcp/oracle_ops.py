"""Real local operations standing in for Oracle 19c.

No real Oracle instance is reachable in this environment (target
architecture assumption, confirmed with the user). "Databases" are real
SQLite files; tablespaces and users are real rows in a catalog table inside
that file — genuine SQL DDL/DML and file I/O, not canned responses. There is
no real Oracle listener process: create_listener is administrative
record-keeping only, and that limitation is stated in its return value.
"""
from __future__ import annotations

import shutil
import sqlite3
from pathlib import Path
from typing import Any

from agent_common.component_store import ComponentStore

_CATALOG_SCHEMA = """
CREATE TABLE IF NOT EXISTS __tablespaces (name TEXT PRIMARY KEY, size_mb INTEGER);
CREATE TABLE IF NOT EXISTS __users (name TEXT PRIMARY KEY, password_hash TEXT, tablespace TEXT);
"""


def _can_write(path: Path) -> bool:
    try:
        path.mkdir(parents=True, exist_ok=True)
        probe = path / ".write_probe"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
        return True
    except OSError:
        return False


class OracleAgent:
    def __init__(self, data_dir: str | Path, environment: str) -> None:
        self._data_dir = Path(data_dir)
        self._environment = environment
        self._store = ComponentStore(self._data_dir, environment, "oracle")

    def _db_path(self, database: str) -> Path:
        return self._data_dir / self._environment / f"oracle_{database}.sqlite"

    def precheck(self) -> dict[str, Any]:
        env_dir = self._data_dir / self._environment
        writable = _can_write(env_dir)
        usage = shutil.disk_usage(env_dir if env_dir.exists() else self._data_dir)
        ok = writable and usage.free > 50 * 1024 * 1024  # 50MB headroom
        return {"ok": ok, "writable": writable, "free_bytes": usage.free}

    def install(self) -> dict[str, Any]:
        data = self._store.read()
        if data["status"] == "INSTALLED":
            return {"already_installed": True, **data}
        data = self._store.update(status="INSTALLED")
        return {"already_installed": False, **data}

    def create_listener(self, name: str, port: int) -> dict[str, Any]:
        record = {
            "name": name,
            "port": port,
            "note": "administrative record only — no real network listener",
        }
        self._store.set_resource("listeners", name, record)
        return record

    def create_database(self, name: str, service: str | None = None) -> dict[str, Any]:
        path = self._db_path(name)
        path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(path))
        conn.executescript(_CATALOG_SCHEMA)
        conn.commit()
        conn.close()
        record = {"name": name, "service": service or name, "path": str(path)}
        self._store.set_resource("databases", name, record)
        return record

    def create_tablespace(self, database: str, name: str, size_mb: int = 100) -> dict[str, Any]:
        if not self._store.has_resource("databases", database):
            raise ValueError(f"database {database!r} does not exist — create it first")
        conn = sqlite3.connect(str(self._db_path(database)))
        conn.execute(
            "INSERT OR REPLACE INTO __tablespaces (name, size_mb) VALUES (?, ?)", (name, size_mb)
        )
        conn.commit()
        conn.close()
        record = {"name": name, "database": database, "size_mb": size_mb}
        self._store.set_resource("tablespaces", f"{database}.{name}", record)
        return record

    def create_user(
        self, database: str, name: str, password_hash: str, tablespace: str
    ) -> dict[str, Any]:
        if not self._store.has_resource("tablespaces", f"{database}.{tablespace}"):
            raise ValueError(
                f"tablespace {tablespace!r} does not exist in database {database!r} — create it first"
            )
        conn = sqlite3.connect(str(self._db_path(database)))
        conn.execute(
            "INSERT OR REPLACE INTO __users (name, password_hash, tablespace) VALUES (?, ?, ?)",
            (name, password_hash, tablespace),
        )
        conn.commit()
        conn.close()
        record = {"name": name, "database": database, "tablespace": tablespace}
        self._store.set_resource("users", f"{database}.{name}", record)
        return record

    def test_connection(self, database: str) -> dict[str, Any]:
        path = self._db_path(database)
        if not path.exists():
            return {"connected": False, "error": f"database {database!r} does not exist"}
        try:
            conn = sqlite3.connect(str(path))
            conn.execute("SELECT 1").fetchone()
            conn.close()
            return {"connected": True}
        except sqlite3.Error as exc:
            return {"connected": False, "error": str(exc)}

    def health(self) -> dict[str, Any]:
        data = self._store.read()
        databases = data.get("resources", {}).get("databases", {})
        missing = [name for name, rec in databases.items() if not Path(rec["path"]).exists()]
        healthy = data["status"] == "INSTALLED" and not missing
        return {
            "status": data["status"],
            "healthy": healthy,
            "databases": list(databases.keys()),
            "missing_database_files": missing,
        }
