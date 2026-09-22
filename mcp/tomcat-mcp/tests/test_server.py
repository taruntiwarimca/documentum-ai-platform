from __future__ import annotations

import asyncio
import importlib
import json

import pytest


@pytest.fixture()
def server_module(tmp_path, monkeypatch):
    (tmp_path / "java.yaml").write_text(
        "java:\n  '21':\n    content_server: UNKNOWN\n    xplore: UNKNOWN\n"
        "    da: VERIFY\n    tomcat: SUPPORTED_BY_TOMCAT\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("DOCUMENTUM_AI_PLATFORM_COMPATIBILITY_DIR", str(tmp_path))
    monkeypatch.setenv("DOCUMENTUM_AI_PLATFORM_DATA_DIR", str(tmp_path / "data"))

    import tomcat_mcp.server as module

    importlib.reload(module)
    return module


def _call(module, name: str, arguments: dict) -> dict:
    result = asyncio.run(module.mcp.call_tool(name, arguments))
    assert result.is_error is False, result
    return json.loads(result.content[0].text)


def test_precheck_blocks_java_21_via_real_dispatch(server_module):
    result = _call(server_module, "tomcat.precheck", {"environment": "DCTM-DEV", "java_version": "21"})
    assert result["ok"] is False


def test_install_and_health(server_module):
    _call(server_module, "tomcat.install", {"environment": "DCTM-DEV", "java_version": "17"})
    health = _call(server_module, "tomcat.health", {"environment": "DCTM-DEV"})
    assert health["healthy"] is True
