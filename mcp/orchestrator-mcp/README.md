# ORCHESTRATOR-MCP

The model's single MCP entry point. **Implemented** (not a stub): a real MCP server (official Python SDK, `mcp.server.mcpserver.MCPServer`) exposing the four tools allowlisted for `orchestrator` in `documentum-ai-platform-poc/config/mcp-tools.yaml`:

- `state.get` / `state.set` — a SQLite-backed State Store. Reads fall back from `current` (runtime) state to `desired` state if no runtime override exists yet (ADR-004).
- `policy.check` — evaluates real rule data from `../../policies/approvals.yaml` (ADR-005) and `../../policies/destructive-actions.yaml` (ADR-009's L0–L4 autonomy levels) — no hardcoded logic.
- `approval.request` — persists a `PENDING` approval record. There is deliberately no `approval.approve` MCP tool: per ADR-005, approval is a human decision made out-of-band, not something the agent grants itself.

Every call to any of the four tools is written to the shared audit log (`mcp/_shared/data/audit.db`, via `agent_common.audit.AuditLog`) following the `decision + evidence + tool call + result` shape from ADR-010 / target architecture §13.

**Dispatch to the other 9 domain agents is implemented** — see `deploy_cli.py` below. It's a CLI, not a 5th MCP tool on this server: that keeps ORCHESTRATOR-MCP's own tool surface matching `config/mcp-tools.yaml`'s documented allowlist unchanged, with dispatch as a separate internal orchestrator capability.

## Layout

```
pyproject.toml
src/orchestrator_mcp/
  state_store.py    SQLite state store + desired-state.yaml loader
  policy_engine.py  loads/evaluates ../../policies/*.yaml
  approvals.py      approval request persistence (+ find_latest, used by deploy_cli)
  audit.py          deprecated re-export of agent_common.audit.AuditLog
  server.py         the MCPServer app wiring the four tools together
  seed_cli.py       loads a desired-state.yaml into the store
  approve_cli.py    human-facing CLI to list/approve/deny pending approvals
  deploy_cli.py     spawns every domain MCP server as a subprocess and runs
                     the real dependency-graph pipeline (target architecture §7)
tests/               pytest unit tests + an in-process protocol-level integration test
```

## Running it

```bash
pip install -e ".[dev]"
pytest

# Seed real desired state from the POC repo, then run the server over stdio:
python -m orchestrator_mcp.seed_cli --from ../../../documentum-ai-platform-poc/config/desired-state.yaml --environment DCTM-DEV
python -m orchestrator_mcp.server

# Run the real end-to-end pipeline (spawns oracle-mcp, content-server-mcp,
# otds-mcp, xplore-mcp, tomcat-mcp, da-mcp, validator-mcp, compatibility-mcp
# as subprocesses and calls their tools for real):
python -m orchestrator_mcp.deploy_cli --environment DCTM-DEV

# A human decides pending approvals out-of-band (deploy_cli stops and tells
# you the approval_id when a step requires one — e.g. OTDS identity-source
# configuration always does, per ADR-005):
python -m orchestrator_mcp.approve_cli list
python -m orchestrator_mcp.approve_cli decide APR-xxxxxxxxxxxx APPROVED --by "your.name"
# then re-run deploy_cli — it picks up the approval and continues.
```

Design source: `../../../documentum-ai-platform-poc/docs/architecture/TARGET_ARCHITECTURE.md` §4, §9, §13, ADR-002, ADR-004, ADR-005, ADR-009, ADR-010, ADR-016.
