from __future__ import annotations

import asyncio
import importlib
import json

import pytest


@pytest.fixture()
def server_module(tmp_path, monkeypatch):
    monkeypatch.setenv("DOCUMENTUM_AI_PLATFORM_DATA_DIR", str(tmp_path))

    import oracle_mcp.server as module

    importlib.reload(module)
    return module


def _call(module, name: str, arguments: dict) -> dict:
    result = asyncio.run(module.mcp.call_tool(name, arguments))
    assert result.is_error is False, result
    return json.loads(result.content[0].text)


def test_full_pipeline_through_real_mcp_dispatch(server_module):
    _call(server_module, "oracle.precheck", {"environment": "DCTM-DEV"})
    install = _call(server_module, "oracle.install", {"environment": "DCTM-DEV"})
    assert install["already_installed"] is False

    _call(
        server_module,
        "oracle.create_listener",
        {"environment": "DCTM-DEV", "name": "LISTENER", "port": 1521},
    )
    db = _call(
        server_module,
        "oracle.create_database",
        {"environment": "DCTM-DEV", "name": "DOCUMDB", "service": "DOCUMDB"},
    )
    assert db["service"] == "DOCUMDB"

    _call(
        server_module,
        "oracle.create_tablespace",
        {"environment": "DCTM-DEV", "database": "DOCUMDB", "name": "USERS_TS"},
    )
    _call(
        server_module,
        "oracle.create_user",
        {
            "environment": "DCTM-DEV",
            "database": "DOCUMDB",
            "name": "dm_admin",
            "password_hash": "hashed",
            "tablespace": "USERS_TS",
        },
    )

    conn = _call(
        server_module, "oracle.test_connection", {"environment": "DCTM-DEV", "database": "DOCUMDB"}
    )
    assert conn["connected"] is True

    health = _call(server_module, "oracle.health", {"environment": "DCTM-DEV"})
    assert health["healthy"] is True
    assert "DOCUMDB" in health["databases"]


def test_events_are_audited(server_module):
    _call(server_module, "oracle.install", {"environment": "DCTM-DEV"})
    events = server_module.audit_log.all()
    assert any(e["event_type"] == "DB_READY" for e in events)
    assert all(e["source"] == "DB-MCP" for e in events)
