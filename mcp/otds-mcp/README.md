# OTDS-MCP

**Implemented** — an OTDS 23.4 stand-in, since none is reachable in this environment, but two pieces are genuinely real: `otds.validate_tls` generates and inspects a real X.509 self-signed certificate (via the `cryptography` package); `otds.test_authentication` checks real PBKDF2-hashed credentials (`agent_common.password`) against a local user store, not a hardcoded `True`.

Matches the six tools already documented for `otds` in `documentum-ai-platform-poc/config/mcp-tools.yaml`: `precheck, health, validate_tls, validate_identity_source, test_authentication, audit`. Two more — `configure_identity_source`, `register_user` — go beyond that allowlist; they exist only so the other four have real state to check against. `otds.audit` returns this environment's recent events from the shared audit log.

**Known pre-existing gap, not resolved here**: `.grok/skills/otds/SKILL.md` lists a broader "safe tools" set than `config/mcp-tools.yaml`'s allowlist — this build follows the narrower, enforced allowlist.

```bash
pip install -e ".[dev]"
pytest
```

Design source: `../../../documentum-ai-platform-poc/docs/architecture/TARGET_ARCHITECTURE.md` §6.7.
