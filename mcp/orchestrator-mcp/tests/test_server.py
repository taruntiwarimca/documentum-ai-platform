"""Integration test: calls all four tools through the real MCP protocol
dispatch (MCPServer.call_tool), not by invoking the Python functions directly.
"""
from __future__ import annotations

import asyncio
import importlib
import json

import pytest


@pytest.fixture()
def server_module(tmp_path, monkeypatch):
    (tmp_path / "approvals.yaml").write_text(
        "default_requires_approval: false\n"
        "rules:\n"
        "  - id: repository-deletion\n"
        "    match:\n"
        "      operation: cs.delete_repository\n"
        "    requires_approval: true\n"
        "    reason: Repository deletion requires human approval.\n",
        encoding="utf-8",
    )
    (tmp_path / "destructive-actions.yaml").write_text(
        "operation_class_required_level:\n"
        "  read: L1\n  write: L2\n  destructive: L3\n  privileged: L4\n"
        "environment_max_autonomy:\n"
        "  DCTM-DEV: L3\n  PROD: L1\n"
        "always_gate_in_prod:\n"
        "  - destructive\n"
        "  - privileged\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("ORCHESTRATOR_MCP_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("ORCHESTRATOR_MCP_POLICIES_DIR", str(tmp_path))
    # audit_log now lives under the shared data dir (see server.py) so every
    # agent writes to one trail — isolate that too for this test.
    monkeypatch.setenv("DOCUMENTUM_AI_PLATFORM_DATA_DIR", str(tmp_path / "shared-data"))

    import orchestrator_mcp.server as module

    importlib.reload(module)
    return module


def _call(module, name: str, arguments: dict) -> dict:
    result = asyncio.run(module.mcp.call_tool(name, arguments))
    assert result.is_error is False, result
    return json.loads(result.content[0].text)


def test_state_set_then_get_roundtrip(server_module):
    _call(
        server_module,
        "state.set",
        {"environment": "DCTM-DEV", "key": "content_server.host", "value": "dmcs01"},
    )
    result = _call(
        server_module,
        "state.get",
        {"environment": "DCTM-DEV", "key": "content_server.host"},
    )
    assert result == {"found": True, "value": "dmcs01"}


def test_state_get_missing_key(server_module):
    result = _call(server_module, "state.get", {"environment": "DCTM-DEV", "key": "nope"})
    assert result == {"found": False, "value": None}


def test_policy_check_allows_read(server_module):
    result = _call(
        server_module,
        "policy.check",
        {"operation": "cs.health", "environment": "DCTM-DEV", "operation_class": "read"},
    )
    assert result["allowed"] is True
    assert result["requires_approval"] is False


def test_policy_check_gates_repository_deletion(server_module):
    result = _call(
        server_module,
        "policy.check",
        {
            "operation": "cs.delete_repository",
            "environment": "DCTM-DEV",
            "operation_class": "destructive",
        },
    )
    assert result["requires_approval"] is True


def test_approval_request_creates_pending_record(server_module):
    result = _call(
        server_module,
        "approval.request",
        {
            "operation": "cs.delete_repository",
            "environment": "DCTM-DEV",
            "resource": "DOCBASE01",
            "requested_by": "orchestrator-grok",
            "reason": "Policy check flagged this operation as requiring approval.",
        },
    )
    assert result["status"] == "PENDING"
    assert result["operation"] == "cs.delete_repository"

    pending = server_module.approval_store.list_pending()
    assert any(p["approval_id"] == result["approval_id"] for p in pending)


def test_every_call_is_audited(server_module):
    _call(server_module, "state.set", {"environment": "DCTM-DEV", "key": "k", "value": "v"})
    _call(server_module, "state.get", {"environment": "DCTM-DEV", "key": "k"})
    _call(
        server_module,
        "policy.check",
        {"operation": "cs.health", "environment": "DCTM-DEV", "operation_class": "read"},
    )
    _call(
        server_module,
        "approval.request",
        {"operation": "cs.delete_repository", "environment": "DCTM-DEV"},
    )

    events = server_module.audit_log.all()
    event_types = {e["event_type"] for e in events}
    assert {"STATE_SET", "STATE_GET", "POLICY_CHECK", "APPROVAL_REQUESTED"} <= event_types
    assert all(e["source"] == "ORCHESTRATOR-MCP" for e in events)
