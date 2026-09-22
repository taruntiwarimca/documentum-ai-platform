# COMPATIBILITY-MCP

**Implemented.** Gates every install request against real support-matrix data — no hardcoded rules.

- `compatibility.check_stack(components?)` — reads `../../compatibility/{documentum-23.4,xplore-22.1-p19,da-23.4,tomcat-10}.yaml`'s `status` field.
- `compatibility.check_java(java_version, components?)` — reads `../../compatibility/java.yaml`'s per-version, per-component matrix (ADR-014) and blocks on `UNKNOWN`/`VERIFY`.

Against the real data shipped in this repo: `check_stack()` is APPROVED (the target stack is the project's own accepted design), but `check_java("21")` is BLOCKED (`content_server`/`xplore`/`da` are `UNKNOWN`/`VERIFY` for Java 21) — this is the real, working demonstration of ADR-014's hard-stop, not a canned example.

No dependencies on other agents. Every call is audit-logged.

```bash
pip install -e ".[dev]"
pytest
```

Design source: `../../../documentum-ai-platform-poc/docs/architecture/TARGET_ARCHITECTURE.md` §5, ADR-014.
