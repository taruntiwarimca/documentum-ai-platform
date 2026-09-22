# SECURITY-GROK

Not detailed with a specific responsibilities/tools list during target-architecture design. Inherits scope from ADR-005 (Human Approval Gates), ADR-006 (Secret References Only), and ADR-009 (Graduated Autonomy).

Owns enforcement of the secrets architecture:

```
GROK → SECRET REF → VAULT → execution worker
```

Never Oracle, Documentum, `dm_bof_registry`, admin, or SSH passwords inside a Grok prompt.

Flagged as open work — see target architecture §6.7, §14, §16.5.
