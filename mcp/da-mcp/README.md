# DA-MCP

Backs DA-GROK (`../../agents/da/`). Exposes the typed tool surface listed there, including `configure_authentication` and `login_test` which must exercise the `dm_bof_registry` trust path. A Documentum Automation Worker (see `../../automation/ansible/da/`) resolves each typed call to the exact commands.

Design source: target architecture §9, ADR-016.
