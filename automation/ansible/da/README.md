# DA automation playbooks

The Documentum Automation Worker layer behind `mcp/da-mcp/`. Each typed tool the model calls (`da.deploy()`, `da.configure_authentication()`, etc.) resolves to a known playbook here, never to model-generated commands.

Design source: target architecture §9, ADR-016.
