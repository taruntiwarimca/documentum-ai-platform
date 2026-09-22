"""OTDS-MCP: OTDS stand-in (see otds_ops.py for what "real" means here)."""
from __future__ import annotations

from agent_common.audit import AuditLog
from agent_common.paths import repo_root_from_agent_package, shared_data_dir
from mcp.server.mcpserver import MCPServer

from .otds_ops import OtdsAgent

_REPO_ROOT = repo_root_from_agent_package(__file__)
_DATA_DIR = shared_data_dir(_REPO_ROOT)

audit_log = AuditLog(_DATA_DIR / "audit.db")
_agents: dict[str, OtdsAgent] = {}


def _agent(environment: str) -> OtdsAgent:
    if environment not in _agents:
        _agents[environment] = OtdsAgent(_DATA_DIR, environment)
    return _agents[environment]


def _audit(environment: str, event_type: str, tool: str, args: dict, result: dict) -> None:
    audit_log.record(
        source="OTDS-MCP",
        event_type=event_type,
        environment=environment,
        decision=None,
        evidence=None,
        tool_call={"tool": tool, "args": args},
        result=result,
    )


mcp = MCPServer("otds-mcp")


@mcp.tool(name="otds.precheck")
def otds_precheck(environment: str) -> dict:
    result = _agent(environment).precheck()
    _audit(environment, "OTDS_PRECHECK", "otds.precheck", {"environment": environment}, result)
    return result


@mcp.tool(name="otds.validate_tls")
def otds_validate_tls(environment: str, common_name: str = "otds01") -> dict:
    result = _agent(environment).validate_tls(common_name)
    _audit(environment, "OTDS_TLS_VALIDATED", "otds.validate_tls",
           {"environment": environment, "common_name": common_name}, result)
    return result


@mcp.tool(name="otds.configure_identity_source")
def otds_configure_identity_source(environment: str, name: str, source_type: str) -> dict:
    result = _agent(environment).configure_identity_source(name, source_type)
    _audit(environment, "OTDS_IDENTITY_SOURCE_CONFIGURED", "otds.configure_identity_source",
           {"environment": environment, "name": name, "source_type": source_type}, result)
    return result


@mcp.tool(name="otds.validate_identity_source")
def otds_validate_identity_source(environment: str, name: str) -> dict:
    result = _agent(environment).validate_identity_source(name)
    _audit(environment, "OTDS_IDENTITY_SOURCE_VALIDATED", "otds.validate_identity_source",
           {"environment": environment, "name": name}, result)
    return result


@mcp.tool(name="otds.register_user")
def otds_register_user(environment: str, username: str, password: str) -> dict:
    result = _agent(environment).register_user(username, password)
    audit_result = {"username": username, "registered": result["registered"]}
    _audit(environment, "OTDS_USER_REGISTERED", "otds.register_user",
           {"environment": environment, "username": username}, audit_result)
    return result


@mcp.tool(name="otds.test_authentication")
def otds_test_authentication(environment: str, username: str, password: str) -> dict:
    result = _agent(environment).test_authentication(username, password)
    _audit(environment, "OTDS_AUTHENTICATION_TESTED", "otds.test_authentication",
           {"environment": environment, "username": username}, result)
    return result


@mcp.tool(name="otds.health")
def otds_health(environment: str) -> dict:
    result = _agent(environment).health()
    _audit(environment, "OTDS_HEALTH_CHECKED", "otds.health", {"environment": environment}, result)
    return result


@mcp.tool(name="otds.audit")
def otds_audit(environment: str, limit: int = 20) -> dict:
    events = [e for e in audit_log.all() if e["environment"] == environment][-limit:]
    return {"environment": environment, "events": events}


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
