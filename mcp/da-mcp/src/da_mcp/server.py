"""DA-MCP: Documentum Administrator stand-in (see da_ops.py for what "real"
means here, especially login_test)."""
from __future__ import annotations

from agent_common.audit import AuditLog
from agent_common.paths import repo_root_from_agent_package, shared_data_dir
from mcp.server.mcpserver import MCPServer

from .da_ops import DaAgent, DependencyError

_REPO_ROOT = repo_root_from_agent_package(__file__)
_DATA_DIR = shared_data_dir(_REPO_ROOT)

audit_log = AuditLog(_DATA_DIR / "audit.db")
_agents: dict[str, DaAgent] = {}


def _agent(environment: str) -> DaAgent:
    if environment not in _agents:
        _agents[environment] = DaAgent(_DATA_DIR, environment)
    return _agents[environment]


def _audit(environment: str, event_type: str, tool: str, args: dict, result: dict) -> None:
    audit_log.record(
        source="DA-MCP",
        event_type=event_type,
        environment=environment,
        decision=None,
        evidence=None,
        tool_call={"tool": tool, "args": args},
        result=result,
    )


mcp = MCPServer("da-mcp")


@mcp.tool(name="da.precheck")
def da_precheck(environment: str) -> dict:
    result = _agent(environment).precheck()
    _audit(environment, "DA_PRECHECK", "da.precheck", {"environment": environment}, result)
    return result


@mcp.tool(name="da.deploy")
def da_deploy(environment: str, repository: str) -> dict:
    args = {"environment": environment, "repository": repository}
    try:
        result = _agent(environment).deploy(repository)
    except DependencyError as exc:
        result = {"ok": False, "error": str(exc)}
        _audit(environment, "DA_DEPLOY_FAILED", "da.deploy", args, result)
        return result
    _audit(environment, "DA_READY", "da.deploy", args, result)
    return result


@mcp.tool(name="da.configure_authentication")
def da_configure_authentication(environment: str, identity_source: str) -> dict:
    args = {"environment": environment, "identity_source": identity_source}
    try:
        result = _agent(environment).configure_authentication(identity_source)
    except DependencyError as exc:
        result = {"ok": False, "error": str(exc)}
        _audit(environment, "DA_CONFIGURE_AUTHENTICATION_FAILED", "da.configure_authentication", args, result)
        return result
    _audit(environment, "DA_AUTHENTICATION_CONFIGURED", "da.configure_authentication", args, result)
    return result


@mcp.tool(name="da.health")
def da_health(environment: str) -> dict:
    result = _agent(environment).health()
    _audit(environment, "DA_HEALTH_CHECKED", "da.health", {"environment": environment}, result)
    return result


@mcp.tool(name="da.login_test")
def da_login_test(environment: str, username: str, password: str) -> dict:
    result = _agent(environment).login_test(username, password)
    _audit(
        environment,
        "DA_LOGIN_TEST_PASSED" if result["ok"] else "DA_LOGIN_TEST_FAILED",
        "da.login_test",
        {"environment": environment, "username": username},
        result,
    )
    return result


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
