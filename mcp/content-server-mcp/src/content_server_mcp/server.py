"""CS-MCP: Content Server stand-in (see cs_ops.py for what "real" means here)."""
from __future__ import annotations

from agent_common.audit import AuditLog
from agent_common.paths import repo_root_from_agent_package, shared_data_dir
from mcp.server.mcpserver import MCPServer

from .cs_ops import ContentServerAgent, DependencyError

_REPO_ROOT = repo_root_from_agent_package(__file__)
_DATA_DIR = shared_data_dir(_REPO_ROOT)

audit_log = AuditLog(_DATA_DIR / "audit.db")
_agents: dict[str, ContentServerAgent] = {}


def _agent(environment: str) -> ContentServerAgent:
    if environment not in _agents:
        _agents[environment] = ContentServerAgent(_DATA_DIR, environment)
    return _agents[environment]


def _audit(environment: str, event_type: str, tool: str, args: dict, result: dict) -> None:
    audit_log.record(
        source="CS-MCP",
        event_type=event_type,
        environment=environment,
        decision=None,
        evidence=None,
        tool_call={"tool": tool, "args": args},
        result=result,
    )


mcp = MCPServer("content-server-mcp")


@mcp.tool(name="cs.precheck")
def cs_precheck(environment: str) -> dict:
    result = _agent(environment).precheck()
    _audit(environment, "CS_PRECHECK", "cs.precheck", {"environment": environment}, result)
    return result


@mcp.tool(name="cs.install")
def cs_install(environment: str) -> dict:
    result = _agent(environment).install()
    event = "CONTENT_SERVER_INSTALLING" if not result.get("already_installed") else "CONTENT_SERVER_ALREADY_INSTALLED"
    _audit(environment, event, "cs.install", {"environment": environment}, result)
    return result


@mcp.tool(name="cs.configure_docbroker")
def cs_configure_docbroker(environment: str, host: str, port: int) -> dict:
    args = {"environment": environment, "host": host, "port": port}
    try:
        result = _agent(environment).configure_docbroker(host, port)
    except ValueError as exc:
        result = {"ok": False, "error": str(exc)}
        _audit(environment, "CS_DOCBROKER_CONFIGURE_FAILED", "cs.configure_docbroker", args, result)
        return result
    _audit(environment, "CS_DOCBROKER_CONFIGURED", "cs.configure_docbroker", args, result)
    return result


@mcp.tool(name="cs.create_repository")
def cs_create_repository(environment: str, name: str, database: str) -> dict:
    args = {"environment": environment, "name": name, "database": database}
    try:
        result = _agent(environment).create_repository(name, database)
    except DependencyError as exc:
        result = {"ok": False, "error": str(exc)}
        _audit(environment, "REPOSITORY_CREATE_FAILED", "cs.create_repository", args, result)
        return result
    _audit(environment, "REPOSITORY_READY", "cs.create_repository", args, result)
    return result


@mcp.tool(name="cs.configure_global_registry")
def cs_configure_global_registry(environment: str, repository: str) -> dict:
    args = {"environment": environment, "repository": repository}
    try:
        result = _agent(environment).configure_global_registry(repository)
    except DependencyError as exc:
        result = {"ok": False, "error": str(exc)}
        _audit(environment, "CS_GLOBAL_REGISTRY_CONFIGURE_FAILED", "cs.configure_global_registry", args, result)
        return result
    _audit(environment, "CS_GLOBAL_REGISTRY_CONFIGURED", "cs.configure_global_registry", args, result)
    return result


@mcp.tool(name="cs.health")
def cs_health(environment: str) -> dict:
    result = _agent(environment).health()
    event = "CONTENT_SERVER_READY" if result["healthy"] else "CS_UNHEALTHY"
    _audit(environment, event, "cs.health", {"environment": environment}, result)
    return result


@mcp.tool(name="cs.test_repository")
def cs_test_repository(environment: str, name: str) -> dict:
    result = _agent(environment).test_repository(name)
    _audit(environment, "REPOSITORY_READY" if result["ok"] else "REPOSITORY_TEST_FAILED",
           "cs.test_repository", {"environment": environment, "name": name}, result)
    return result


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
