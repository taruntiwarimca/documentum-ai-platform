from __future__ import annotations

import asyncio
import importlib
import json

import pytest


@pytest.fixture()
def server_module(tmp_path, monkeypatch):
    (tmp_path / "documentum-23.4.yaml").write_text(
        "component: content-server\nversion: '23.4'\nstatus: SUPPORTED\n", encoding="utf-8"
    )
    (tmp_path / "java.yaml").write_text(
        "java:\n  '21':\n    content_server: UNKNOWN\n    tomcat: SUPPORTED_BY_TOMCAT\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("DOCUMENTUM_AI_PLATFORM_COMPATIBILITY_DIR", str(tmp_path))
    monkeypatch.setenv("DOCUMENTUM_AI_PLATFORM_DATA_DIR", str(tmp_path / "data"))

    import compatibility_mcp.server as module

    importlib.reload(module)
    return module


def _call(module, name: str, arguments: dict) -> dict:
    result = asyncio.run(module.mcp.call_tool(name, arguments))
    assert result.is_error is False, result
    return json.loads(result.content[0].text)


def test_check_stack_tool(server_module):
    result = _call(server_module, "compatibility.check_stack", {"components": ["content_server"]})
    assert result["approved"] is True


def test_check_java_tool_blocks(server_module):
    result = _call(
        server_module,
        "compatibility.check_java",
        {"java_version": "21", "components": ["content_server"]},
    )
    assert result["approved"] is False


def test_calls_are_audited(server_module):
    _call(server_module, "compatibility.check_stack", {"components": ["content_server"]})
    events = server_module.audit_log.all()
    assert any(e["event_type"] == "COMPATIBILITY_CHECK_STACK" for e in events)
    assert all(e["source"] == "COMPATIBILITY-MCP" for e in events)
