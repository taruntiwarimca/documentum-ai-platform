"""Real local operations standing in for Documentum Administrator 23.4.

No real DA instance is reachable in this environment. `deploy` performs a
real cross-component check against APP-MCP (Tomcat installed) and CS-MCP
(the target repository exists). `login_test` is the important one: rather
than checking HTTP 200 from Tomcat, it re-verifies the DA -> OTDS
authentication path for real — reading OTDS-MCP's own user-store state
(agent_common.component_store.ComponentStore.peek) and checking the
password with the same PBKDF2 verification OTDS-MCP itself uses
(agent_common.password) — plus confirming the CS repository it's configured
against still exists. This is the target architecture §6.6 requirement:
test the DA -> CS trust/`dm_bof_registry` path for real, not just a status
code.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from agent_common.component_store import ComponentStore
from agent_common.password import verify_password


class DependencyError(ValueError):
    """Raised when a required upstream component/resource doesn't exist."""


class DaAgent:
    def __init__(self, data_dir: str | Path, environment: str) -> None:
        self._data_dir = Path(data_dir)
        self._environment = environment
        self._store = ComponentStore(self._data_dir, environment, "da")

    def _peek(self, component: str) -> dict[str, Any] | None:
        return ComponentStore.peek(self._data_dir, self._environment, component)

    def precheck(self) -> dict[str, Any]:
        tomcat = self._peek("tomcat")
        cs = self._peek("content-server")
        return {
            "ok": True,
            "tomcat_installed": bool(tomcat and tomcat.get("status") == "INSTALLED"),
            "content_server_installed": bool(cs and cs.get("status") == "INSTALLED"),
        }

    def deploy(self, repository: str) -> dict[str, Any]:
        tomcat = self._peek("tomcat")
        if not tomcat or tomcat.get("status") != "INSTALLED":
            raise DependencyError("APP-MCP (Tomcat) is not installed — deploy it first")
        cs = self._peek("content-server")
        if not cs or repository not in cs.get("resources", {}).get("repositories", {}):
            raise DependencyError(
                f"repository {repository!r} does not exist in CS-MCP's state — create it first"
            )
        data = self._store.update(status="INSTALLED", repository=repository)
        return {"deployed": True, "repository": repository, **data}

    def configure_authentication(self, identity_source: str) -> dict[str, Any]:
        otds = self._peek("otds")
        if not otds or identity_source not in otds.get("resources", {}).get(
            "identity_sources", {}
        ):
            raise DependencyError(
                f"identity source {identity_source!r} is not configured in OTDS-MCP's state — "
                "configure it there first"
            )
        record = {"identity_source": identity_source}
        self._store.update(authentication=record)
        return record

    def health(self) -> dict[str, Any]:
        data = self._store.read()
        return {
            "status": data["status"],
            "healthy": data["status"] == "INSTALLED",
            "repository": data.get("repository"),
            "authentication": data.get("authentication"),
        }

    def login_test(self, username: str, password: str) -> dict[str, Any]:
        data = self._store.read()
        if data["status"] != "INSTALLED":
            return {"ok": False, "reason": "DA is not deployed"}
        repository = data.get("repository")
        auth = data.get("authentication")
        if not repository or not auth:
            return {"ok": False, "reason": "DA is not fully configured (repository/authentication)"}

        cs = self._peek("content-server")
        if not cs or repository not in cs.get("resources", {}).get("repositories", {}):
            return {
                "ok": False,
                "reason": f"repository {repository!r} no longer exists in CS-MCP's state — "
                "DA -> Content Server trust path broken",
            }

        otds = self._peek("otds")
        identity_source = auth["identity_source"]
        if not otds or identity_source not in otds.get("resources", {}).get(
            "identity_sources", {}
        ):
            return {
                "ok": False,
                "reason": f"identity source {identity_source!r} no longer configured in OTDS-MCP",
            }

        user_record = otds.get("resources", {}).get("users", {}).get(username)
        if user_record is None:
            result = {"ok": False, "reason": "unknown user in OTDS-MCP's user store"}
            self._store.update(last_login_test=result)
            return result
        if not verify_password(password, user_record["salt"], user_record["password_hash"]):
            result = {"ok": False, "reason": "invalid credentials (DA -> OTDS authentication path)"}
            self._store.update(last_login_test=result)
            return result

        result = {
            "ok": True,
            "username": username,
            "repository": repository,
            "identity_source": identity_source,
        }
        # Recorded so VALIDATOR-MCP's golden transaction can check that a real
        # login was exercised and passed, without re-running it itself.
        self._store.update(last_login_test=result)
        return result
