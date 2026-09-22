# agent-common

Shared library used by every agent in `mcp/` — not a standalone agent itself.

- `audit.py` — `AuditLog`: the one shared audit trail (SQLite) every agent writes to, following the `decision + evidence + tool call + result` shape (ADR-010) with the event envelope from ADR-015.
- `component_store.py` — `ComponentStore`: a real JSON-file-backed state manager standing in for "installed component" state (no real Oracle/OpenText installers are available in this environment). `ComponentStore.peek(...)` lets one agent read another's state read-only, which is how real cross-component dependency checks (e.g. CS-MCP requiring DB-MCP's database to exist) work.
- `password.py` — shared PBKDF2 hashing, used by OTDS-MCP (to store/check credentials) and DA-MCP (to verify the DA → OTDS login path for real).
- `secrets_client.py` — resolves `vault://...` references against SECURITY-MCP's local vault file (ADR-006).
- `paths.py` — shared conventions for where all of the above lives (`DOCUMENTUM_AI_PLATFORM_DATA_DIR`, `DOCUMENTUM_AI_PLATFORM_VAULT_PATH`, `DOCUMENTUM_AI_PLATFORM_COMPATIBILITY_DIR` env var overrides, used by every agent's tests for isolation).

Every other `mcp/*-mcp/` package installs this locally: `pip install -e ../_shared/agent_common` before installing itself.

```bash
pip install -e ".[dev]"
pytest
```
