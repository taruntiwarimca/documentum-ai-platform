import pytest

from agent_common.component_store import ComponentStore
from content_server_mcp.cs_ops import ContentServerAgent, DependencyError


def _seed_oracle_database(tmp_path, environment, database):
    store = ComponentStore(tmp_path, environment, "oracle")
    store.update(status="INSTALLED")
    store.set_resource("databases", database, {"name": database, "path": "irrelevant"})


def test_precheck_reports_oracle_not_installed(tmp_path):
    agent = ContentServerAgent(tmp_path, "DCTM-DEV")
    result = agent.precheck()
    assert result["oracle_installed"] is False


def test_precheck_reports_oracle_installed(tmp_path):
    _seed_oracle_database(tmp_path, "DCTM-DEV", "DOCUMDB")
    agent = ContentServerAgent(tmp_path, "DCTM-DEV")
    assert agent.precheck()["oracle_installed"] is True


def test_create_repository_fails_without_database(tmp_path):
    agent = ContentServerAgent(tmp_path, "DCTM-DEV")
    with pytest.raises(DependencyError):
        agent.create_repository("DOCBASE01", "DOCUMDB")


def test_create_repository_succeeds_with_real_database(tmp_path):
    _seed_oracle_database(tmp_path, "DCTM-DEV", "DOCUMDB")
    agent = ContentServerAgent(tmp_path, "DCTM-DEV")
    record = agent.create_repository("DOCBASE01", "DOCUMDB")
    assert record["name"] == "DOCBASE01"


def test_configure_global_registry_requires_repository(tmp_path):
    agent = ContentServerAgent(tmp_path, "DCTM-DEV")
    with pytest.raises(DependencyError):
        agent.configure_global_registry("DOCBASE01")


def test_test_repository_fails_if_database_removed(tmp_path):
    _seed_oracle_database(tmp_path, "DCTM-DEV", "DOCUMDB")
    agent = ContentServerAgent(tmp_path, "DCTM-DEV")
    agent.create_repository("DOCBASE01", "DOCUMDB")

    # Simulate the database disappearing from DB-MCP's state after the fact.
    oracle_store = ComponentStore(tmp_path, "DCTM-DEV", "oracle")
    oracle_store.update(resources={})

    result = agent.test_repository("DOCBASE01")
    assert result["ok"] is False


def test_configure_docbroker_rejects_invalid_port(tmp_path):
    agent = ContentServerAgent(tmp_path, "DCTM-DEV")
    with pytest.raises(ValueError):
        agent.configure_docbroker("dmcs01", 70000)
