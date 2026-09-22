"""Resolves vault://... secret references against SECURITY-MCP's local
file-backed vault store (ADR-006: agents never receive or embed plaintext
secrets directly; they resolve a reference at the point of use).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class SecretNotFoundError(KeyError):
    pass


def resolve_secret(vault_path: str | Path, ref: str) -> Any:
    """Resolve a 'vault://a/b/c' reference by looking up ["a"]["b"]["c"] in
    the vault JSON file at vault_path."""
    if not ref.startswith("vault://"):
        raise ValueError(f"not a vault reference: {ref}")
    path = Path(vault_path)
    if not path.exists():
        raise SecretNotFoundError(ref)
    node: Any = json.loads(path.read_text(encoding="utf-8"))
    for part in ref[len("vault://") :].split("/"):
        if not isinstance(node, dict) or part not in node:
            raise SecretNotFoundError(ref)
        node = node[part]
    return node
