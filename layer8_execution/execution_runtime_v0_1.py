"""
GUS v4.0 — L8 Execution Layer
Execution Runtime v0.1

L8-2:
- Authorization Gate enforced (ALLOW + registry allow-list + NOOP-only).

L8-3 Upgrade:
- execute() MUST return ExecutionRecord (never ExecutionResult).
- record_hash MUST be deterministic and cover:
  execution_id, decision_hash, result fields, audit_trace.

L8-4 Upgrade:
- Side effects MUST be declared IO only (SideEffectBus).
- ExecutionRecord MUST include side_effect_events.
- record_hash MUST cover side_effect_events.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Callable, Mapping, Tuple

from layer8_execution.action_registry_v0_1 import (
    get_declared_side_effect_channels,
    is_action_allowed,
)
from layer8_execution.execution_record_v0_1 import (
    ExecutionRecord,
    ExecutionRequest,
    ExecutionResult,
)
from layer8_execution.side_effects_v0_1 import SideEffectBus

from layer10_policy_verdict.policy_verdict_engine_v0_1 import PolicyVerdictEngine
from layer10_policy_verdict.policy_rules_v0_1 import RuleContext
from layer10_policy_verdict.verdict_types_v0_1 import VerdictCode


_FIXED_TIMESTAMP_UTC = "1970-01-01T00:00:00Z"


def _stable_json(data: Mapping[str, Any]) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _hash_str(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _events_to_wire(events: Tuple[Any, ...]) -> Tuple[Mapping[str, Any], ...]:
    out: list[Mapping[str, Any]] = []
    for ev in events:
        out.append(
            {
                "seq": int(getattr(ev, "seq")),
                "timestamp_utc": str(getattr(ev, "timestamp_utc")),
                "channel": str(getattr(ev, "channel")),
                "payload": dict(getattr(ev, "payload")),
                "action_id": str(getattr(ev, "action_id")),
                "run_id": str(getattr(ev, "run_id")),
            }
        )
    return tuple(out)


class ExecutionRuntimeV0_1:
    def __init__(self, clock_utc: Callable[[], str] | None = None) -> None:
        self._clock_utc = clock_utc or (lambda: _FIXED_TIMESTAMP_UTC)
        self._policy_engine = PolicyVerdictEngine()

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

    def _policy_preflight(self, *, action_id: str, actor_id: str, inputs: Mapping[str, Any]) -> Mapping[str, Any]:
        verdict = self._policy_engine.evaluate(
            RuleContext(action_id=action_id, actor_id=actor_id, inputs=inputs)
        )
        return verdict.to_dict()

    def execute(self, decision: Mapping[str, Any]) -> ExecutionRecord:
        """
        Execute an authorized action deterministically.
        Always returns ExecutionRecord (even when BLOCKED).
        """
        self._require_fields(decision)

        req = ExecutionRequest(
            decision_id=decision["decision_id"],
            verdict=decision["verdict"],
            authorized_action=decision["authorized_action"],
            parameters=decision["parameters"],
            decision_hash=decision["decision_hash"],
        )

        # Policy preflight: uses req fields (no undefined vars)
        actor_id = str(decision.get("actor_id", "UNKNOWN_ACTOR"))
        policy_verdict_wire = self._policy_preflight(
            action_id=req.authorized_action,
            actor_id=actor_id,
            inputs=req.parameters,
        )

        # Enforce policy DENY immediately (hard stop), but still return a record
        if policy_verdict_wire["code"] == VerdictCode.DENY.value:
            return self._record(
                req,
                status="BLOCKED",
                note=f"Execution denied by policy: {policy_verdict_wire.get('summary', '')}",
                side_effect_events=(),
                declared_channels=(),
                policy_verdict=policy_verdict_wire,
            )

        # Gate 1: verdict must be ALLOW
        if req.verdict != "ALLOW":
            return self._record(
                req,
                status="BLOCKED",
                note="Verdict not ALLOW",
                side_effect_events=(),
                declared_channels=(),
                policy_verdict=policy_verdict_wire,
            )

        # Gate 2: action must be allow-listed
        if not is_action_allowed(req.authorized_action):
            return self._record(
                req,
                status="BLOCKED",
                note="Action not in registry",
                side_effect_events=(),
                declared_channels=(),
                policy_verdict=policy_verdict_wire,
            )

        # v0.1: NOOP only
        if req.authorized_action != "NOOP":
            return self._record(
                req,
                status="BLOCKED",
                note="Only NOOP permitted in v0.1",
                side_effect_events=(),
                declared_channels=(),
                policy_verdict=policy_verdict_wire,
            )

        # L8-4/L8-6: declared channels enforced by registry+bus. Fail-closed on invalid registry metadata.
        run_id = _hash_str(_stable_json({"decision_id": req.decision_id, "decision_hash": req.decision_hash}))
        try:
            declared = get_declared_side_effect_channels(req.authorized_action)
            bus = SideEffectBus(
                declared_channels=declared,
                clock_utc=self._clock_utc,
                action_id=req.authorized_action,
                run_id=run_id,
            )
            side_effect_events = _events_to_wire(bus.snapshot())
        except ValueError:
            return self._record(
                req,
                status="BLOCKED",
                note="Registry metadata invalid",
                side_effect_events=(),
                declared_channels=(),
                policy_verdict=policy_verdict_wire,
            )

        return self._record(
            req,
            status="SUCCESS",
            note="NOOP executed",
            side_effect_events=side_effect_events,
            declared_channels=declared,
            policy_verdict=policy_verdict_wire,
        )

    def _record(
        self,
        req: ExecutionRequest,
        *,
        status: str,
        note: str,
        side_effect_events: Tuple[Mapping[str, Any], ...],
        declared_channels: Tuple[str, ...] = (),
        policy_verdict: Mapping[str, Any] | None = None,
    ) -> ExecutionRecord:
        ts = self._clock_utc()

        execution_hash = _hash_str(
            _stable_json(
                {
                    "decision_hash": req.decision_hash,
                    "status": status,
                    "action": req.authorized_action,
                    "timestamp_utc": ts,
                    "note": note,
                    "side_effect_events": side_effect_events,
                    "policy_verdict": policy_verdict or {},
                }
            )
        )

        result = ExecutionResult(
            status=status,  # type: ignore[arg-type]
            timestamp_utc=ts,
            execution_hash=execution_hash,
            note=note,
        )

        execution_id = _hash_str(_stable_json({"decision_id": req.decision_id, "execution_hash": execution_hash}))

        emitted_channels = tuple(
            sorted(
                {
                    ch
                    for ch in (
                        (ev.get("channel") if isinstance(ev, dict) else None) for ev in side_effect_events
                    )
                    if isinstance(ch, str) and ch.strip()
                }
            )
        )
        emitted_count = len(side_effect_events)

        audit_trace = {
            "gate_version": "0.1",
            "decision_id": req.decision_id,
            "decision_hash": req.decision_hash,
            "authorized_action": req.authorized_action,
            "verdict": req.verdict,
            "status": result.status,
            "note": result.note,
            "declared_channels": declared_channels,
            "emitted_channels": emitted_channels,
            "emitted_count": emitted_count,
            "side_effect_count": len(side_effect_events),
            "policy_verdict": policy_verdict or {},
        }

        record_hash = _hash_str(
            _stable_json(
                {
                    "execution_id": execution_id,
                    "decision_hash": req.decision_hash,
                    "result": {
                        "status": result.status,
                        "timestamp_utc": result.timestamp_utc,
                        "execution_hash": result.execution_hash,
                        "note": result.note,
                        "declared_channels": declared_channels,
                        "emitted_channels": emitted_channels,
                        "emitted_count": emitted_count,
                    },
                    "audit_trace": audit_trace,
                    "side_effect_events": side_effect_events,
                    "policy_verdict": policy_verdict or {},
                }
            )
        )

        # NOTE: ExecutionRecord must have policy_verdict: dict | None field.
        return ExecutionRecord(
            execution_id=execution_id,
            decision_hash=req.decision_hash,
            result=result,
            audit_trace=audit_trace,
            side_effect_events=side_effect_events,
            record_hash=record_hash,
            policy_verdict=dict(policy_verdict) if policy_verdict is not None else None,
        )

