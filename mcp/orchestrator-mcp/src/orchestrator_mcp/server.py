"""ORCHESTRATOR-MCP: state store, policy engine, and approval requests.

Implements exactly the four tools allowlisted for ``orchestrator`` in
documentum-ai-platform-poc/config/mcp-tools.yaml: state.get, state.set,
policy.check, approval.request. See ADR-002, ADR-004, ADR-005, ADR-009,
ADR-010, ADR-015, ADR-016 and docs/architecture/TARGET_ARCHITECTURE.md
(§4, §9, §13) in the POC repo.
"""
from __future__ import annotations

import os
from pathlib import Path

from agent_common.audit import AuditLog
from agent_common.paths import shared_data_dir
from mcp.server.mcpserver import MCPServer

from .approvals import ApprovalStore
from .policy_engine import PolicyEngine
from .state_store import StateStore

# .../documentum-ai-platform/mcp/orchestrator-mcp/src/orchestrator_mcp/server.py
_PACKAGE_DIR = Path(__file__).resolve().parent
_ORCHESTRATOR_MCP_DIR = _PACKAGE_DIR.parent.parent  # -> mcp/orchestrator-mcp
_REPO_ROOT = _ORCHESTRATOR_MCP_DIR.parent.parent  # -> documentum-ai-platform

# State and approvals are orchestrator-owned (no other agent has its own
# copy). The audit log is the one shared trail every agent writes to
# (mcp/_shared/data/audit.db) so VALIDATOR-MCP's evidence lookups see
# orchestrator-level events too, not just domain-agent ones.
_DATA_DIR = Path(os.environ.get("ORCHESTRATOR_MCP_DATA_DIR", _ORCHESTRATOR_MCP_DIR / "data"))
_POLICIES_DIR = Path(
    os.environ.get("ORCHESTRATOR_MCP_POLICIES_DIR", _REPO_ROOT / "policies")
)

state_store = StateStore(_DATA_DIR / "state.db")
approval_store = ApprovalStore(_DATA_DIR / "approvals.db")
audit_log = AuditLog(shared_data_dir(_REPO_ROOT) / "audit.db")
policy_engine = PolicyEngine(
    approvals_path=_POLICIES_DIR / "approvals.yaml",
    autonomy_path=_POLICIES_DIR / "destructive-actions.yaml",
)

mcp = MCPServer("orchestrator-mcp")


@mcp.tool(name="state.get")
def state_get(environment: str, key: str) -> dict:
    """Read current state for a key, falling back to desired state (ADR-004)."""
    try:
        value = state_store.get(environment, key)
        result = {"found": True, "value": value}
    except KeyError:
        result = {"found": False, "value": None}
    audit_log.record(
        source="ORCHESTRATOR-MCP",
        event_type="STATE_GET",
        environment=environment,
        decision=None,
        evidence=None,
        tool_call={"tool": "state.get", "args": {"environment": environment, "key": key}},
        result=result,
    )
    return result


@mcp.tool(name="state.set")
def state_set(environment: str, key: str, value: str) -> dict:
    """Write current (runtime) state for a key (ADR-004)."""
    state_store.set(environment, key, value, namespace="current")
    result = {"stored": True}
    audit_log.record(
        source="ORCHESTRATOR-MCP",
        event_type="STATE_SET",
        environment=environment,
        decision=None,
        evidence=None,
        tool_call={
            "tool": "state.set",
            "args": {"environment": environment, "key": key, "value": value},
        },
        result=result,
    )
    return result


@mcp.tool(name="policy.check")
def policy_check(
    operation: str,
    environment: str,
    resource: str = "",
    operation_class: str = "read",
) -> dict:
    """Evaluate an operation against approval gates (ADR-005) and autonomy levels (ADR-009)."""
    outcome = policy_engine.check(operation, environment, resource or None, operation_class)
    result = outcome.to_dict()
    audit_log.record(
        source="ORCHESTRATOR-MCP",
        event_type="POLICY_CHECK",
        environment=environment,
        decision="ALLOWED" if result["allowed"] else "BLOCKED",
        evidence={
            "operation": operation,
            "operation_class": operation_class,
            "resource": resource,
        },
        tool_call={
            "tool": "policy.check",
            "args": {
                "operation": operation,
                "environment": environment,
                "resource": resource,
                "operation_class": operation_class,
            },
        },
        result=result,
    )
    return result


@mcp.tool(name="approval.request")
def approval_request(
    operation: str,
    environment: str,
    resource: str = "",
    requested_by: str = "",
    reason: str = "",
) -> dict:
    """Create a PENDING human-approval record (ADR-005).

    Decisions are made out-of-band via approve_cli.py — the agent cannot
    approve its own requests.
    """
    record = approval_store.request(
        operation, environment, resource or None, requested_by or "unknown", reason
    )
    audit_log.record(
        source="ORCHESTRATOR-MCP",
        event_type="APPROVAL_REQUESTED",
        environment=environment,
        decision="PENDING",
        evidence={"operation": operation, "resource": resource, "requested_by": requested_by},
        tool_call={
            "tool": "approval.request",
            "args": {
                "operation": operation,
                "environment": environment,
                "resource": resource,
                "requested_by": requested_by,
                "reason": reason,
            },
        },
        result=record,
    )
    return record


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
