from orchestrator_mcp.approvals import ApprovalStore


def test_find_latest_returns_none_when_no_requests(tmp_path):
    store = ApprovalStore(tmp_path / "approvals.db")
    assert store.find_latest("otds.configure_identity_source", "DCTM-DEV") is None


def test_find_latest_returns_most_recent_matching_request(tmp_path):
    store = ApprovalStore(tmp_path / "approvals.db")
    store.request("otds.configure_identity_source", "DCTM-DEV", None, "orchestrator", "reason")
    latest = store.find_latest("otds.configure_identity_source", "DCTM-DEV")
    assert latest is not None
    assert latest["status"] == "PENDING"


def test_find_latest_reflects_decision(tmp_path):
    store = ApprovalStore(tmp_path / "approvals.db")
    record = store.request("otds.configure_identity_source", "DCTM-DEV", None, "orchestrator", "reason")
    store.decide(record["approval_id"], "APPROVED", "jane.doe")
    latest = store.find_latest("otds.configure_identity_source", "DCTM-DEV")
    assert latest["status"] == "APPROVED"


def test_find_latest_does_not_match_other_environment(tmp_path):
    store = ApprovalStore(tmp_path / "approvals.db")
    store.request("otds.configure_identity_source", "DCTM-DEV", None, "orchestrator", "reason")
    assert store.find_latest("otds.configure_identity_source", "PROD") is None
