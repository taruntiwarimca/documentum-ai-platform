from __future__ import annotations

import asyncio
import importlib
import json

import pytest


@pytest.fixture()
def server_module(tmp_path, monkeypatch):
    vault_path = tmp_path / "vault.json"
    vault_path.write_text(
        json.dumps({"dctm": {"oracle": {"admin": "not-a-real-secret"}}}), encoding="utf-8"
    )
    monkeypatch.setenv("DOCUMENTUM_AI_PLATFORM_VAULT_PATH", str(vault_path))
    monkeypatch.setenv("DOCUMENTUM_AI_PLATFORM_DATA_DIR", str(tmp_path / "data"))

    import security_mcp.server as module

    importlib.reload(module)
    return module


def _call(module, name: str, arguments: dict) -> dict:
    result = asyncio.run(module.mcp.call_tool(name, arguments))
    assert result.is_error is False, result
    return json.loads(result.content[0].text)


def test_resolve_found(server_module):
    result = _call(server_module, "secret.resolve", {"ref": "vault://dctm/oracle/admin"})
    assert result == {"found": True, "value": "not-a-real-secret"}


def test_resolve_not_found(server_module):
    result = _call(server_module, "secret.resolve", {"ref": "vault://dctm/oracle/nope"})
    assert result == {"found": False, "value": None}


def test_audit_log_redacts_secret_value(server_module):
    _call(server_module, "secret.resolve", {"ref": "vault://dctm/oracle/admin"})
    events = server_module.audit_log.all()
    assert len(events) == 1
    result_json = events[0]["result"]
    assert "not-a-real-secret" not in result_json
    assert "REDACTED" in result_json
