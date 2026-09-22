"""Real local operations standing in for Content Server 23.4.

No real Content Server is reachable in this environment. State is a real
JSON manifest (ComponentStore); `create_repository` performs a genuine
cross-component dependency check by reading DB-MCP's own state file
(ComponentStore.peek) and fails if the target database doesn't actually
exist there — the same "Oracle → Content Server → Repository" dependency
from target architecture §7, enforced for real rather than assumed.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from agent_common.component_store import ComponentStore


class DependencyError(ValueError):
    """Raised when a required upstream component/resource doesn't exist."""


class ContentServerAgent:
    def __init__(self, data_dir: str | Path, environment: str) -> None:
        self._data_dir = Path(data_dir)
        self._environment = environment
        self._store = ComponentStore(self._data_dir, environment, "content-server")

    def precheck(self) -> dict[str, Any]:
        oracle_state = ComponentStore.peek(self._data_dir, self._environment, "oracle")
        oracle_installed = bool(oracle_state and oracle_state.get("status") == "INSTALLED")
        return {"ok": True, "oracle_installed": oracle_installed}

    def install(self) -> dict[str, Any]:
        data = self._store.read()
        if data["status"] == "INSTALLED":
            return {"already_installed": True, **data}
        data = self._store.update(status="INSTALLED")
        return {"already_installed": False, **data}

    def configure_docbroker(self, host: str, port: int) -> dict[str, Any]:
        if not host:
            raise ValueError("host is required")
        if not (1 <= port <= 65535):
            raise ValueError(f"invalid port {port}")
        record = {"host": host, "port": port}
        self._store.update(docbroker=record)
        return record

    def create_repository(self, name: str, database: str) -> dict[str, Any]:
        oracle_state = ComponentStore.peek(self._data_dir, self._environment, "oracle")
        if not oracle_state or database not in oracle_state.get("resources", {}).get(
            "databases", {}
        ):
            raise DependencyError(
                f"database {database!r} does not exist in DB-MCP's state — "
                "create it there first (Oracle -> Content Server -> Repository)"
            )
        docbroker = self._store.read().get("docbroker")
        record = {"name": name, "database": database, "docbroker": docbroker}
        self._store.set_resource("repositories", name, record)
        return record

    def configure_global_registry(self, repository: str) -> dict[str, Any]:
        if not self._store.has_resource("repositories", repository):
            raise DependencyError(
                f"repository {repository!r} does not exist — create it first"
            )
        record = {"repository": repository}
        self._store.update(global_registry=record)
        return record

    def health(self) -> dict[str, Any]:
        data = self._store.read()
        repositories = data.get("resources", {}).get("repositories", {})
        return {
            "status": data["status"],
            "healthy": data["status"] == "INSTALLED",
            "repositories": list(repositories.keys()),
            "docbroker": data.get("docbroker"),
        }

    def test_repository(self, name: str) -> dict[str, Any]:
        record = self._store.get_resource("repositories", name)
        if record is None:
            return {"ok": False, "reason": f"repository {name!r} not found"}
        oracle_state = ComponentStore.peek(self._data_dir, self._environment, "oracle")
        db_ok = bool(
            oracle_state
            and record["database"] in oracle_state.get("resources", {}).get("databases", {})
        )
        if not db_ok:
            return {
                "ok": False,
                "reason": f"backing database {record['database']!r} no longer exists in DB-MCP's state",
            }
        return {"ok": True, "repository": name, "database": record["database"]}
