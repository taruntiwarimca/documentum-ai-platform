# ORCHESTRATOR-MCP

The model's single MCP entry point. Routes to every other domain MCP server (`oracle-mcp`, `content-server-mcp`, `xplore-mcp`, `tomcat-mcp`, `da-mcp`, `validator-mcp`, `otds-mcp`, `security-mcp`, `compatibility-mcp`) rather than the model holding direct connections to each.

Tool surface: `state.get, state.set, policy.check, approval.request` — the Policy Engine and State Store described in target architecture §4.

Design source: target architecture §4, §9, ADR-016.
