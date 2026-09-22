from otds_mcp.otds_ops import OtdsAgent


def test_validate_tls_generates_real_cert(tmp_path):
    agent = OtdsAgent(tmp_path, "DCTM-DEV")
    result = agent.validate_tls("otds01")
    assert result["valid"] is True
    assert "otds01" in result["subject"]
    assert (tmp_path / "DCTM-DEV" / "otds_server.crt").exists()


def test_validate_tls_is_idempotent_reuses_cert(tmp_path):
    agent = OtdsAgent(tmp_path, "DCTM-DEV")
    first = agent.validate_tls("otds01")
    second = agent.validate_tls("otds01")
    assert first["subject"] == second["subject"]
    assert first["not_valid_after"] == second["not_valid_after"]


def test_validate_identity_source_not_configured(tmp_path):
    agent = OtdsAgent(tmp_path, "DCTM-DEV")
    result = agent.validate_identity_source("corporate-ldap")
    assert result["ok"] is False


def test_configure_then_validate_identity_source(tmp_path):
    agent = OtdsAgent(tmp_path, "DCTM-DEV")
    agent.configure_identity_source("corporate-ldap", "ldap")
    result = agent.validate_identity_source("corporate-ldap")
    assert result["ok"] is True
    assert result["type"] == "ldap"


def test_authentication_with_correct_password(tmp_path):
    agent = OtdsAgent(tmp_path, "DCTM-DEV")
    agent.register_user("jane.doe", "correct-horse-battery-staple")
    result = agent.test_authentication("jane.doe", "correct-horse-battery-staple")
    assert result["authenticated"] is True


def test_authentication_with_wrong_password(tmp_path):
    agent = OtdsAgent(tmp_path, "DCTM-DEV")
    agent.register_user("jane.doe", "correct-horse-battery-staple")
    result = agent.test_authentication("jane.doe", "wrong-password")
    assert result["authenticated"] is False


def test_authentication_unknown_user(tmp_path):
    agent = OtdsAgent(tmp_path, "DCTM-DEV")
    result = agent.test_authentication("nobody", "whatever")
    assert result["authenticated"] is False
    assert result["reason"] == "unknown user"


def test_password_hash_is_not_stored_in_plaintext(tmp_path):
    agent = OtdsAgent(tmp_path, "DCTM-DEV")
    agent.register_user("jane.doe", "correct-horse-battery-staple")
    stored = agent._store.get_resource("users", "jane.doe")
    assert "correct-horse-battery-staple" not in stored["password_hash"]


def test_health_reflects_tls_and_identity_sources(tmp_path):
    agent = OtdsAgent(tmp_path, "DCTM-DEV")
    assert agent.health()["healthy"] is False
    agent.validate_tls("otds01")
    agent.configure_identity_source("corporate-ldap", "ldap")
    health = agent.health()
    assert health["healthy"] is True
    assert "corporate-ldap" in health["identity_sources"]
