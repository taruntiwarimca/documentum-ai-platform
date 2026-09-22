import pytest

from agent_common.component_store import ComponentStore
from xplore_mcp.xplore_ops import DependencyError, XploreAgent


def _seed_cs_repository(tmp_path, environment, repository):
    store = ComponentStore(tmp_path, environment, "content-server")
    store.update(status="INSTALLED")
    store.set_resource("repositories", repository, {"name": repository, "database": "DOCUMDB"})


def test_register_repository_fails_without_cs_repository(tmp_path):
    agent = XploreAgent(tmp_path, "DCTM-DEV")
    with pytest.raises(DependencyError):
        agent.register_repository("DOCBASE01")


def test_register_repository_succeeds_with_real_cs_state(tmp_path):
    _seed_cs_repository(tmp_path, "DCTM-DEV", "DOCBASE01")
    agent = XploreAgent(tmp_path, "DCTM-DEV")
    result = agent.register_repository("DOCBASE01")
    assert result["repository"] == "DOCBASE01"


def test_create_collection_requires_registered_repository(tmp_path):
    agent = XploreAgent(tmp_path, "DCTM-DEV")
    with pytest.raises(DependencyError):
        agent.create_collection("COLL01", "DOCBASE01")


def test_search_requires_indexed_documents(tmp_path):
    _seed_cs_repository(tmp_path, "DCTM-DEV", "DOCBASE01")
    agent = XploreAgent(tmp_path, "DCTM-DEV")
    agent.register_repository("DOCBASE01")
    agent.create_collection("COLL01", "DOCBASE01")

    empty = agent.search_test("COLL01", "quarterly report")
    assert empty["ok"] is False
    assert empty["hits"] == []

    agent.index_document("COLL01", "doc-1", "Quarterly financial report for Q3")
    agent.index_document("COLL01", "doc-2", "Employee handbook and onboarding guide")

    hit = agent.search_test("COLL01", "quarterly report")
    assert hit["ok"] is True
    assert hit["hits"] == ["doc-1"]

    miss = agent.search_test("COLL01", "quarterly handbook")
    assert miss["ok"] is False


def test_index_status_reports_document_count(tmp_path):
    _seed_cs_repository(tmp_path, "DCTM-DEV", "DOCBASE01")
    agent = XploreAgent(tmp_path, "DCTM-DEV")
    agent.register_repository("DOCBASE01")
    agent.create_collection("COLL01", "DOCBASE01")
    agent.index_document("COLL01", "doc-1", "hello world")
    agent.index_document("COLL01", "doc-2", "another document")

    status = agent.index_status("COLL01")
    assert status["exists"] is True
    assert status["document_count"] == 2
