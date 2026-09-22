# OTDS-MCP

Backs OTDS-GROK (`../../agents/`, not yet detailed — see target architecture §6.7). Tool surface (unchanged from the POC): `otds.precheck, otds.health, otds.validate_tls, otds.validate_identity_source, otds.test_authentication, otds.audit`.

Note: the POC's `.grok/skills/otds/SKILL.md` lists a broader "safe tools" set (`otds.get_config, otds.sync_identity_source, otds.create_partition, otds.create_mapping, otds.register_client`) that is not reflected in `config/mcp-tools.yaml`'s allowlist. This scaffold inherits the narrower, enforced allowlist and does not resolve that pre-existing inconsistency.

Design source: target architecture §6.7, §16.5.
