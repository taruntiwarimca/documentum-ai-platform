from __future__ import annotations

import asyncio
import importlib
import json

import pytest

from agent_common.component_store import ComponentStore
from agent_common.password import hash_password


@pytest.fixture()
def server_module(tmp_path, monkeypatch):
    monkeypatch.setenv("DOCUMENTUM_AI_PLATFORM_DATA_DIR", str(tmp_path))

    import da_mcp.server as module

    importlib.reload(module)
    return module, tmp_path


def _call(module, name: str, arguments: dict) -> dict:
    result = asyncio.run(module.mcp.call_tool(name, arguments))
    assert result.is_error is False, result
    return json.loads(result.content[0].text)


def test_full_real_chain_via_mcp_dispatch(server_module):
    module, tmp_path = server_module

    ComponentStore(tmp_path, "DCTM-DEV", "tomcat").update(status="INSTALLED")
    ComponentStore(tmp_path, "DCTM-DEV", "content-server").update(status="INSTALLED")
    ComponentStore(tmp_path, "DCTM-DEV", "content-server").set_resource(
        "repositories", "DOCBASE01", {"name": "DOCBASE01"}
    )
    otds = ComponentStore(tmp_path, "DCTM-DEV", "otds")
    otds.set_resource("identity_sources", "corporate-ldap", {"type": "ldap"})
    otds.set_resource("users", "jane.doe", hash_password("s3cret"))

    _call(module, "da.precheck", {"environment": "DCTM-DEV"})
    deploy = _call(module, "da.deploy", {"environment": "DCTM-DEV", "repository": "DOCBASE01"})
    assert deploy["deployed"] is True

    _call(
        module,
        "da.configure_authentication",
        {"environment": "DCTM-DEV", "identity_source": "corporate-ldap"},
    )

    login_ok = _call(
        module, "da.login_test", {"environment": "DCTM-DEV", "username": "jane.doe", "password": "s3cret"}
    )
    assert login_ok["ok"] is True

    login_bad = _call(
        module, "da.login_test", {"environment": "DCTM-DEV", "username": "jane.doe", "password": "nope"}
    )
    assert login_bad["ok"] is False

    health = _call(module, "da.health", {"environment": "DCTM-DEV"})
    assert health["healthy"] is True


def test_deploy_without_tomcat_returns_graceful_error(server_module):
    module, _ = server_module
    result = _call(module, "da.deploy", {"environment": "DCTM-DEV", "repository": "DOCBASE01"})
    assert result["ok"] is False
