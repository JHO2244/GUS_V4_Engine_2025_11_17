"""
GUS v4.0 — L8 Execution Layer
Execution Record Models v0.1

L8-3 Upgrade:
- ExecutionRecord MUST include record_hash.
- record_hash is deterministic and covers:
  execution_id, decision_hash, result fields, audit_trace.

L8-4 Upgrade:
- ExecutionRecord MUST include side_effect_events (declared IO only).
- record_hash MUST cover side_effect_events.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Literal, Tuple


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
    side_effect_events: Tuple[Mapping[str, Any], ...]
    record_hash: str
