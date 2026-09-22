"""Real local operations standing in for xPlore 22.1 Patch 19.

No real xPlore instance is reachable in this environment. Collections get a
real local JSON inverted index (token -> document ids); search_test performs
genuine token-intersection search over indexed documents, not a canned
result. register_repository performs a real cross-component dependency
check against CS-MCP's state (target architecture §6.4's dependency chain:
Oracle -> Content Server -> Repository -> xPlore registration).

index_document goes beyond the eight tools documented for `xplore` in
documentum-ai-platform-poc/config/mcp-tools.yaml — it exists only so
search_test has real documents to search; see the README for this scope note.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from agent_common.component_store import ComponentStore


class DependencyError(ValueError):
    """Raised when a required upstream component/resource doesn't exist."""


class XploreAgent:
    def __init__(self, data_dir: str | Path, environment: str) -> None:
        self._data_dir = Path(data_dir)
        self._environment = environment
        self._store = ComponentStore(self._data_dir, environment, "xplore")

    def _collection_index_path(self, collection: str) -> Path:
        return self._data_dir / self._environment / "xplore_index" / f"{collection}.json"

    def precheck(self) -> dict[str, Any]:
        cs_state = ComponentStore.peek(self._data_dir, self._environment, "content-server")
        cs_installed = bool(cs_state and cs_state.get("status") == "INSTALLED")
        return {"ok": True, "content_server_installed": cs_installed}

    def install(self) -> dict[str, Any]:
        data = self._store.read()
        if data["status"] == "INSTALLED":
            return {"already_installed": True, **data}
        data = self._store.update(status="INSTALLED")
        return {"already_installed": False, **data}

    def configure(self, index_root: str = "default") -> dict[str, Any]:
        path = self._data_dir / self._environment / "xplore_index"
        path.mkdir(parents=True, exist_ok=True)
        record = {"index_root": index_root, "path": str(path)}
        self._store.update(configuration=record)
        return record

    def register_repository(self, repository: str) -> dict[str, Any]:
        cs_state = ComponentStore.peek(self._data_dir, self._environment, "content-server")
        if not cs_state or repository not in cs_state.get("resources", {}).get("repositories", {}):
            raise DependencyError(
                f"repository {repository!r} does not exist in CS-MCP's state — "
                "create it there first (Content Server -> Repository -> xPlore registration)"
            )
        record = {"repository": repository}
        self._store.set_resource("registered_repositories", repository, record)
        return record

    def create_collection(self, name: str, repository: str) -> dict[str, Any]:
        if not self._store.has_resource("registered_repositories", repository):
            raise DependencyError(
                f"repository {repository!r} is not registered — call register_repository first"
            )
        record = {"name": name, "repository": repository}
        self._store.set_resource("collections", name, record)
        index_path = self._collection_index_path(name)
        index_path.parent.mkdir(parents=True, exist_ok=True)
        if not index_path.exists():
            index_path.write_text(json.dumps({"documents": {}, "postings": {}}), encoding="utf-8")
        return record

    def index_document(self, collection: str, doc_id: str, text: str) -> dict[str, Any]:
        if not self._store.has_resource("collections", collection):
            raise DependencyError(f"collection {collection!r} does not exist — create it first")
        index_path = self._collection_index_path(collection)
        index = (
            json.loads(index_path.read_text(encoding="utf-8"))
            if index_path.exists()
            else {"documents": {}, "postings": {}}
        )
        index["documents"][doc_id] = text
        tokens = set(text.lower().split())
        for tok in tokens:
            postings = index["postings"].setdefault(tok, [])
            if doc_id not in postings:
                postings.append(doc_id)
        index_path.write_text(json.dumps(index), encoding="utf-8")
        return {"doc_id": doc_id, "indexed": True, "tokens": len(tokens)}

    def index_status(self, collection: str) -> dict[str, Any]:
        if not self._store.has_resource("collections", collection):
            return {"exists": False, "document_count": 0}
        index_path = self._collection_index_path(collection)
        doc_count = 0
        if index_path.exists():
            index = json.loads(index_path.read_text(encoding="utf-8"))
            doc_count = len(index.get("documents", {}))
        return {"exists": True, "document_count": doc_count}

    def search_test(self, collection: str, query: str) -> dict[str, Any]:
        index_path = self._collection_index_path(collection)
        if not index_path.exists():
            return {"ok": False, "hits": [], "reason": "collection not indexed yet"}
        index = json.loads(index_path.read_text(encoding="utf-8"))
        tokens = query.lower().split()
        if not tokens:
            return {"ok": False, "hits": [], "reason": "empty query"}
        doc_sets = [set(index["postings"].get(tok, [])) for tok in tokens]
        hits = set.intersection(*doc_sets) if doc_sets else set()
        return {"ok": len(hits) > 0, "hits": sorted(hits), "query": query}

    def health(self) -> dict[str, Any]:
        data = self._store.read()
        collections = data.get("resources", {}).get("collections", {})
        return {
            "status": data["status"],
            "healthy": data["status"] == "INSTALLED",
            "collections": list(collections.keys()),
        }
