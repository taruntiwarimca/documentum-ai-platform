"""Reads compatibility/*.yaml matrix data and evaluates stack/Java
compatibility (ADR-014, target architecture §5). No hardcoded rules — all
decisions trace back to the YAML data files.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

_COMPONENT_FILES = {
    "content_server": "documentum-23.4.yaml",
    "xplore": "xplore-22.1-p19.yaml",
    "da": "da-23.4.yaml",
    "tomcat": "tomcat-10.yaml",
}

_GOOD_JAVA_STATUSES = ("SUPPORTED", "SUPPORTED_BY_TOMCAT")


class CompatibilityMatrix:
    def __init__(self, compatibility_dir: str | Path) -> None:
        self._dir = Path(compatibility_dir)

    def check_stack(self, components: list[str] | None = None) -> dict[str, Any]:
        """Approved only if every checked component's recorded status is
        SUPPORTED. Defaults to checking all four known components."""
        components = components or list(_COMPONENT_FILES)
        results: dict[str, str] = {}
        blocked: list[str] = []
        for name in components:
            filename = _COMPONENT_FILES.get(name)
            status = "UNKNOWN_COMPONENT"
            if filename is not None:
                path = self._dir / filename
                if path.exists():
                    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
                    status = data.get("status", "UNKNOWN")
                else:
                    status = "NO_DATA"
            results[name] = status
            if status != "SUPPORTED":
                blocked.append(name)
        return {
            "approved": len(blocked) == 0,
            "component_status": results,
            "blocked_components": blocked,
        }

    def check_java(
        self, java_version: str, components: list[str] | None = None
    ) -> dict[str, Any]:
        """Approved only if every checked component's Java-support status is
        SUPPORTED or SUPPORTED_BY_TOMCAT. UNKNOWN/VERIFY hard-stops (ADR-014)."""
        components = components or ["content_server", "xplore", "da", "tomcat"]
        path = self._dir / "java.yaml"
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {} if path.exists() else {}
        version_matrix = data.get("java", {}).get(str(java_version), {})

        results: dict[str, str] = {}
        blocked: list[str] = []
        for name in components:
            status = version_matrix.get(name, "UNKNOWN")
            results[name] = status
            if status not in _GOOD_JAVA_STATUSES:
                blocked.append(name)
        return {
            "approved": len(blocked) == 0,
            "java_version": str(java_version),
            "component_status": results,
            "blocked_components": blocked,
        }
