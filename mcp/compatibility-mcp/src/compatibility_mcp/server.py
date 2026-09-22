"""COMPATIBILITY-MCP: the stack and Java compatibility gate (ADR-014).

Gates every install request before any domain agent runs (target
architecture §5). No dependencies on other agents.
"""
from __future__ import annotations

from agent_common.audit import AuditLog
from agent_common.paths import compatibility_dir, repo_root_from_agent_package, shared_data_dir
from mcp.server.mcpserver import MCPServer

from .matrix import CompatibilityMatrix

_REPO_ROOT = repo_root_from_agent_package(__file__)
_DATA_DIR = shared_data_dir(_REPO_ROOT)
_COMPATIBILITY_DIR = compatibility_dir(_REPO_ROOT)

audit_log = AuditLog(_DATA_DIR / "audit.db")
matrix = CompatibilityMatrix(_COMPATIBILITY_DIR)

mcp = MCPServer("compatibility-mcp")


@mcp.tool(name="compatibility.check_stack")
def compatibility_check_stack(components: list[str] | None = None) -> dict:
    """Check requested components against their recorded support status."""
    result = matrix.check_stack(components)
    audit_log.record(
        source="COMPATIBILITY-MCP",
        event_type="COMPATIBILITY_CHECK_STACK",
        environment=None,
        decision="APPROVED" if result["approved"] else "BLOCKED",
        evidence={"components": components},
        tool_call={"tool": "compatibility.check_stack", "args": {"components": components}},
        result=result,
    )
    return result


@mcp.tool(name="compatibility.check_java")
def compatibility_check_java(java_version: str, components: list[str] | None = None) -> dict:
    """Check requested components against the Java compatibility matrix."""
    result = matrix.check_java(java_version, components)
    audit_log.record(
        source="COMPATIBILITY-MCP",
        event_type="COMPATIBILITY_CHECK_JAVA",
        environment=None,
        decision="APPROVED" if result["approved"] else "BLOCKED",
        evidence={"java_version": java_version, "components": components},
        tool_call={
            "tool": "compatibility.check_java",
            "args": {"java_version": java_version, "components": components},
        },
        result=result,
    )
    return result


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
