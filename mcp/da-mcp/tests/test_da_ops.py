import pytest

from agent_common.component_store import ComponentStore
from agent_common.password import hash_password
from da_mcp.da_ops import DaAgent, DependencyError


def _seed_tomcat(tmp_path, environment):
    ComponentStore(tmp_path, environment, "tomcat").update(status="INSTALLED")


def _seed_cs_repository(tmp_path, environment, repository):
    store = ComponentStore(tmp_path, environment, "content-server")
    store.update(status="INSTALLED")
    store.set_resource("repositories", repository, {"name": repository})


def _seed_otds_identity_and_user(tmp_path, environment, identity_source, username, password):
    store = ComponentStore(tmp_path, environment, "otds")
    store.set_resource("identity_sources", identity_source, {"name": identity_source, "type": "ldap"})
    store.set_resource("users", username, hash_password(password))


def test_deploy_fails_without_tomcat(tmp_path):
    agent = DaAgent(tmp_path, "DCTM-DEV")
    with pytest.raises(DependencyError):
        agent.deploy("DOCBASE01")


def test_deploy_fails_without_repository(tmp_path):
    _seed_tomcat(tmp_path, "DCTM-DEV")
    agent = DaAgent(tmp_path, "DCTM-DEV")
    with pytest.raises(DependencyError):
        agent.deploy("DOCBASE01")


def test_deploy_succeeds_with_real_dependencies(tmp_path):
    _seed_tomcat(tmp_path, "DCTM-DEV")
    _seed_cs_repository(tmp_path, "DCTM-DEV", "DOCBASE01")
    agent = DaAgent(tmp_path, "DCTM-DEV")
    result = agent.deploy("DOCBASE01")
    assert result["deployed"] is True


def test_login_test_fails_before_deploy(tmp_path):
    agent = DaAgent(tmp_path, "DCTM-DEV")
    result = agent.login_test("jane.doe", "s3cret")
    assert result["ok"] is False


def test_login_test_full_real_chain(tmp_path):
    _seed_tomcat(tmp_path, "DCTM-DEV")
    _seed_cs_repository(tmp_path, "DCTM-DEV", "DOCBASE01")
    _seed_otds_identity_and_user(tmp_path, "DCTM-DEV", "corporate-ldap", "jane.doe", "s3cret")

    agent = DaAgent(tmp_path, "DCTM-DEV")
    agent.deploy("DOCBASE01")
    agent.configure_authentication("corporate-ldap")

    ok = agent.login_test("jane.doe", "s3cret")
    assert ok["ok"] is True

    bad = agent.login_test("jane.doe", "wrong-password")
    assert bad["ok"] is False
    assert "dential" in bad["reason"] or "OTDS" in bad["reason"]


def test_login_test_fails_if_repository_removed_after_deploy(tmp_path):
    _seed_tomcat(tmp_path, "DCTM-DEV")
    _seed_cs_repository(tmp_path, "DCTM-DEV", "DOCBASE01")
    _seed_otds_identity_and_user(tmp_path, "DCTM-DEV", "corporate-ldap", "jane.doe", "s3cret")

    agent = DaAgent(tmp_path, "DCTM-DEV")
    agent.deploy("DOCBASE01")
    agent.configure_authentication("corporate-ldap")

    # Simulate the repository disappearing from CS-MCP's state after DA was deployed.
    ComponentStore(tmp_path, "DCTM-DEV", "content-server").update(resources={})

    result = agent.login_test("jane.doe", "s3cret")
    assert result["ok"] is False
    assert "trust path" in result["reason"]
