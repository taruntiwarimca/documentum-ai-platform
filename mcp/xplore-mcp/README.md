# XPLORE-MCP

**Implemented** — an xPlore 22.1 P19 stand-in, since none is reachable in this environment. `xplore.register_repository` performs a real cross-component dependency check against CS-MCP's state (the "Content Server → Repository → xPlore registration" chain, target architecture §6.4). `xplore.search_test` runs a genuine local inverted-index token search over indexed documents — real intersection matching, not a canned hit list.

Tools: `precheck, install, configure, register_repository, create_collection, index_status, search_test, health`, plus `index_document` (beyond the documented eight — needed so `search_test` has real documents to search).

Collections are modeled as first-class resources with their own state, per the "model as resources" principle from target architecture §6.4, rather than being hidden inside one opaque `install()`.

```bash
pip install -e ".[dev]"
pytest
```

Design source: `../../../documentum-ai-platform-poc/docs/architecture/TARGET_ARCHITECTURE.md` §6.4.
