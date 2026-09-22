# XPLORE-GROK

Owns xPlore 22.1 Patch 19. Responsibilities:

- Prerequisite validation
- Java validation
- Installation
- Configuration
- Content Server connection
- Repository registration
- Indexing configuration
- Collections
- Indexing agents
- Full-text test
- Reindexing
- Health

Target tools (via `mcp/xplore-mcp/`):

```
xplore.precheck()          xplore.install()            xplore.configure()
xplore.register_repository() xplore.create_collection() xplore.start()
xplore.stop()               xplore.restart()           xplore.health()
xplore.index_status()       xplore.reindex()           xplore.search_test()
xplore.logs()
```

**xPlore is a dependent service, not a peer server.** Hard dependency chain: Oracle → Content Server → Repository → xPlore registration → Index configuration → Test document → Index → Search. The orchestrator must serialize xPlore after CS/repository are READY (it may still run concurrently with the Tomcat/DA branch — see target architecture §7).

**Resource modeling**: collections and indexing agents are first-class resources with their own lifecycle, not hidden inside one opaque `install()`.

Design source: target architecture §6.4.
