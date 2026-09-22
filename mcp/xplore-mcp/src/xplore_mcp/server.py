"""XPLORE-MCP: xPlore stand-in (see xplore_ops.py for what "real" means here)."""
from __future__ import annotations

from agent_common.audit import AuditLog
from agent_common.paths import repo_root_from_agent_package, shared_data_dir
from mcp.server.mcpserver import MCPServer

from .xplore_ops import DependencyError, XploreAgent

_REPO_ROOT = repo_root_from_agent_package(__file__)
_DATA_DIR = shared_data_dir(_REPO_ROOT)

audit_log = AuditLog(_DATA_DIR / "audit.db")
_agents: dict[str, XploreAgent] = {}


def _agent(environment: str) -> XploreAgent:
    if environment not in _agents:
        _agents[environment] = XploreAgent(_DATA_DIR, environment)
    return _agents[environment]


def _audit(environment: str, event_type: str, tool: str, args: dict, result: dict) -> None:
    audit_log.record(
        source="XPLORE-MCP",
        event_type=event_type,
        environment=environment,
        decision=None,
        evidence=None,
        tool_call={"tool": tool, "args": args},
        result=result,
    )


mcp = MCPServer("xplore-mcp")


@mcp.tool(name="xplore.precheck")
def xplore_precheck(environment: str) -> dict:
    result = _agent(environment).precheck()
    _audit(environment, "XPLORE_PRECHECK", "xplore.precheck", {"environment": environment}, result)
    return result


@mcp.tool(name="xplore.install")
def xplore_install(environment: str) -> dict:
    result = _agent(environment).install()
    event = "XPLORE_INSTALLING" if not result.get("already_installed") else "XPLORE_ALREADY_INSTALLED"
    _audit(environment, event, "xplore.install", {"environment": environment}, result)
    return result


@mcp.tool(name="xplore.configure")
def xplore_configure(environment: str, index_root: str = "default") -> dict:
    result = _agent(environment).configure(index_root)
    _audit(environment, "XPLORE_CONFIGURED", "xplore.configure",
           {"environment": environment, "index_root": index_root}, result)
    return result


@mcp.tool(name="xplore.register_repository")
def xplore_register_repository(environment: str, repository: str) -> dict:
    args = {"environment": environment, "repository": repository}
    try:
        result = _agent(environment).register_repository(repository)
    except DependencyError as exc:
        result = {"ok": False, "error": str(exc)}
        _audit(environment, "XPLORE_REGISTER_REPOSITORY_FAILED", "xplore.register_repository", args, result)
        return result
    _audit(environment, "XPLORE_REPOSITORY_REGISTERED", "xplore.register_repository", args, result)
    return result


@mcp.tool(name="xplore.create_collection")
def xplore_create_collection(environment: str, name: str, repository: str) -> dict:
    args = {"environment": environment, "name": name, "repository": repository}
    try:
        result = _agent(environment).create_collection(name, repository)
    except DependencyError as exc:
        result = {"ok": False, "error": str(exc)}
        _audit(environment, "XPLORE_CREATE_COLLECTION_FAILED", "xplore.create_collection", args, result)
        return result
    _audit(environment, "XPLORE_COLLECTION_CREATED", "xplore.create_collection", args, result)
    return result


@mcp.tool(name="xplore.index_document")
def xplore_index_document(environment: str, collection: str, doc_id: str, text: str) -> dict:
    args = {"environment": environment, "collection": collection, "doc_id": doc_id}
    try:
        result = _agent(environment).index_document(collection, doc_id, text)
    except DependencyError as exc:
        result = {"ok": False, "error": str(exc)}
        _audit(environment, "XPLORE_INDEX_DOCUMENT_FAILED", "xplore.index_document", args, result)
        return result
    _audit(environment, "XPLORE_DOCUMENT_INDEXED", "xplore.index_document", args, result)
    return result


@mcp.tool(name="xplore.index_status")
def xplore_index_status(environment: str, collection: str) -> dict:
    result = _agent(environment).index_status(collection)
    event = "INDEX_READY" if result.get("exists") else "INDEX_NOT_FOUND"
    _audit(environment, event, "xplore.index_status",
           {"environment": environment, "collection": collection}, result)
    return result


@mcp.tool(name="xplore.search_test")
def xplore_search_test(environment: str, collection: str, query: str) -> dict:
    result = _agent(environment).search_test(collection, query)
    _audit(environment, "XPLORE_SEARCH_TESTED", "xplore.search_test",
           {"environment": environment, "collection": collection, "query": query}, result)
    return result


@mcp.tool(name="xplore.health")
def xplore_health(environment: str) -> dict:
    result = _agent(environment).health()
    event = "XPLORE_READY" if result["healthy"] else "XPLORE_UNHEALTHY"
    _audit(environment, event, "xplore.health", {"environment": environment}, result)
    return result


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
