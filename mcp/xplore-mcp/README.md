# XPLORE-MCP

Backs XPLORE-GROK (`../../agents/xplore/`). Exposes the typed tool surface listed there, including per-collection resource operations (`create_collection`, `index_status`, `reindex`). A Documentum Automation Worker (see `../../automation/ansible/xplore/`) resolves each typed call to the exact commands.

Design source: target architecture §9, ADR-016.
