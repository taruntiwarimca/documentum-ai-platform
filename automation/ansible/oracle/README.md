# Oracle automation playbooks

The Documentum Automation Worker layer behind `mcp/oracle-mcp/`. Each typed tool the model calls (`oracle.install()`, `oracle.create_listener()`, etc.) resolves to a known playbook here, never to model-generated commands.

Design source: target architecture §9, ADR-016.
