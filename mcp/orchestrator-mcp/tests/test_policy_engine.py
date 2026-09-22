from pathlib import Path

from orchestrator_mcp.policy_engine import PolicyEngine

_APPROVALS_YAML = """
default_requires_approval: false
rules:
  - id: destructive-prod
    match:
      environment: PROD
      operation_class: destructive
    requires_approval: true
    reason: "Destructive operations in production require human approval."
  - id: repository-deletion
    match:
      operation: cs.delete_repository
    requires_approval: true
    reason: "Repository deletion requires human approval."
"""

_AUTONOMY_YAML = """
operation_class_required_level:
  read: L1
  write: L2
  destructive: L3
  privileged: L4
environment_max_autonomy:
  DCTM-DEV: L3
  PROD: L1
always_gate_in_prod:
  - destructive
  - privileged
"""


def _engine(tmp_path):
    approvals = tmp_path / "approvals.yaml"
    approvals.write_text(_APPROVALS_YAML, encoding="utf-8")
    autonomy = tmp_path / "destructive-actions.yaml"
    autonomy.write_text(_AUTONOMY_YAML, encoding="utf-8")
    return PolicyEngine(approvals, autonomy)


def test_read_in_dev_is_allowed_no_approval(tmp_path):
    result = _engine(tmp_path).check("cs.health", "DCTM-DEV", operation_class="read")
    assert result.allowed is True
    assert result.requires_approval is False


def test_destructive_in_prod_requires_approval_and_is_blocked_by_autonomy(tmp_path):
    result = _engine(tmp_path).check(
        "cs.delete_repository", "PROD", operation_class="destructive"
    )
    assert result.requires_approval is True
    # PROD's max autonomy is L1; destructive requires L3 -> not autonomously allowed
    assert result.allowed is False


def test_destructive_in_dev_is_allowed_by_autonomy_but_repo_deletion_still_gated(tmp_path):
    engine = _engine(tmp_path)

    generic_destructive = engine.check("cs.restart", "DCTM-DEV", operation_class="destructive")
    assert generic_destructive.allowed is True
    assert generic_destructive.requires_approval is False

    repo_deletion = engine.check("cs.delete_repository", "DCTM-DEV", operation_class="destructive")
    assert repo_deletion.requires_approval is True


def test_real_policy_files_parse_and_gate_prod_destructive():
    repo_root = Path(__file__).resolve().parents[3]  # orchestrator-mcp -> mcp -> documentum-ai-platform
    engine = PolicyEngine(
        approvals_path=repo_root / "policies" / "approvals.yaml",
        autonomy_path=repo_root / "policies" / "destructive-actions.yaml",
    )
    result = engine.check("cs.delete_repository", "PROD", operation_class="destructive")
    assert result.requires_approval is True
    assert result.allowed is False
