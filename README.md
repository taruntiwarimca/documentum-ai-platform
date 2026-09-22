# documentum-ai-platform

This is the **target-state implementation scaffold** for the autonomous Documentum operations platform designed in [`documentum-ai-platform-poc`](../documentum-ai-platform-poc). The full architecture — logical/physical diagrams, agent roster, MCP topology, event protocol, dependency-graph scheduler, installation state machine, diagnostic pattern, secrets model, and knowledge/retrieval layer — is documented at:

```
../documentum-ai-platform-poc/docs/architecture/TARGET_ARCHITECTURE.md
```

and formalized in ADR-014 through ADR-020 in that repo's `adrs/` directory.

**Nothing in this repository is implemented yet.** Every directory below contains only a README describing its target purpose. This is a structural scaffold, not working code — matching the POC's own stated boundary (ADR-012: documentation + simulator, not a working integration).

## Layout

| Directory | Purpose |
|---|---|
| `agents/` | Role-based agent definitions (orchestrator, infrastructure, database, content-server, xplore, application-server, da, validator, security, compatibility) |
| `mcp/` | Product-based MCP server implementations — 1:1 with `agents/`, different naming convention |
| `automation/` | Ansible playbooks / scripts / templates behind each MCP server (the "Documentum Automation Worker" layer) |
| `configuration/` | Per-environment desired state (dev, qa, uat, prod) |
| `compatibility/` | Per-component version support matrices |
| `validation/` | Per-component and end-to-end validation suites |
| `policies/` | Approval gates, autonomy levels, destructive-action rules as data |
| `docs/` | Architecture, runbooks, troubleshooting |

See `docs/architecture/README.md` for the pointer back to the full design.
