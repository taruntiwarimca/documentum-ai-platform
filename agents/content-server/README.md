# CS-GROK

Owns Content Server 23.4 — the most sophisticated agent. Responsibilities:

- Prerequisite validation
- Content Server installation
- DFC/JMS configuration
- Docbroker
- Repository
- Global Registry
- Database connection
- Filesystem/content storage
- ACL/security
- Service management
- Health validation

Target tools (via `mcp/content-server-mcp/`):

```
cs.precheck()              cs.install()                cs.configure()
cs.configure_database()    cs.configure_docbroker()    cs.create_repository()
cs.configure_global_registry() cs.start()  cs.stop()   cs.restart()
cs.health()                 cs.logs()                  cs.test_repository()
```

Machine-readable result contract:

```json
{
  "component": "content-server",
  "version": "23.4",
  "repository": "DOCBASE01",
  "docbroker": { "host": "dmcs01", "port": 1489 },
  "database": "DOCUMDB",
  "status": "READY"
}
```

Design source: target architecture §6.3.
