from agent_common.component_store import ComponentStore


def test_initial_state(tmp_path):
    store = ComponentStore(tmp_path, "DCTM-DEV", "oracle")
    data = store.read()
    assert data["status"] == "NOT_INSTALLED"
    assert data["resources"] == {}


def test_update_persists(tmp_path):
    store = ComponentStore(tmp_path, "DCTM-DEV", "oracle")
    store.update(status="INSTALLED")
    reopened = ComponentStore(tmp_path, "DCTM-DEV", "oracle")
    assert reopened.read()["status"] == "INSTALLED"


def test_set_and_get_resource(tmp_path):
    store = ComponentStore(tmp_path, "DCTM-DEV", "oracle")
    store.set_resource("databases", "DOCUMDB", {"service": "DOCUMDB", "created": True})
    assert store.get_resource("databases", "DOCUMDB") == {"service": "DOCUMDB", "created": True}
    assert store.get_resource("databases", "NOPE") is None
    assert store.has_resource("databases", "DOCUMDB") is True
    assert store.has_resource("databases", "NOPE") is False


def test_peek_missing_returns_none(tmp_path):
    assert ComponentStore.peek(tmp_path, "DCTM-DEV", "oracle") is None


def test_peek_reads_another_instance_state(tmp_path):
    ComponentStore(tmp_path, "DCTM-DEV", "oracle").update(status="INSTALLED")
    peeked = ComponentStore.peek(tmp_path, "DCTM-DEV", "oracle")
    assert peeked["status"] == "INSTALLED"
