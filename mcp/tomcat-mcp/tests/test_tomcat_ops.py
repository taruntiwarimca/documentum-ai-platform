from tomcat_mcp.tomcat_ops import TomcatAgent

_JAVA_YAML = (
    "java:\n"
    "  '21':\n"
    "    content_server: UNKNOWN\n"
    "    xplore: UNKNOWN\n"
    "    da: VERIFY\n"
    "    tomcat: SUPPORTED_BY_TOMCAT\n"
    "  '17':\n"
    "    content_server: SUPPORTED\n"
    "    xplore: SUPPORTED\n"
    "    da: SUPPORTED\n"
    "    tomcat: SUPPORTED_BY_TOMCAT\n"
)


def _agent(tmp_path):
    (tmp_path / "java.yaml").write_text(_JAVA_YAML, encoding="utf-8")
    return TomcatAgent(tmp_path / "data", "DCTM-DEV", tmp_path)


def test_precheck_blocks_java_21(tmp_path):
    result = _agent(tmp_path).precheck("21")
    assert result["ok"] is False
    assert "content_server" in result["blocked_components"]


def test_precheck_passes_java_17(tmp_path):
    result = _agent(tmp_path).precheck("17")
    assert result["ok"] is True
    assert result["blocked_components"] == []


def test_install_is_idempotent(tmp_path):
    agent = _agent(tmp_path)
    first = agent.install("17")
    assert first["already_installed"] is False
    second = agent.install("17")
    assert second["already_installed"] is True


def test_health_reports_java_version(tmp_path):
    agent = _agent(tmp_path)
    agent.install("17")
    health = agent.health()
    assert health["healthy"] is True
    assert health["java_version"] == "17"
