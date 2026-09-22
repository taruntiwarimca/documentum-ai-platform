# SECURITY-MCP

**Implemented.** `secret.resolve(ref)` resolves `vault://...` references against a local file-backed vault store (`data/vault.json`, gitignored) — real key lookup, not a stub. The resolved value is returned to the caller but redacted (`***REDACTED***`) in the audit log, so secrets never appear in logs even though the model receives them (ADR-006).

There is deliberately no `secret.put`/write MCP tool — only `seed_cli.py`, a human/ops tool, populates the vault, mirroring `approval.request` having no matching MCP-exposed `approve` tool.

```bash
pip install -e ".[dev]"
pytest

python -m security_mcp.seed_cli put dctm/oracle/admin "not-a-real-secret"
```

Design source: `../../../documentum-ai-platform-poc/docs/architecture/TARGET_ARCHITECTURE.md` §14, ADR-006.
