# VALIDATOR-MCP

**Implemented.** Aggregates every other agent's real local state into a golden-transaction GREEN/RED verdict (ADR-008: functional validation, not just process/port checks). Does not call other agents' MCP tools itself — that's the orchestrator dispatcher's job (`orchestrator_mcp.deploy_cli`); this agent reads each component's real `ComponentStore`/index files and checks them for real.

- `validate.component(environment, component)` — that component's real recorded status.
- `validate.golden_transaction(environment)` — checks DB (database exists) → CS (repository exists) → xPlore (collection has real indexed documents, not just an empty collection) → DA (deployed, authentication configured, and its last real `login_test` actually passed) → aggregates GREEN/RED with recent audit-event evidence.
- `validate.evidence(operation_id)` — reads a specific record back from the shared audit log (ADR-010).

```bash
pip install -e ".[dev]"
pytest
```

Design source: `../../../documentum-ai-platform-poc/docs/architecture/TARGET_ARCHITECTURE.md` §6.7, §11, §13, ADR-008, ADR-010.
