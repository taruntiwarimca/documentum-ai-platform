# documentum-ai-platform

This is the **target-state implementation scaffold** for the autonomous Documentum operations platform designed in [`documentum-ai-platform-poc`](../documentum-ai-platform-poc). The full architecture — logical/physical diagrams, agent roster, MCP topology, event protocol, dependency-graph scheduler, installation state machine, diagnostic pattern, secrets model, and knowledge/retrieval layer — is documented at:

```
../documentum-ai-platform-poc/docs/architecture/TARGET_ARCHITECTURE.md
```

and formalized in ADR-014 through ADR-020 in that repo's `adrs/` directory.

**`mcp/` is real and working** — 10 MCP servers (orchestrator, compatibility, security, oracle, content-server, otds, xplore, tomcat, da, validator), each with real logic and a passing test suite, plus a real dispatcher (`mcp/orchestrator-mcp/src/orchestrator_mcp/deploy_cli.py`) that spawns every domain server as a subprocess and runs the actual dependency-graph pipeline end to end (a real run reaches `GREEN`). `agents/`, `automation/`, `configuration/`, `validation/`, `docs/` are still README-only scaffolding. See each `mcp/*/README.md` for what "real" means there: no licensed Oracle/OpenText installer media is available in this environment, so every agent operates on genuine local state (real SQLite databases, real JSON manifests, real cross-component dependency checks, real password hashing and X.509 cert validation) rather than actual Oracle/Content Server/xPlore/Tomcat/OTDS binaries.

## Layout

| Directory | Purpose |
|---|---|
| `agents/` | Role-based agent definitions (orchestrator, infrastructure, database, content-server, xplore, application-server, da, validator, security, compatibility) — README scaffolding |
| `mcp/` | **Real, tested** MCP server implementations — 1:1 with `agents/`, product-based naming. `mcp/_shared/agent_common/` is the shared library every agent depends on. |
| `automation/` | Ansible playbooks / scripts / templates behind each MCP server (the "Documentum Automation Worker" layer) — README scaffolding |
| `configuration/` | Per-environment desired state (dev, qa, uat, prod) — README scaffolding |
| `compatibility/` | Per-component version support matrices — **real data**, consumed by `mcp/compatibility-mcp` and `mcp/tomcat-mcp` |
| `validation/` | Per-component and end-to-end validation suites — README scaffolding (VALIDATOR-MCP itself is real, in `mcp/validator-mcp`) |
| `policies/` | Approval gates, autonomy levels, destructive-action rules — **real data** (`approvals.yaml`, `destructive-actions.yaml`), consumed by `mcp/orchestrator-mcp`'s policy engine |
| `docs/` | Architecture, runbooks, troubleshooting |

See `docs/architecture/README.md` for the pointer back to the full design, and `mcp/orchestrator-mcp/README.md` for how to run the real end-to-end pipeline.
