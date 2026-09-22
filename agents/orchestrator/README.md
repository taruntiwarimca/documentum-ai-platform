# ORCHESTRATOR-GROK

The master agent. Responsibilities:

- Parse requested environment
- Load architecture
- Check compatibility (delegates to COMPATIBILITY-GROK, see `../compatibility/`)
- Create dependency graph (see `../../docs/architecture/README.md` → target architecture §7)
- Create execution plan
- Dispatch tasks
- Monitor agents
- Handle failures
- Request approvals
- Trigger rollback
- Run final validation

Tools (via `mcp/orchestrator-mcp/`): `state.get, state.set, policy.check, approval.request`.

Design source: target architecture §6.1, §7, ADR-017.
