"""APP-MCP: Tomcat stand-in (see tomcat_ops.py for what "real" means here)."""
from __future__ import annotations

from agent_common.audit import AuditLog
from agent_common.paths import compatibility_dir, repo_root_from_agent_package, shared_data_dir
from mcp.server.mcpserver import MCPServer

from .tomcat_ops import TomcatAgent

_REPO_ROOT = repo_root_from_agent_package(__file__)
_DATA_DIR = shared_data_dir(_REPO_ROOT)
_COMPATIBILITY_DIR = compatibility_dir(_REPO_ROOT)

audit_log = AuditLog(_DATA_DIR / "audit.db")
_agents: dict[str, TomcatAgent] = {}


def _agent(environment: str) -> TomcatAgent:
    if environment not in _agents:
        _agents[environment] = TomcatAgent(_DATA_DIR, environment, _COMPATIBILITY_DIR)
    return _agents[environment]


def _audit(environment: str, event_type: str, tool: str, args: dict, result: dict) -> None:
    audit_log.record(
        source="APP-MCP",
        event_type=event_type,
        environment=environment,
        decision=None,
        evidence=None,
        tool_call={"tool": tool, "args": args},
        result=result,
    )


mcp = MCPServer("tomcat-mcp")


@mcp.tool(name="tomcat.precheck")
def tomcat_precheck(environment: str, java_version: str) -> dict:
    result = _agent(environment).precheck(java_version)
    _audit(
        environment,
        "APP_PRECHECK_PASSED" if result["ok"] else "APP_PRECHECK_BLOCKED",
        "tomcat.precheck",
        {"environment": environment, "java_version": java_version},
        result,
    )
    return result


@mcp.tool(name="tomcat.install")
def tomcat_install(environment: str, java_version: str) -> dict:
    result = _agent(environment).install(java_version)
    event = "APP_READY" if not result.get("already_installed") else "APP_ALREADY_INSTALLED"
    _audit(environment, event, "tomcat.install", {"environment": environment, "java_version": java_version}, result)
    return result


@mcp.tool(name="tomcat.health")
def tomcat_health(environment: str) -> dict:
    result = _agent(environment).health()
    _audit(environment, "APP_HEALTH_CHECKED", "tomcat.health", {"environment": environment}, result)
    return result


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
