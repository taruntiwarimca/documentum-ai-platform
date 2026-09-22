# Content Server automation playbooks

The Documentum Automation Worker layer behind `mcp/content-server-mcp/`. Each typed tool the model calls (`cs.install()`, `cs.create_repository()`, etc.) resolves to a known playbook here, never to model-generated commands.

Design source: target architecture §9, ADR-016.
