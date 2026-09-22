# DA-MCP

**Implemented** — a Documentum Administrator 23.4 stand-in, since none is reachable in this environment. `da.login_test` is the important one: rather than checking HTTP 200 from Tomcat, it re-verifies the DA → OTDS authentication path for real — reading OTDS-MCP's own user-store state and checking the password with the same PBKDF2 verification OTDS-MCP itself uses (`agent_common.password`) — plus confirming the CS repository it's configured against still exists (the DA → Content Server trust path). This is the target architecture §6.6 requirement made concrete.

Tools: `da.precheck, da.deploy, da.configure_authentication, da.health, da.login_test`. `deploy` requires APP-MCP installed and the CS-MCP repository to exist; `configure_authentication` requires the OTDS-MCP identity source to be configured — both real cross-component checks, not assumed.

```bash
pip install -e ".[dev]"
pytest
```

Design source: `../../../documentum-ai-platform-poc/docs/architecture/TARGET_ARCHITECTURE.md` §6.6.
