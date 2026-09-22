import pytest

from orchestrator_mcp.state_store import StateNotFoundError, StateStore


def test_set_and_get_current(tmp_path):
    store = StateStore(tmp_path / "state.db")
    store.set("DCTM-DEV", "content_server.host", "dmcs01")
    assert store.get("DCTM-DEV", "content_server.host") == "dmcs01"


def test_get_falls_back_to_desired(tmp_path):
    store = StateStore(tmp_path / "state.db")
    store.set("DCTM-DEV", "content_server.host", "desired-host", namespace="desired")
    assert store.get("DCTM-DEV", "content_server.host") == "desired-host"

    store.set("DCTM-DEV", "content_server.host", "current-host")
    assert store.get("DCTM-DEV", "content_server.host") == "current-host"


def test_get_missing_raises(tmp_path):
    store = StateStore(tmp_path / "state.db")
    with pytest.raises(StateNotFoundError):
        store.get("DCTM-DEV", "nope")


def test_set_persists_across_instances(tmp_path):
    db_path = tmp_path / "state.db"
    StateStore(db_path).set("DCTM-DEV", "k", "v")
    reopened = StateStore(db_path)
    assert reopened.get("DCTM-DEV", "k") == "v"


def test_load_desired_state_from_yaml(tmp_path):
    yaml_path = tmp_path / "desired-state.yaml"
    yaml_path.write_text(
        "content_server:\n  host: dmcs01\n  docbroker:\n    port: 1489\n",
        encoding="utf-8",
    )
    store = StateStore(tmp_path / "state.db")
    count = store.load_desired_state_from_yaml(yaml_path, "DCTM-DEV")
    assert count == 2
    assert store.get("DCTM-DEV", "content_server.host") == "dmcs01"
    assert store.get("DCTM-DEV", "content_server.docbroker.port") == 1489


def test_load_real_poc_desired_state():
    """Sanity-checks against the POC's actual desired-state.yaml, if present."""
    poc_path = (
        __import__("pathlib").Path(__file__).resolve().parents[4]
        / "documentum-ai-platform-poc"
        / "config"
        / "desired-state.yaml"
    )
    if not poc_path.exists():
        pytest.skip("documentum-ai-platform-poc sibling repo not found")

    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        store = StateStore(f"{tmp}/state.db")
        try:
            count = store.load_desired_state_from_yaml(poc_path, "DCTM-DEV")
            assert count > 0
            # Real key per the POC's config/desired-state.yaml structure
            # (hosts: {content_server: dmcs01, ...}), not a nested per-component block.
            assert store.get("DCTM-DEV", "hosts.content_server") == "dmcs01"
        finally:
            store.close()
