# VALIDATOR-GROK

Not detailed with a specific responsibilities/tools list beyond what already exists in the POC. Inherits scope from ADR-008 (Functional Validation) and ADR-010 (Immutable Evidence), and the existing tool allowlist in `config/mcp-tools.yaml`:

```
validate.component, validate.golden_transaction, validate.evidence
```

Owns the golden transaction (auth → repo connect → create/check-in → xPlore index/search → retrieve/checksum → cleanup) and, per DA-GROK's note, the DA → CS `dm_bof_registry` authentication path specifically.

Flagged as open work — see target architecture §6.7 and §16.5.
