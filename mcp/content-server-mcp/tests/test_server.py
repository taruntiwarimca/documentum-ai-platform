from __future__ import annotations

import asyncio
import importlib
import json

import pytest

from agent_common.component_store import ComponentStore


@pytest.fixture()
def server_module(tmp_path, monkeypatch):
    monkeypatch.setenv("DOCUMENTUM_AI_PLATFORM_DATA_DIR", str(tmp_path))

    import content_server_mcp.server as module

    importlib.reload(module)
    return module


def _call(module, name: str, arguments: dict) -> dict:
    result = asyncio.run(module.mcp.call_tool(name, arguments))
    assert result.is_error is False, result
    return json.loads(result.content[0].text)


def test_create_repository_via_real_dispatch_requires_real_oracle_state(tmp_path, server_module):
    failed = _call(
        server_module,
        "cs.create_repository",
        {"environment": "DCTM-DEV", "name": "DOCBASE01", "database": "DOCUMDB"},
    )
    assert failed["ok"] is False
    assert "DOCUMDB" in failed["error"]

    oracle_store = ComponentStore(tmp_path, "DCTM-DEV", "oracle")
    oracle_store.set_resource("databases", "DOCUMDB", {"name": "DOCUMDB"})

    ok_result = _call(
        server_module,
        "cs.create_repository",
        {"environment": "DCTM-DEV", "name": "DOCBASE01", "database": "DOCUMDB"},
    )
    assert ok_result["name"] == "DOCBASE01"


def test_full_pipeline(tmp_path, server_module):
    ComponentStore(tmp_path, "DCTM-DEV", "oracle").set_resource(
        "databases", "DOCUMDB", {"name": "DOCUMDB"}
    )
    _call(server_module, "cs.install", {"environment": "DCTM-DEV"})
    _call(server_module, "cs.configure_docbroker", {"environment": "DCTM-DEV", "host": "dmcs01", "port": 1489})
    _call(server_module, "cs.create_repository", {"environment": "DCTM-DEV", "name": "DOCBASE01", "database": "DOCUMDB"})
    _call(server_module, "cs.configure_global_registry", {"environment": "DCTM-DEV", "repository": "DOCBASE01"})

    health = _call(server_module, "cs.health", {"environment": "DCTM-DEV"})
    assert health["healthy"] is True
    assert "DOCBASE01" in health["repositories"]

    test_result = _call(server_module, "cs.test_repository", {"environment": "DCTM-DEV", "name": "DOCBASE01"})
    assert test_result["ok"] is True


def test_events_are_audited(server_module):
    _call(server_module, "cs.install", {"environment": "DCTM-DEV"})
    events = server_module.audit_log.all()
    assert all(e["source"] == "CS-MCP" for e in events)
