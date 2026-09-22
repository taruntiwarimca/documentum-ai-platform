import pytest

from oracle_mcp.oracle_ops import OracleAgent


def test_precheck_ok_on_writable_dir(tmp_path):
    agent = OracleAgent(tmp_path, "DCTM-DEV")
    result = agent.precheck()
    assert result["ok"] is True
    assert result["writable"] is True


def test_install_is_idempotent(tmp_path):
    agent = OracleAgent(tmp_path, "DCTM-DEV")
    first = agent.install()
    assert first["already_installed"] is False
    second = agent.install()
    assert second["already_installed"] is True


def test_create_database_creates_real_sqlite_file(tmp_path):
    agent = OracleAgent(tmp_path, "DCTM-DEV")
    record = agent.create_database("DOCUMDB")
    assert (tmp_path / "DCTM-DEV" / "oracle_DOCUMDB.sqlite").exists()
    assert record["service"] == "DOCUMDB"


def test_create_tablespace_requires_database_first(tmp_path):
    agent = OracleAgent(tmp_path, "DCTM-DEV")
    with pytest.raises(ValueError):
        agent.create_tablespace("DOCUMDB", "USERS_TS")


def test_create_user_requires_tablespace_first(tmp_path):
    agent = OracleAgent(tmp_path, "DCTM-DEV")
    agent.create_database("DOCUMDB")
    with pytest.raises(ValueError):
        agent.create_user("DOCUMDB", "dm_admin", "hash", "USERS_TS")


def test_full_dependency_chain(tmp_path):
    agent = OracleAgent(tmp_path, "DCTM-DEV")
    agent.create_database("DOCUMDB")
    agent.create_tablespace("DOCUMDB", "USERS_TS")
    record = agent.create_user("DOCUMDB", "dm_admin", "hashed", "USERS_TS")
    assert record["name"] == "dm_admin"


def test_test_connection_fails_for_missing_database(tmp_path):
    agent = OracleAgent(tmp_path, "DCTM-DEV")
    result = agent.test_connection("NOPE")
    assert result["connected"] is False


def test_test_connection_succeeds_for_real_database(tmp_path):
    agent = OracleAgent(tmp_path, "DCTM-DEV")
    agent.create_database("DOCUMDB")
    result = agent.test_connection("DOCUMDB")
    assert result["connected"] is True


def test_health_detects_missing_database_file(tmp_path):
    agent = OracleAgent(tmp_path, "DCTM-DEV")
    agent.install()
    agent.create_database("DOCUMDB")
    (tmp_path / "DCTM-DEV" / "oracle_DOCUMDB.sqlite").unlink()
    result = agent.health()
    assert result["healthy"] is False
    assert "DOCUMDB" in result["missing_database_files"]
