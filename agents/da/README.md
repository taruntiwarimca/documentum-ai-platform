# DA-GROK

Documentum Administrator 23.4 — a web application dependent on Content Server. Responsibilities:

- Java validation
- Tomcat validation
- WAR deployment
- DFC configuration
- Repository connection
- Authentication
- BOF registry
- Configuration
- Startup
- Login test

Target tools (via `mcp/da-mcp/`):

```
da.precheck()   da.install()   da.deploy()   da.configure()
da.configure_repository()   da.configure_authentication()
da.start()   da.health()   da.login_test()   da.logs()
```

**Validation must specifically exercise the DA → Content Server trust/`dm_bof_registry` client-rights authentication path** — not merely check HTTP 200 from Tomcat. There are documented community reports of DA 23.4 environments hitting `dm_bof_registry`/client-rights authentication problems.

Design source: target architecture §6.6.
