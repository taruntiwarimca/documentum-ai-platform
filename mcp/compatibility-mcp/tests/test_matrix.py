from pathlib import Path

from compatibility_mcp.matrix import CompatibilityMatrix

_CS_SUPPORTED = "component: content-server\nversion: '23.4'\nstatus: SUPPORTED\n"
_CS_UNKNOWN = "component: content-server\nversion: '23.4'\nstatus: UNKNOWN\n"
_JAVA_21 = (
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


def test_check_stack_all_supported(tmp_path):
    (tmp_path / "documentum-23.4.yaml").write_text(_CS_SUPPORTED, encoding="utf-8")
    matrix = CompatibilityMatrix(tmp_path)
    result = matrix.check_stack(["content_server"])
    assert result["approved"] is True
    assert result["blocked_components"] == []


def test_check_stack_blocks_unsupported(tmp_path):
    (tmp_path / "documentum-23.4.yaml").write_text(_CS_UNKNOWN, encoding="utf-8")
    matrix = CompatibilityMatrix(tmp_path)
    result = matrix.check_stack(["content_server"])
    assert result["approved"] is False
    assert "content_server" in result["blocked_components"]


def test_check_stack_missing_data_blocks(tmp_path):
    matrix = CompatibilityMatrix(tmp_path)
    result = matrix.check_stack(["content_server"])
    assert result["approved"] is False
    assert result["component_status"]["content_server"] == "NO_DATA"


def test_check_java_21_blocks_on_unknown(tmp_path):
    (tmp_path / "java.yaml").write_text(_JAVA_21, encoding="utf-8")
    matrix = CompatibilityMatrix(tmp_path)
    result = matrix.check_java("21")
    assert result["approved"] is False
    assert "content_server" in result["blocked_components"]
    assert "xplore" in result["blocked_components"]
    assert "da" in result["blocked_components"]
    assert "tomcat" not in result["blocked_components"]


def test_check_java_17_all_supported(tmp_path):
    (tmp_path / "java.yaml").write_text(_JAVA_21, encoding="utf-8")
    matrix = CompatibilityMatrix(tmp_path)
    result = matrix.check_java("17")
    assert result["approved"] is True
    assert result["blocked_components"] == []


def test_real_compatibility_data_java_21_is_blocked():
    """Sanity-checks the real compatibility/*.yaml data this repo ships."""
    repo_root = Path(__file__).resolve().parents[3]  # compatibility-mcp -> mcp -> documentum-ai-platform
    matrix = CompatibilityMatrix(repo_root / "compatibility")
    result = matrix.check_java("21")
    assert result["approved"] is False

    stack_result = matrix.check_stack()
    assert stack_result["approved"] is True
