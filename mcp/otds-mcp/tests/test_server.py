from __future__ import annotations

import asyncio
import importlib
import json

import pytest


@pytest.fixture()
def server_module(tmp_path, monkeypatch):
    monkeypatch.setenv("DOCUMENTUM_AI_PLATFORM_DATA_DIR", str(tmp_path))

    import otds_mcp.server as module

    importlib.reload(module)
    return module


def _call(module, name: str, arguments: dict) -> dict:
    result = asyncio.run(module.mcp.call_tool(name, arguments))
    assert result.is_error is False, result
    return json.loads(result.content[0].text)


def test_full_pipeline(server_module):
    _call(server_module, "otds.precheck", {"environment": "DCTM-DEV"})

    tls = _call(server_module, "otds.validate_tls", {"environment": "DCTM-DEV"})
    assert tls["valid"] is True

    _call(
        server_module,
        "otds.configure_identity_source",
        {"environment": "DCTM-DEV", "name": "corporate-ldap", "source_type": "ldap"},
    )
    identity = _call(
        server_module,
        "otds.validate_identity_source",
        {"environment": "DCTM-DEV", "name": "corporate-ldap"},
    )
    assert identity["ok"] is True

    _call(
        server_module,
        "otds.register_user",
        {"environment": "DCTM-DEV", "username": "jane.doe", "password": "s3cret"},
    )
    auth_ok = _call(
        server_module,
        "otds.test_authentication",
        {"environment": "DCTM-DEV", "username": "jane.doe", "password": "s3cret"},
    )
    assert auth_ok["authenticated"] is True

    auth_bad = _call(
        server_module,
        "otds.test_authentication",
        {"environment": "DCTM-DEV", "username": "jane.doe", "password": "wrong"},
    )
    assert auth_bad["authenticated"] is False

    health = _call(server_module, "otds.health", {"environment": "DCTM-DEV"})
    assert health["healthy"] is True


def test_audit_tool_filters_by_environment(server_module):
    _call(server_module, "otds.precheck", {"environment": "DCTM-DEV"})
    _call(server_module, "otds.precheck", {"environment": "OTHER-ENV"})

    result = _call(server_module, "otds.audit", {"environment": "DCTM-DEV"})
    assert all(e["environment"] == "DCTM-DEV" for e in result["events"])
    assert len(result["events"]) >= 1
