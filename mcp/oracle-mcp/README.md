# ORACLE-MCP

Backs DB-GROK (`../../agents/database/`). Exposes the typed tool surface listed there; a Documentum Automation Worker (Ansible/Bash/Python/Oracle utilities, see `../../automation/ansible/oracle/`) resolves each typed call to the exact commands — the model never generates shell directly.

Design source: target architecture §9, ADR-016.
