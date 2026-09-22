# xPlore automation playbooks

The Documentum Automation Worker layer behind `mcp/xplore-mcp/`. Each typed tool the model calls (`xplore.install()`, `xplore.create_collection()`, etc.) resolves to a known playbook here, never to model-generated commands.

Design source: target architecture §9, ADR-016.
