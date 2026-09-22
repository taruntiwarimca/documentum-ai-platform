"""Policy engine evaluating ADR-005 approval rules and ADR-009 autonomy levels.

Reads real, structured policy data from ``policies/approvals.yaml`` and
``policies/destructive-actions.yaml`` (see the target-architecture repo's
``policies/`` directory) — no hardcoded rules here.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

_LEVEL_ORDER = ["L0", "L1", "L2", "L3", "L4"]


@dataclass
class PolicyResult:
    allowed: bool
    requires_approval: bool
    autonomy_level_required: str
    autonomy_level_max: str
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "allowed": self.allowed,
            "requires_approval": self.requires_approval,
            "autonomy_level_required": self.autonomy_level_required,
            "autonomy_level_max": self.autonomy_level_max,
            "reason": self.reason,
        }


class PolicyEngine:
    def __init__(self, approvals_path: str | Path, autonomy_path: str | Path) -> None:
        self._approvals: dict[str, Any] = (
            yaml.safe_load(Path(approvals_path).read_text(encoding="utf-8")) or {}
        )
        self._autonomy: dict[str, Any] = (
            yaml.safe_load(Path(autonomy_path).read_text(encoding="utf-8")) or {}
        )

    def check(
        self,
        operation: str,
        environment: str,
        resource: str | None = None,
        operation_class: str = "read",
    ) -> PolicyResult:
        required_level = self._autonomy.get("operation_class_required_level", {}).get(
            operation_class, "L1"
        )
        max_level = self._autonomy.get("environment_max_autonomy", {}).get(environment, "L1")
        allowed = _LEVEL_ORDER.index(required_level) <= _LEVEL_ORDER.index(max_level)

        requires_approval = bool(self._approvals.get("default_requires_approval", False))
        reason = "No matching approval rule; default policy applied."
        for rule in self._approvals.get("rules", []):
            if _rule_matches(rule, operation, environment, operation_class):
                requires_approval = bool(rule.get("requires_approval", True))
                reason = rule.get("reason", f"Matched rule {rule.get('id', '?')}")
                break

        if environment == "PROD" and operation_class in self._autonomy.get(
            "always_gate_in_prod", []
        ):
            requires_approval = True
            reason = f"{operation_class} operations in PROD always require approval (ADR-005)."

        return PolicyResult(
            allowed=allowed,
            requires_approval=requires_approval,
            autonomy_level_required=required_level,
            autonomy_level_max=max_level,
            reason=reason,
        )


def _rule_matches(
    rule: dict[str, Any], operation: str, environment: str, operation_class: str
) -> bool:
    match = rule.get("match", {})
    if "environment" in match and match["environment"] != environment:
        return False
    if "operation" in match:
        ops = match["operation"]
        ops = ops if isinstance(ops, list) else [ops]
        if operation not in ops:
            return False
    if "operation_class" in match and match["operation_class"] != operation_class:
        return False
    return True
