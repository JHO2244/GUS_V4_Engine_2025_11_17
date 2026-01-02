"""
GUS v4.0 — L8 Execution Layer
Execution Runtime v0.1 (L8-2 Authorization Gate)

Purpose:
- Execute ONLY what L7 explicitly authorizes.
- Enforce deterministic allow-list via action_registry_v0_1.py
- No side effects (NOOP only in v0.1)
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping, Callable

from layer8_execution.action_registry_v0_1 import is_action_allowed
from layer8_execution.execution_record_v0_1 import (
    ExecutionRequest,
    ExecutionResult,
    ExecutionRecord,
)


_FIXED_TIMESTAMP_UTC = "1970-01-01T00:00:00Z"


def _stable_json(data: Mapping[str, Any]) -> str:
    """Deterministic JSON encoding for hashing."""
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _hash_str(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


class ExecutionRuntimeV0_1:
    """
    Deterministic execution runtime.
    - Accepts a decision dict from L7 (treated as read-only).
    - Applies Authorization Gate rules.
    """

    def __init__(self, clock_utc: Callable[[], str] | None = None) -> None:
        # clock_utc is injected for future flexibility; default remains deterministic.
        self._clock_utc = clock_utc or (lambda: _FIXED_TIMESTAMP_UTC)

    @staticmethod
    def _require_fields(decision: Mapping[str, Any]) -> None:
        required = ["decision_id", "verdict", "authorized_action", "parameters", "decision_hash"]
        missing = [k for k in required if k not in decision]
        if missing:
            raise ValueError(f"Missing required decision fields: {missing}")

        if not isinstance(decision["parameters"], dict):
            raise ValueError("Field 'parameters' must be a dict.")

        for k in ["decision_id", "verdict", "authorized_action", "decision_hash"]:
            if not isinstance(decision[k], str) or not decision[k].strip():
                raise ValueError(f"Field '{k}' must be a non-empty string.")

    def execute(self, decision: Mapping[str, Any]) -> ExecutionResult:
        """
        Execute an authorized action deterministically.
        Returns ExecutionResult only (record enforcement comes in L8-3).
        """
        self._require_fields(decision)

        req = ExecutionRequest(
            decision_id=decision["decision_id"],
            verdict=decision["verdict"],
            authorized_action=decision["authorized_action"],
            parameters=decision["parameters"],
            decision_hash=decision["decision_hash"],
        )

        # Gate 1: verdict must be ALLOW
        if req.verdict != "ALLOW":
            return self._blocked(req, note="Verdict not ALLOW")

        # Gate 2: action must be allow-listed
        if not is_action_allowed(req.authorized_action):
            return self._blocked(req, note="Action not in registry")

        # v0.1: NOOP only, no side effects
        if req.authorized_action != "NOOP":
            return self._blocked(req, note="Only NOOP permitted in v0.1")

        # Deterministic SUCCESS for NOOP
        ts = self._clock_utc()
        execution_hash = _hash_str(_stable_json({
            "decision_hash": req.decision_hash,
            "status": "SUCCESS",
            "action": req.authorized_action,
            "timestamp_utc": ts,
        }))
        return ExecutionResult(status="SUCCESS", timestamp_utc=ts, execution_hash=execution_hash, note="NOOP executed")

    def _blocked(self, req: ExecutionRequest, note: str) -> ExecutionResult:
        ts = self._clock_utc()
        execution_hash = _hash_str(_stable_json({
            "decision_hash": req.decision_hash,
            "status": "BLOCKED",
            "action": req.authorized_action,
            "timestamp_utc": ts,
            "note": note,
        }))
        return ExecutionResult(status="BLOCKED", timestamp_utc=ts, execution_hash=execution_hash, note=note)

    def execute_with_record(self, decision: Mapping[str, Any]) -> ExecutionRecord:
        """
        Convenience: returns a minimal ExecutionRecord.
        (Full record enforcement + audit trace hardening is L8-3.)
        """
        result = self.execute(decision)
        execution_id = _hash_str(_stable_json({
            "decision_id": decision.get("decision_id", ""),
            "execution_hash": result.execution_hash,
        }))
        audit_trace = {
            "gate_version": "0.1",
            "decision_id": decision.get("decision_id", ""),
            "decision_hash": decision.get("decision_hash", ""),
            "authorized_action": decision.get("authorized_action", ""),
            "verdict": decision.get("verdict", ""),
            "status": result.status,
            "note": result.note,
        }
        return ExecutionRecord(
            execution_id=execution_id,
            decision_hash=decision.get("decision_hash", ""),
            result=result,
            audit_trace=audit_trace,
        )

