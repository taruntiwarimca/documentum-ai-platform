import json

from agent_common.audit import AuditLog
from agent_common.component_store import ComponentStore
from validator_mcp.validator_ops import ValidatorAgent


def _seed_full_green_state(tmp_path, environment):
    ComponentStore(tmp_path, environment, "oracle").update(status="INSTALLED")
    ComponentStore(tmp_path, environment, "oracle").set_resource(
        "databases", "DOCUMDB", {"name": "DOCUMDB"}
    )

    ComponentStore(tmp_path, environment, "content-server").update(status="INSTALLED")
    ComponentStore(tmp_path, environment, "content-server").set_resource(
        "repositories", "DOCBASE01", {"name": "DOCBASE01"}
    )

    ComponentStore(tmp_path, environment, "xplore").update(status="INSTALLED")
    ComponentStore(tmp_path, environment, "xplore").set_resource(
        "collections", "COLL01", {"name": "COLL01"}
    )
    index_dir = tmp_path / environment / "xplore_index"
    index_dir.mkdir(parents=True, exist_ok=True)
    (index_dir / "COLL01.json").write_text(
        json.dumps({"documents": {"doc-1": "hello"}, "postings": {}}), encoding="utf-8"
    )

    ComponentStore(tmp_path, environment, "da").update(
        status="INSTALLED",
        repository="DOCBASE01",
        authentication={"identity_source": "corporate-ldap"},
        last_login_test={"ok": True, "username": "jane.doe"},
    )


def test_golden_transaction_green_when_everything_real_and_ready(tmp_path):
    _seed_full_green_state(tmp_path, "DCTM-DEV")
    audit_log = AuditLog(tmp_path / "audit.db")
    validator = ValidatorAgent(tmp_path, audit_log)

    result = validator.golden_transaction("DCTM-DEV")
    assert result["status"] == "GREEN"
    assert result["steps"]["db"]["ok"] is True
    assert result["steps"]["content_server"]["ok"] is True
    assert result["steps"]["xplore"]["ok"] is True
    assert result["steps"]["da"]["ok"] is True


def test_golden_transaction_red_when_nothing_set_up(tmp_path):
    audit_log = AuditLog(tmp_path / "audit.db")
    validator = ValidatorAgent(tmp_path, audit_log)
    result = validator.golden_transaction("DCTM-DEV")
    assert result["status"] == "RED"
    assert result["steps"]["db"]["ok"] is False


def test_golden_transaction_red_when_da_login_never_passed(tmp_path):
    _seed_full_green_state(tmp_path, "DCTM-DEV")
    # Undo DA's passing login test.
    ComponentStore(tmp_path, "DCTM-DEV", "da").update(last_login_test={"ok": False, "reason": "nope"})

    audit_log = AuditLog(tmp_path / "audit.db")
    validator = ValidatorAgent(tmp_path, audit_log)
    result = validator.golden_transaction("DCTM-DEV")
    assert result["status"] == "RED"
    assert result["steps"]["da"]["ok"] is False


def test_golden_transaction_red_when_xplore_has_no_indexed_documents(tmp_path):
    _seed_full_green_state(tmp_path, "DCTM-DEV")
    index_path = tmp_path / "DCTM-DEV" / "xplore_index" / "COLL01.json"
    index_path.write_text(json.dumps({"documents": {}, "postings": {}}), encoding="utf-8")

    audit_log = AuditLog(tmp_path / "audit.db")
    validator = ValidatorAgent(tmp_path, audit_log)
    result = validator.golden_transaction("DCTM-DEV")
    assert result["status"] == "RED"
    assert result["steps"]["xplore"]["ok"] is False


def test_validate_component_not_found(tmp_path):
    audit_log = AuditLog(tmp_path / "audit.db")
    validator = ValidatorAgent(tmp_path, audit_log)
    result = validator.validate_component("DCTM-DEV", "oracle")
    assert result["healthy"] is False
    assert result["status"] == "NOT_FOUND"


def test_evidence_reads_back_audit_record(tmp_path):
    audit_log = AuditLog(tmp_path / "audit.db")
    event_id = audit_log.record(
        source="DB-MCP",
        event_type="DB_READY",
        environment="DCTM-DEV",
        decision=None,
        evidence=None,
        tool_call={"tool": "oracle.install", "args": {}},
        result={"status": "INSTALLED"},
    )
    validator = ValidatorAgent(tmp_path, audit_log)
    result = validator.evidence(event_id)
    assert result["found"] is True
    assert result["event_type"] == "DB_READY"


def test_evidence_missing_returns_not_found(tmp_path):
    audit_log = AuditLog(tmp_path / "audit.db")
    validator = ValidatorAgent(tmp_path, audit_log)
    assert validator.evidence("EVT-does-not-exist")["found"] is False
