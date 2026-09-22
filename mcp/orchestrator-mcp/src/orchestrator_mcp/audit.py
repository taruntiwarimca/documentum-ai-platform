"""Deprecated: AuditLog now lives in the shared agent_common package so
every agent (not just orchestrator-mcp) uses the same implementation. This
re-export exists only for backward compatibility with any code still
importing from here.
"""
from __future__ import annotations

from agent_common.audit import AuditLog

__all__ = ["AuditLog"]
