from agent_common.audit import AuditLog


def test_record_and_read_back(tmp_path):
    log = AuditLog(tmp_path / "audit.db")
    event_id = log.record(
        source="DB-MCP",
        event_type="DB_READY",
        environment="DCTM-DEV",
        decision="ALLOWED",
        evidence={"host": "local-sim"},
        tool_call={"tool": "oracle.install", "args": {}},
        result={"status": "INSTALLED"},
    )
    assert event_id.startswith("EVT-")

    events = log.all()
    assert len(events) == 1
    assert events[0]["event_id"] == event_id
    assert events[0]["source"] == "DB-MCP"

    fetched = log.get(event_id)
    assert fetched["event_type"] == "DB_READY"


def test_get_missing_returns_none(tmp_path):
    log = AuditLog(tmp_path / "audit.db")
    assert log.get("EVT-does-not-exist") is None
