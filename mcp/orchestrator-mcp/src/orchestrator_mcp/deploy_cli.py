"""Real dispatch: spawns each domain MCP server as a subprocess and calls
its tools in dependency order (target architecture §7), gated by
policy.check / approval.request (ADR-005/009), with every step recorded via
state.set and the shared audit log using the ADR-015 event vocabulary.

    python -m orchestrator_mcp.deploy_cli --environment DCTM-DEV

Not a 5th MCP tool on ORCHESTRATOR-MCP — this keeps the server's tool
surface matching documentum-ai-platform-poc/config/mcp-tools.yaml's
documented allowlist (state.get, state.set, policy.check,
approval.request) unchanged; dispatch is an internal orchestrator
capability, exposed here as a CLI.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any

from agent_common.audit import AuditLog
from agent_common.paths import shared_data_dir
from mcp import Client, StdioServerParameters

from .approvals import ApprovalStore
from .policy_engine import PolicyEngine
from .state_store import StateStore

_PACKAGE_DIR = Path(__file__).resolve().parent
_ORCHESTRATOR_MCP_DIR = _PACKAGE_DIR.parent.parent
_MCP_DIR = _ORCHESTRATOR_MCP_DIR.parent
_REPO_ROOT = _MCP_DIR.parent
_POLICIES_DIR = _REPO_ROOT / "policies"
_DATA_DIR = Path(os.environ.get("ORCHESTRATOR_MCP_DATA_DIR", _ORCHESTRATOR_MCP_DIR / "data"))


async def _call(module: str, tool: str, args: dict[str, Any]) -> dict[str, Any]:
    params = StdioServerParameters(command=sys.executable, args=["-m", module], env=dict(os.environ))
    async with Client(params) as client:
        result = await client.call_tool(tool, args)
        if result.is_error:
            raise RuntimeError(f"{tool} crashed: {result.content}")
        return json.loads(result.content[0].text)


def _failed(result: dict[str, Any]) -> bool:
    return "error" in result or result.get("ok") is False


class Deployment:
    def __init__(self, environment: str) -> None:
        self.environment = environment
        self.java_version = "21"
        self.state = StateStore(_DATA_DIR / "state.db")
        self.approvals = ApprovalStore(_DATA_DIR / "approvals.db")
        self.audit = AuditLog(shared_data_dir(_REPO_ROOT) / "audit.db")
        self.policy = PolicyEngine(
            approvals_path=_POLICIES_DIR / "approvals.yaml",
            autonomy_path=_POLICIES_DIR / "destructive-actions.yaml",
        )

    def _gate(self, operation: str, operation_class: str, resource: str = "") -> bool:
        decision = self.policy.check(operation, self.environment, resource or None, operation_class)
        if decision.requires_approval:
            existing = self.approvals.find_latest(operation, self.environment)
            if existing and existing["status"] == "APPROVED":
                print(f"  [approved earlier: {existing['approval_id']}] {operation}")
                return True
            if existing and existing["status"] == "PENDING":
                print(f"  BLOCKED — awaiting approval {existing['approval_id']} for {operation}")
            else:
                record = self.approvals.request(
                    operation, self.environment, resource or None, "orchestrator-deploy-cli", decision.reason
                )
                print(f"  BLOCKED — approval required for {operation}: {decision.reason}")
                print(f"    Filed {record['approval_id']}.")
            print(
                "    Run: python -m orchestrator_mcp.approve_cli decide <approval_id> APPROVED --by <you>, "
                "then re-run this command."
            )
            return False
        if not decision.allowed:
            print(
                f"  BLOCKED by autonomy policy: {operation} needs "
                f"{decision.autonomy_level_required}, {self.environment} allows up to "
                f"{decision.autonomy_level_max}"
            )
            return False
        return True

    def _record(self, source: str, event_type: str, tool: str, args: dict, result: dict) -> None:
        self.state.set(self.environment, f"last.{tool}", result)
        self.audit.record(
            source=source,
            event_type=event_type,
            environment=self.environment,
            decision=None,
            evidence=None,
            tool_call={"tool": tool, "args": args},
            result=result,
        )

    async def run_compatibility_gate(self) -> bool:
        print("== Compatibility gate ==")
        stack = await _call("compatibility_mcp.server", "compatibility.check_stack", {})
        java = await _call(
            "compatibility_mcp.server", "compatibility.check_java", {"java_version": "21"}
        )
        self._record("COMPATIBILITY-MCP", "COMPATIBILITY_CHECK_STACK", "compatibility.check_stack", {}, stack)
        self._record(
            "COMPATIBILITY-MCP", "COMPATIBILITY_CHECK_JAVA", "compatibility.check_java",
            {"java_version": "21"}, java,
        )
        if not stack["approved"]:
            print(f"  BLOCKED: stack not approved: {stack['blocked_components']}")
            return False
        if not java["approved"]:
            self.java_version = "17"
            print(f"  Java 21 blocked for {java['blocked_components']} (ADR-014) -> using Java 17 instead")
        else:
            print("  stack and Java 21 both approved")
        return True

    async def run_db(self) -> bool:
        print("== DB (Oracle stand-in) ==")
        if not self._gate("oracle.install", "write"):
            return False
        await _call("oracle_mcp.server", "oracle.precheck", {"environment": self.environment})
        await _call("oracle_mcp.server", "oracle.install", {"environment": self.environment})
        await _call(
            "oracle_mcp.server", "oracle.create_listener",
            {"environment": self.environment, "name": "LISTENER", "port": 1521},
        )
        await _call(
            "oracle_mcp.server", "oracle.create_database",
            {"environment": self.environment, "name": "DOCUMDB", "service": "DOCUMDB"},
        )
        await _call(
            "oracle_mcp.server", "oracle.create_tablespace",
            {"environment": self.environment, "database": "DOCUMDB", "name": "USERS_TS"},
        )
        await _call(
            "oracle_mcp.server", "oracle.create_user",
            {
                "environment": self.environment, "database": "DOCUMDB", "name": "dm_admin",
                "password_hash": "placeholder-not-a-real-hash", "tablespace": "USERS_TS",
            },
        )
        health = await _call("oracle_mcp.server", "oracle.health", {"environment": self.environment})
        self._record("DB-MCP", "DB_READY", "oracle.install", {"environment": self.environment}, health)
        print(f"  DB_READY: {health}")
        return health["healthy"]

    async def run_cs(self) -> bool:
        print("== CS (Content Server stand-in) ==")
        if not self._gate("cs.install", "write"):
            return False
        await _call("content_server_mcp.server", "cs.precheck", {"environment": self.environment})
        await _call("content_server_mcp.server", "cs.install", {"environment": self.environment})
        await _call(
            "content_server_mcp.server", "cs.configure_docbroker",
            {"environment": self.environment, "host": "dmcs01", "port": 1489},
        )
        repo = await _call(
            "content_server_mcp.server", "cs.create_repository",
            {"environment": self.environment, "name": "DOCBASE01", "database": "DOCUMDB"},
        )
        if _failed(repo):
            print(f"  BLOCKED: {repo}")
            return False
        await _call(
            "content_server_mcp.server", "cs.configure_global_registry",
            {"environment": self.environment, "repository": "DOCBASE01"},
        )
        health = await _call("content_server_mcp.server", "cs.health", {"environment": self.environment})
        self._record("CS-MCP", "CONTENT_SERVER_READY", "cs.install", {"environment": self.environment}, health)
        print(f"  CONTENT_SERVER_READY: {health}")
        return health["healthy"]

    async def run_otds(self) -> bool:
        print("== OTDS ==")
        await _call("otds_mcp.server", "otds.precheck", {"environment": self.environment})
        tls = await _call("otds_mcp.server", "otds.validate_tls", {"environment": self.environment})
        if not self._gate("otds.configure_identity_source", "write"):
            return False
        await _call(
            "otds_mcp.server", "otds.configure_identity_source",
            {"environment": self.environment, "name": "corporate-ldap", "source_type": "ldap"},
        )
        identity = await _call(
            "otds_mcp.server", "otds.validate_identity_source",
            {"environment": self.environment, "name": "corporate-ldap"},
        )
        await _call(
            "otds_mcp.server", "otds.register_user",
            {"environment": self.environment, "username": "jane.doe", "password": "golden-transaction-demo"},
        )
        health = await _call("otds_mcp.server", "otds.health", {"environment": self.environment})
        self._record("OTDS-MCP", "OTDS_READY", "otds.health", {"environment": self.environment}, health)
        print(f"  OTDS ready: {health}, tls_valid={tls['valid']}, identity_ok={identity['ok']}")
        return health["healthy"]

    async def run_xplore_branch(self) -> bool:
        print("== xPlore branch ==")
        if not self._gate("xplore.install", "write"):
            return False
        await _call("xplore_mcp.server", "xplore.precheck", {"environment": self.environment})
        await _call("xplore_mcp.server", "xplore.install", {"environment": self.environment})
        await _call("xplore_mcp.server", "xplore.configure", {"environment": self.environment})
        reg = await _call(
            "xplore_mcp.server", "xplore.register_repository",
            {"environment": self.environment, "repository": "DOCBASE01"},
        )
        if _failed(reg):
            print(f"  BLOCKED: {reg}")
            return False
        await _call(
            "xplore_mcp.server", "xplore.create_collection",
            {"environment": self.environment, "name": "COLL01", "repository": "DOCBASE01"},
        )
        await _call(
            "xplore_mcp.server", "xplore.index_document",
            {
                "environment": self.environment, "collection": "COLL01", "doc_id": "doc-1",
                "text": "quarterly report golden transaction",
            },
        )
        health = await _call("xplore_mcp.server", "xplore.health", {"environment": self.environment})
        self._record("XPLORE-MCP", "XPLORE_READY", "xplore.health", {"environment": self.environment}, health)
        print(f"  XPLORE_READY: {health}")
        return health["healthy"]

    async def run_app_da_branch(self) -> bool:
        print("== Tomcat/DA branch ==")
        if not self._gate("tomcat.install", "write"):
            return False
        await _call(
            "tomcat_mcp.server", "tomcat.precheck",
            {"environment": self.environment, "java_version": self.java_version},
        )
        await _call(
            "tomcat_mcp.server", "tomcat.install",
            {"environment": self.environment, "java_version": self.java_version},
        )
        app_health = await _call("tomcat_mcp.server", "tomcat.health", {"environment": self.environment})
        self._record("APP-MCP", "APP_READY", "tomcat.health", {"environment": self.environment}, app_health)
        print(f"  APP_READY: {app_health}")
        if not app_health["healthy"]:
            return False

        if not self._gate("da.deploy", "write"):
            return False
        await _call("da_mcp.server", "da.precheck", {"environment": self.environment})
        deploy = await _call(
            "da_mcp.server", "da.deploy", {"environment": self.environment, "repository": "DOCBASE01"}
        )
        if _failed(deploy):
            print(f"  BLOCKED: {deploy}")
            return False
        await _call(
            "da_mcp.server", "da.configure_authentication",
            {"environment": self.environment, "identity_source": "corporate-ldap"},
        )
        login = await _call(
            "da_mcp.server", "da.login_test",
            {"environment": self.environment, "username": "jane.doe", "password": "golden-transaction-demo"},
        )
        da_health = await _call("da_mcp.server", "da.health", {"environment": self.environment})
        self._record("DA-MCP", "DA_READY", "da.login_test", {"environment": self.environment}, login)
        print(f"  DA_READY: {da_health}, login_test={login}")
        return da_health["healthy"] and login["ok"]

    async def run_validation(self) -> dict[str, Any]:
        print("== Validation (golden transaction) ==")
        result = await _call(
            "validator_mcp.server", "validate.golden_transaction", {"environment": self.environment}
        )
        self._record(
            "VALIDATOR-MCP",
            "VALIDATION_PASSED" if result["status"] == "GREEN" else "VALIDATION_FAILED",
            "validate.golden_transaction",
            {"environment": self.environment},
            result,
        )
        return result

    async def run(self) -> int:
        if not await self.run_compatibility_gate():
            return 1
        if not await self.run_db():
            return 1
        if not await self.run_cs():
            return 1
        if not await self.run_otds():
            return 1

        # xPlore and Tomcat/DA are independent siblings under CS in the
        # dependency graph (target architecture §7) — run them concurrently
        # rather than serializing, per ADR-017.
        xplore_ok, app_da_ok = await asyncio.gather(
            self.run_xplore_branch(), self.run_app_da_branch()
        )
        if not (xplore_ok and app_da_ok):
            return 1

        result = await self.run_validation()
        print(f"\n=== {result['status']} ===")
        for name, step in result["steps"].items():
            print(f"  {name}: {'OK' if step['ok'] else 'FAILED'}")
        return 0 if result["status"] == "GREEN" else 1


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the real deployment pipeline (target architecture §7, §11)."
    )
    parser.add_argument("--environment", required=True)
    args = parser.parse_args()

    deployment = Deployment(args.environment)
    exit_code = asyncio.run(deployment.run())
    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
