# ORCHESTRATOR-MCP

The model's single MCP entry point. **Implemented** (not a stub): a real MCP server (official Python SDK, `mcp.server.mcpserver.MCPServer`) exposing the four tools allowlisted for `orchestrator` in `documentum-ai-platform-poc/config/mcp-tools.yaml`:

- `state.get` / `state.set` — a SQLite-backed State Store. Reads fall back from `current` (runtime) state to `desired` state if no runtime override exists yet (ADR-004).
- `policy.check` — evaluates real rule data from `../../policies/approvals.yaml` (ADR-005) and `../../policies/destructive-actions.yaml` (ADR-009's L0–L4 autonomy levels) — no hardcoded logic.
- `approval.request` — persists a `PENDING` approval record. There is deliberately no `approval.approve` MCP tool: per ADR-005, approval is a human decision made out-of-band, not something the agent grants itself.

Every call to any of the four tools is written to an `audit_log` table following the `decision + evidence + tool call + result` shape from ADR-010 / target architecture §13.

Routing to other domain MCP servers (`oracle-mcp`, `content-server-mcp`, etc.) is **not implemented yet** — those servers don't exist, so there's nothing to dispatch to. This build covers exactly ORCHESTRATOR-GROK's own state/policy/approval surface.

## Layout

```
pyproject.toml
src/orchestrator_mcp/
  state_store.py    SQLite state store + desired-state.yaml loader
  policy_engine.py  loads/evaluates ../../policies/*.yaml
  approvals.py      approval request persistence
  audit.py          shared audit-log writer
  server.py         the MCPServer app wiring the four tools together
  seed_cli.py       loads a desired-state.yaml into the store
  approve_cli.py    human-facing CLI to list/approve/deny pending approvals
tests/               pytest unit tests + an in-process protocol-level integration test
```

## Running it

```bash
pip install -e ".[dev]"
pytest

# Seed real desired state from the POC repo, then run the server over stdio:
python -m orchestrator_mcp.seed_cli --from ../../../documentum-ai-platform-poc/config/desired-state.yaml --environment DCTM-DEV
python -m orchestrator_mcp.server

# A human decides pending approvals out-of-band:
python -m orchestrator_mcp.approve_cli list
python -m orchestrator_mcp.approve_cli decide APR-xxxxxxxxxxxx APPROVED --by "your.name"
```

Design source: `../../../documentum-ai-platform-poc/docs/architecture/TARGET_ARCHITECTURE.md` §4, §9, §13, ADR-002, ADR-004, ADR-005, ADR-009, ADR-010, ADR-016.
