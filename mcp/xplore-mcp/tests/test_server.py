from __future__ import annotations

import asyncio
import importlib
import json

import pytest

from agent_common.component_store import ComponentStore


@pytest.fixture()
def server_module(tmp_path, monkeypatch):
    monkeypatch.setenv("DOCUMENTUM_AI_PLATFORM_DATA_DIR", str(tmp_path))

    import xplore_mcp.server as module

    importlib.reload(module)
    return module


def _call(module, name: str, arguments: dict) -> dict:
    result = asyncio.run(module.mcp.call_tool(name, arguments))
    assert result.is_error is False, result
    return json.loads(result.content[0].text)


def test_full_pipeline_with_real_dependency_and_real_search(tmp_path, server_module):
    blocked = _call(
        server_module, "xplore.register_repository", {"environment": "DCTM-DEV", "repository": "DOCBASE01"}
    )
    assert blocked["ok"] is False

    ComponentStore(tmp_path, "DCTM-DEV", "content-server").set_resource(
        "repositories", "DOCBASE01", {"name": "DOCBASE01"}
    )

    _call(server_module, "xplore.install", {"environment": "DCTM-DEV"})
    _call(server_module, "xplore.configure", {"environment": "DCTM-DEV"})
    _call(server_module, "xplore.register_repository", {"environment": "DCTM-DEV", "repository": "DOCBASE01"})
    _call(server_module, "xplore.create_collection", {"environment": "DCTM-DEV", "name": "COLL01", "repository": "DOCBASE01"})
    _call(server_module, "xplore.index_document", {"environment": "DCTM-DEV", "collection": "COLL01", "doc_id": "doc-1", "text": "quarterly report"})

    status = _call(server_module, "xplore.index_status", {"environment": "DCTM-DEV", "collection": "COLL01"})
    assert status["document_count"] == 1

    search = _call(server_module, "xplore.search_test", {"environment": "DCTM-DEV", "collection": "COLL01", "query": "quarterly"})
    assert search["ok"] is True
    assert search["hits"] == ["doc-1"]

    health = _call(server_module, "xplore.health", {"environment": "DCTM-DEV"})
    assert health["healthy"] is True


def test_events_are_audited(server_module):
    _call(server_module, "xplore.install", {"environment": "DCTM-DEV"})
    events = server_module.audit_log.all()
    assert all(e["source"] == "XPLORE-MCP" for e in events)
