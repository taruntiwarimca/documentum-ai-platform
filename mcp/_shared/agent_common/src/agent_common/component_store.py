"""JSON-file-backed component state store shared by every domain agent.

Each domain agent gets one JSON file per environment at
<data_dir>/<environment>/<component>.json, standing in for real
installed-component state (no real Oracle/OpenText installers are available
in this environment). Other agents may read a peer's file read-only via
`ComponentStore.peek(...)` to enforce real cross-component dependency checks
(e.g. xPlore requires CS's repository to exist before it can register it).
"""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any


class ComponentStore:
    def __init__(self, data_dir: str | Path, environment: str, component: str) -> None:
        self.environment = environment
        self.component = component
        self._path = Path(data_dir) / environment / f"{component}.json"
        self._path.parent.mkdir(parents=True, exist_ok=True)
        if not self._path.exists():
            self._write(self._initial_state())

    def _initial_state(self) -> dict[str, Any]:
        return {
            "component": self.component,
            "environment": self.environment,
            "status": "NOT_INSTALLED",
            "resources": {},
        }

    def read(self) -> dict[str, Any]:
        return json.loads(self._path.read_text(encoding="utf-8"))

    def _write(self, data: dict[str, Any]) -> None:
        fd, tmp_path = tempfile.mkstemp(dir=str(self._path.parent), suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            os.replace(tmp_path, self._path)
        except Exception:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            raise

    def update(self, **fields: Any) -> dict[str, Any]:
        data = self.read()
        data.update(fields)
        self._write(data)
        return data

    def set_resource(self, kind: str, name: str, value: dict[str, Any]) -> dict[str, Any]:
        data = self.read()
        data.setdefault("resources", {}).setdefault(kind, {})[name] = value
        self._write(data)
        return data

    def get_resource(self, kind: str, name: str) -> dict[str, Any] | None:
        return self.read().get("resources", {}).get(kind, {}).get(name)

    def has_resource(self, kind: str, name: str) -> bool:
        return self.get_resource(kind, name) is not None

    def list_resources(self, kind: str) -> dict[str, Any]:
        return self.read().get("resources", {}).get(kind, {})

    @staticmethod
    def peek(data_dir: str | Path, environment: str, component: str) -> dict[str, Any] | None:
        """Read-only lookup of another component's state, without creating it
        if it doesn't exist yet (unlike the constructor)."""
        path = Path(data_dir) / environment / f"{component}.json"
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))
