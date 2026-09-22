"""SECURITY-MCP: secret reference resolution (ADR-006).

Agents resolve vault://... references through this tool rather than
embedding plaintext secrets. The resolved value is returned to the caller
but never written to the audit log (redacted).
"""
from __future__ import annotations

from agent_common.audit import AuditLog
from agent_common.paths import repo_root_from_agent_package, shared_data_dir, vault_path
from agent_common.secrets_client import SecretNotFoundError, resolve_secret
from mcp.server.mcpserver import MCPServer

_REPO_ROOT = repo_root_from_agent_package(__file__)
_DATA_DIR = shared_data_dir(_REPO_ROOT)
_VAULT_PATH = vault_path(_REPO_ROOT)

audit_log = AuditLog(_DATA_DIR / "audit.db")

mcp = MCPServer("security-mcp")


@mcp.tool(name="secret.resolve")
def secret_resolve(ref: str) -> dict:
    """Resolve a vault://... secret reference."""
    try:
        value = resolve_secret(_VAULT_PATH, ref)
        result = {"found": True, "value": value}
        audit_result = {"found": True, "value": "***REDACTED***"}
    except (SecretNotFoundError, ValueError):
        result = {"found": False, "value": None}
        audit_result = result

    audit_log.record(
        source="SECURITY-MCP",
        event_type="SECRET_RESOLVED" if result["found"] else "SECRET_NOT_FOUND",
        environment=None,
        decision=None,
        evidence=None,
        tool_call={"tool": "secret.resolve", "args": {"ref": ref}},
        result=audit_result,
    )
    return result


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
