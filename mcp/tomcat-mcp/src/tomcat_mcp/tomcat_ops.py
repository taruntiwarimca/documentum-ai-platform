"""Real local operations standing in for Tomcat 10.

No real Tomcat instance is reachable in this environment. precheck's Java
compatibility enforcement is real, though: it reads compatibility/java.yaml
(ADR-014) and hard-stops if any of content_server/xplore/da is UNKNOWN or
VERIFY for the requested Java version — Tomcat's own JDK support does not
imply every Documentum component deployed to it is certified for that JDK.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from agent_common.component_store import ComponentStore

_GOOD_STATUSES = ("SUPPORTED", "SUPPORTED_BY_TOMCAT")
_REQUIRED_COMPONENTS = ("content_server", "xplore", "da", "tomcat")


class TomcatAgent:
    def __init__(
        self, data_dir: str | Path, environment: str, compatibility_dir: str | Path
    ) -> None:
        self._data_dir = Path(data_dir)
        self._environment = environment
        self._compatibility_dir = Path(compatibility_dir)
        self._store = ComponentStore(self._data_dir, environment, "tomcat")

    def precheck(self, java_version: str) -> dict[str, Any]:
        path = self._compatibility_dir / "java.yaml"
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {} if path.exists() else {}
        version_matrix = data.get("java", {}).get(str(java_version), {})

        statuses: dict[str, str] = {}
        blocked: list[str] = []
        for name in _REQUIRED_COMPONENTS:
            status = version_matrix.get(name, "UNKNOWN")
            statuses[name] = status
            if status not in _GOOD_STATUSES:
                blocked.append(name)

        return {
            "ok": len(blocked) == 0,
            "java_version": str(java_version),
            "component_status": statuses,
            "blocked_components": blocked,
        }

    def install(self, java_version: str) -> dict[str, Any]:
        data = self._store.read()
        if data["status"] == "INSTALLED":
            return {"already_installed": True, **data}
        data = self._store.update(status="INSTALLED", java_version=str(java_version))
        return {"already_installed": False, **data}

    def health(self) -> dict[str, Any]:
        data = self._store.read()
        return {
            "status": data["status"],
            "healthy": data["status"] == "INSTALLED",
            "java_version": data.get("java_version"),
        }
