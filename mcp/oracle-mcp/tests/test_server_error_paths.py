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


def test_create_tablespace_without_database_returns_graceful_error(server_module):
    result = _call(
        server_module,
        "oracle.create_tablespace",
        {"environment": "DCTM-DEV", "database": "DOCUMDB", "name": "USERS_TS"},
    )
    assert result["ok"] is False
    assert "DOCUMDB" in result["error"]


def test_create_user_without_tablespace_returns_graceful_error(server_module):
    _call(
        server_module,
        "oracle.create_database",
        {"environment": "DCTM-DEV", "name": "DOCUMDB"},
    )
    result = _call(
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
    assert result["ok"] is False
    assert "USERS_TS" in result["error"]
