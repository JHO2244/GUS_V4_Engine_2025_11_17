"""
GUS v4.0 — L8 Execution Layer
Execution Record Models v0.1

Goal:
- Deterministic execution outputs (no side effects).
- Minimal structures to support the L8-2 Authorization Gate tests.

Notes:
- timestamp_utc is deterministic by default (fixed epoch string).
- execution_hash is derived deterministically from decision_hash + status + action.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Literal


Status = Literal["SUCCESS", "FAILURE", "BLOCKED"]


@dataclass(frozen=True)
class ExecutionRequest:
    decision_id: str
    verdict: str
    authorized_action: str
    parameters: Mapping[str, Any]
    decision_hash: str


@dataclass(frozen=True)
class ExecutionResult:
    status: Status
    timestamp_utc: str
    execution_hash: str
    note: str = ""


@dataclass(frozen=True)
class ExecutionRecord:
    execution_id: str
    decision_hash: str
    result: ExecutionResult
    audit_trace: Mapping[str, Any]

