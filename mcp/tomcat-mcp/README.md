# TOMCAT-MCP

**Implemented** — a Tomcat 10 stand-in, since none is reachable in this environment. `tomcat.precheck` is the meaningful piece: it reads the real `../../compatibility/java.yaml` matrix (ADR-014) and hard-stops if `content_server`, `xplore`, or `da` is `UNKNOWN`/`VERIFY` for the requested Java version — Tomcat's own JDK support does not imply every Documentum component deployed to it is certified for that JDK.

Tools: `tomcat.precheck, tomcat.install, tomcat.health`.

```bash
pip install -e ".[dev]"
pytest
```

Design source: `../../../documentum-ai-platform-poc/docs/architecture/TARGET_ARCHITECTURE.md` §5, §6.5, ADR-014.
