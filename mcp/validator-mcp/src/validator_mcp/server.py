"""VALIDATOR-MCP: golden-transaction aggregation (see validator_ops.py)."""
from __future__ import annotations

from agent_common.audit import AuditLog
from agent_common.paths import repo_root_from_agent_package, shared_data_dir
from mcp.server.mcpserver import MCPServer

from .validator_ops import ValidatorAgent

_REPO_ROOT = repo_root_from_agent_package(__file__)
_DATA_DIR = shared_data_dir(_REPO_ROOT)

audit_log = AuditLog(_DATA_DIR / "audit.db")
validator = ValidatorAgent(_DATA_DIR, audit_log)

mcp = MCPServer("validator-mcp")


def _audit(environment: str | None, event_type: str, tool: str, args: dict, result: dict) -> None:
    audit_log.record(
        source="VALIDATOR-MCP",
        event_type=event_type,
        environment=environment,
        decision=None,
        evidence=None,
        tool_call={"tool": tool, "args": args},
        result=result,
    )


@mcp.tool(name="validate.component")
def validate_component(environment: str, component: str) -> dict:
    result = validator.validate_component(environment, component)
    _audit(environment, "COMPONENT_VALIDATED", "validate.component",
           {"environment": environment, "component": component}, result)
    return result


@mcp.tool(name="validate.golden_transaction")
def validate_golden_transaction(environment: str) -> dict:
    result = validator.golden_transaction(environment)
    _audit(environment, "VALIDATION_PASSED" if result["status"] == "GREEN" else "VALIDATION_FAILED",
           "validate.golden_transaction", {"environment": environment}, result)
    return result


@mcp.tool(name="validate.evidence")
def validate_evidence(operation_id: str) -> dict:
    return validator.evidence(operation_id)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
