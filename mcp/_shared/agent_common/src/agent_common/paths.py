"""Shared conventions for where agent state lives.

Every agent's ComponentStore reads/writes under one common data directory so
cross-agent dependency checks (ComponentStore.peek) can find each other's
state, the same way real agents would look up a peer's status via the state
store (target architecture §4) rather than each keeping isolated state.
"""
from __future__ import annotations

import os
from pathlib import Path


def shared_data_dir(repo_root: str | Path) -> Path:
    override = os.environ.get("DOCUMENTUM_AI_PLATFORM_DATA_DIR")
    if override:
        return Path(override)
    return Path(repo_root) / "mcp" / "_shared" / "data"


def vault_path(repo_root: str | Path) -> Path:
    override = os.environ.get("DOCUMENTUM_AI_PLATFORM_VAULT_PATH")
    if override:
        return Path(override)
    return shared_data_dir(repo_root) / "vault.json"


def compatibility_dir(repo_root: str | Path) -> Path:
    override = os.environ.get("DOCUMENTUM_AI_PLATFORM_COMPATIBILITY_DIR")
    if override:
        return Path(override)
    return Path(repo_root) / "compatibility"


def repo_root_from_agent_package(package_file: str) -> Path:
    """Given an agent's server.py's __file__, return the documentum-ai-platform
    repo root. Assumes the standard layout: mcp/<name>-mcp/src/<name>_mcp/server.py.
    """
    package_dir = Path(package_file).resolve().parent  # .../<name>_mcp
    agent_dir = package_dir.parent.parent  # .../<name>-mcp
    mcp_dir = agent_dir.parent  # .../mcp
    return mcp_dir.parent  # .../documentum-ai-platform
