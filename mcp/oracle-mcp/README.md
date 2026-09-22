# ORACLE-MCP

**Implemented** — an Oracle 19c stand-in, since no real Oracle instance is reachable in this environment. "Databases" are real local SQLite files; tablespaces and users are real rows in a catalog table inside that file (genuine SQL DDL/DML, not canned responses). There is no real Oracle listener process: `oracle.create_listener` is administrative record-keeping only, stated in its own return value.

Tools: `oracle.precheck, oracle.install, oracle.create_listener, oracle.create_database, oracle.create_tablespace, oracle.create_user, oracle.test_connection, oracle.health`. `create_tablespace`/`create_user` enforce their real prerequisite chain (database → tablespace → user) and return a graceful `{"ok": false, "error": ...}` rather than crashing if it's violated.

```bash
pip install -e ".[dev]"
pytest
```

Design source: `../../../documentum-ai-platform-poc/docs/architecture/TARGET_ARCHITECTURE.md` §6.2.
