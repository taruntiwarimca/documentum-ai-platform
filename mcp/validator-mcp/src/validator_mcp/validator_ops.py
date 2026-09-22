"""Real aggregation of every other agent's local state into a golden
transaction verdict (ADR-008: GREEN requires functional validation, not just
process/port checks).

VALIDATOR-MCP does not call other agents' MCP tools itself — that is the
orchestrator dispatcher's job (it calls each domain agent in dependency
order, then calls this agent to aggregate the resulting real state). This
agent reads each component's real ComponentStore/index files
(agent_common.component_store.ComponentStore.peek) and checks it for real,
rather than trusting a canned status.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from agent_common.audit import AuditLog
from agent_common.component_store import ComponentStore


class ValidatorAgent:
    def __init__(self, data_dir: str | Path, audit_log: AuditLog) -> None:
        self._data_dir = Path(data_dir)
        self._audit_log = audit_log

    def _peek(self, environment: str, component: str) -> dict[str, Any] | None:
        return ComponentStore.peek(self._data_dir, environment, component)

    def validate_component(self, environment: str, component: str) -> dict[str, Any]:
        state = self._peek(environment, component)
        if state is None:
            return {"healthy": False, "status": "NOT_FOUND"}
        return {"healthy": state.get("status") == "INSTALLED", "status": state.get("status")}

    def _check_db(self, environment: str) -> dict[str, Any]:
        state = self._peek(environment, "oracle")
        databases = state.get("resources", {}).get("databases", {}) if state else {}
        ok = bool(state and state.get("status") == "INSTALLED" and databases)
        return {"ok": ok, "databases": list(databases)}

    def _check_cs(self, environment: str) -> dict[str, Any]:
        state = self._peek(environment, "content-server")
        repositories = state.get("resources", {}).get("repositories", {}) if state else {}
        ok = bool(state and state.get("status") == "INSTALLED" and repositories)
        return {"ok": ok, "repositories": list(repositories)}

    def _check_xplore(self, environment: str) -> dict[str, Any]:
        state = self._peek(environment, "xplore")
        collections = state.get("resources", {}).get("collections", {}) if state else {}
        indexed_docs = 0
        for name in collections:
            index_path = self._data_dir / environment / "xplore_index" / f"{name}.json"
            if index_path.exists():
                index = json.loads(index_path.read_text(encoding="utf-8"))
                indexed_docs += len(index.get("documents", {}))
        ok = bool(state and state.get("status") == "INSTALLED" and collections and indexed_docs > 0)
        return {"ok": ok, "collections": list(collections), "indexed_documents": indexed_docs}

    def _check_da(self, environment: str) -> dict[str, Any]:
        state = self._peek(environment, "da")
        last_login = state.get("last_login_test") if state else None
        ok = bool(
            state
            and state.get("status") == "INSTALLED"
            and state.get("repository")
            and state.get("authentication")
            and last_login
            and last_login.get("ok") is True
        )
        return {"ok": ok, "last_login_test": last_login}

    def golden_transaction(self, environment: str) -> dict[str, Any]:
        db = self._check_db(environment)
        cs = self._check_cs(environment)
        xplore = self._check_xplore(environment)
        da = self._check_da(environment)

        steps = {"db": db, "content_server": cs, "xplore": xplore, "da": da}
        passed = all(step["ok"] for step in steps.values())

        recent_evidence = [
            e["event_id"]
            for e in self._audit_log.all()
            if e.get("environment") == environment
        ][-10:]

        return {
            "status": "GREEN" if passed else "RED",
            "environment": environment,
            "steps": steps,
            "evidence": recent_evidence,
        }

    def evidence(self, operation_id: str) -> dict[str, Any]:
        record = self._audit_log.get(operation_id)
        if record is None:
            return {"found": False}
        return {"found": True, **record}
