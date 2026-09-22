# CONTENT-SERVER-MCP

**Implemented** — a Content Server 23.4 stand-in, since none is reachable in this environment. `cs.create_repository` performs a genuine cross-component dependency check by reading ORACLE-MCP's own state file (`agent_common.component_store.ComponentStore.peek`) and fails for real if the target database doesn't exist there — the "Oracle → Content Server → Repository" chain from target architecture §7, enforced rather than assumed.

Tools: `cs.precheck, cs.install, cs.configure_docbroker, cs.create_repository, cs.configure_global_registry, cs.health, cs.test_repository`. `test_repository` re-checks the backing database still exists, catching drift.

```bash
pip install -e ".[dev]"
pytest
```

Design source: `../../../documentum-ai-platform-poc/docs/architecture/TARGET_ARCHITECTURE.md` §6.3.
