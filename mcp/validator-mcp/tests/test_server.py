from __future__ import annotations

import asyncio
import importlib
import json

import pytest

from agent_common.component_store import ComponentStore


@pytest.fixture()
def server_module(tmp_path, monkeypatch):
    monkeypatch.setenv("DOCUMENTUM_AI_PLATFORM_DATA_DIR", str(tmp_path))

    import validator_mcp.server as module

    importlib.reload(module)
    return module, tmp_path


def _call(module, name: str, arguments: dict) -> dict:
    result = asyncio.run(module.mcp.call_tool(name, arguments))
    assert result.is_error is False, result
    return json.loads(result.content[0].text)


def test_golden_transaction_via_real_mcp_dispatch(server_module):
    module, tmp_path = server_module

    ComponentStore(tmp_path, "DCTM-DEV", "oracle").update(status="INSTALLED")
    ComponentStore(tmp_path, "DCTM-DEV", "oracle").set_resource("databases", "DOCUMDB", {"name": "DOCUMDB"})
    ComponentStore(tmp_path, "DCTM-DEV", "content-server").update(status="INSTALLED")
    ComponentStore(tmp_path, "DCTM-DEV", "content-server").set_resource(
        "repositories", "DOCBASE01", {"name": "DOCBASE01"}
    )
    ComponentStore(tmp_path, "DCTM-DEV", "xplore").update(status="INSTALLED")
    ComponentStore(tmp_path, "DCTM-DEV", "xplore").set_resource("collections", "COLL01", {"name": "COLL01"})
    index_dir = tmp_path / "DCTM-DEV" / "xplore_index"
    index_dir.mkdir(parents=True, exist_ok=True)
    (index_dir / "COLL01.json").write_text(
        json.dumps({"documents": {"doc-1": "hello"}, "postings": {}}), encoding="utf-8"
    )
    ComponentStore(tmp_path, "DCTM-DEV", "da").update(
        status="INSTALLED",
        repository="DOCBASE01",
        authentication={"identity_source": "corporate-ldap"},
        last_login_test={"ok": True},
    )

    result = _call(module, "validate.golden_transaction", {"environment": "DCTM-DEV"})
    assert result["status"] == "GREEN"

    component = _call(module, "validate.component", {"environment": "DCTM-DEV", "component": "oracle"})
    assert component["healthy"] is True


def test_events_are_audited(server_module):
    module, _ = server_module
    _call(module, "validate.golden_transaction", {"environment": "DCTM-DEV"})
    events = module.audit_log.all()
    assert any(e["event_type"] == "VALIDATION_FAILED" for e in events)
    assert all(e["source"] == "VALIDATOR-MCP" for e in events)
