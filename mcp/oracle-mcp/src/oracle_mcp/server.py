"""DB-MCP: Oracle stand-in (see oracle_ops.py for what "real" means here)."""
from __future__ import annotations

from agent_common.audit import AuditLog
from agent_common.paths import repo_root_from_agent_package, shared_data_dir
from mcp.server.mcpserver import MCPServer

from .oracle_ops import OracleAgent

_REPO_ROOT = repo_root_from_agent_package(__file__)
_DATA_DIR = shared_data_dir(_REPO_ROOT)

audit_log = AuditLog(_DATA_DIR / "audit.db")
_agents: dict[str, OracleAgent] = {}


def _agent(environment: str) -> OracleAgent:
    if environment not in _agents:
        _agents[environment] = OracleAgent(_DATA_DIR, environment)
    return _agents[environment]


def _audit(environment: str, event_type: str, tool: str, args: dict, result: dict) -> None:
    audit_log.record(
        source="DB-MCP",
        event_type=event_type,
        environment=environment,
        decision=None,
        evidence=None,
        tool_call={"tool": tool, "args": args},
        result=result,
    )


mcp = MCPServer("oracle-mcp")


@mcp.tool(name="oracle.precheck")
def oracle_precheck(environment: str) -> dict:
    result = _agent(environment).precheck()
    _audit(environment, "DB_PRECHECK", "oracle.precheck", {"environment": environment}, result)
    return result


@mcp.tool(name="oracle.install")
def oracle_install(environment: str) -> dict:
    result = _agent(environment).install()
    _audit(environment, "DB_READY" if not result.get("already_installed") else "DB_ALREADY_INSTALLED",
           "oracle.install", {"environment": environment}, result)
    return result


@mcp.tool(name="oracle.create_listener")
def oracle_create_listener(environment: str, name: str, port: int) -> dict:
    result = _agent(environment).create_listener(name, port)
    _audit(environment, "DB_LISTENER_CREATED", "oracle.create_listener",
           {"environment": environment, "name": name, "port": port}, result)
    return result


@mcp.tool(name="oracle.create_database")
def oracle_create_database(environment: str, name: str, service: str = "") -> dict:
    result = _agent(environment).create_database(name, service or None)
    _audit(environment, "DB_DATABASE_CREATED", "oracle.create_database",
           {"environment": environment, "name": name, "service": service}, result)
    return result


@mcp.tool(name="oracle.create_tablespace")
def oracle_create_tablespace(environment: str, database: str, name: str, size_mb: int = 100) -> dict:
    args = {"environment": environment, "database": database, "name": name, "size_mb": size_mb}
    try:
        result = _agent(environment).create_tablespace(database, name, size_mb)
    except ValueError as exc:
        result = {"ok": False, "error": str(exc)}
        _audit(environment, "DB_TABLESPACE_CREATE_FAILED", "oracle.create_tablespace", args, result)
        return result
    _audit(environment, "DB_TABLESPACE_CREATED", "oracle.create_tablespace", args, result)
    return result


@mcp.tool(name="oracle.create_user")
def oracle_create_user(
    environment: str, database: str, name: str, password_hash: str, tablespace: str
) -> dict:
    args = {
        "environment": environment,
        "database": database,
        "name": name,
        "tablespace": tablespace,
    }
    try:
        result = _agent(environment).create_user(database, name, password_hash, tablespace)
    except ValueError as exc:
        result = {"ok": False, "error": str(exc)}
        _audit(environment, "DB_USER_CREATE_FAILED", "oracle.create_user", args, result)
        return result
    _audit(environment, "DB_USER_CREATED", "oracle.create_user", args, result)
    return result


@mcp.tool(name="oracle.test_connection")
def oracle_test_connection(environment: str, database: str) -> dict:
    result = _agent(environment).test_connection(database)
    _audit(environment, "DB_CONNECTION_TESTED", "oracle.test_connection",
           {"environment": environment, "database": database}, result)
    return result


@mcp.tool(name="oracle.health")
def oracle_health(environment: str) -> dict:
    result = _agent(environment).health()
    _audit(environment, "DB_HEALTH_CHECKED", "oracle.health", {"environment": environment}, result)
    return result


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
