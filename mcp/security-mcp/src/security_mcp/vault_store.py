"""Local file-backed vault store (stand-in for a real secrets manager, ADR-006).

Reads go through agent_common.secrets_client.resolve_secret. Writes happen
only via seed_cli.py, a human/ops tool, never through an MCP tool — mirrors
approval.request having no matching MCP-exposed approve tool.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def read_vault(vault_path: str | Path) -> dict[str, Any]:
    path = Path(vault_path)
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def write_vault(vault_path: str | Path, data: dict[str, Any]) -> None:
    path = Path(vault_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def put_secret(vault_path: str | Path, ref_path: str, value: Any) -> None:
    """ref_path is like 'dctm/oracle/admin' (no 'vault://' prefix)."""
    data = read_vault(vault_path)
    node = data
    parts = ref_path.split("/")
    for part in parts[:-1]:
        node = node.setdefault(part, {})
    node[parts[-1]] = value
    write_vault(vault_path, data)
