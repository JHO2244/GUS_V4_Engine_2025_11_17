from __future__ import annotations

"""
GUS v4 — Layer 3 Decision Engine (v0.1)

Goal:
- Provide a minimal, deterministic decision pipeline:
  context -> evaluate -> decide -> authorize -> result

Safety:
- This module does NOT execute actions.
- It only returns a decision result object.
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional

from utils import get_guardian_logger

from layer3_decision_engine.L3_context_evaluator_stub import evaluate_context
from layer3_decision_engine.L3_authorization_stub import authorize_decision
from layer3_decision_engine.L3_decision_matrix_stub import load_decision_engine_status

logger = get_guardian_logger("GUSv4.Layer3.Engine")


@dataclass(frozen=True)
class L3DecisionResult:
    ok: bool
    status: str  # approved | denied | aborted
    reason: str
    decision: Optional[Dict[str, Any]]


def _safe_get_str(d: Dict[str, Any], key: str, default: str = "") -> str:
    v = d.get(key, default)
    return str(v) if v is not None else default


def _safe_get_int(d: Dict[str, Any], key: str, default: int = 0) -> int:
    try:
        return int(d.get(key, default))
    except Exception:
        return default


def select_decision_minimal(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Minimal deterministic decision builder based on schema v0.1 fields.
    """
    requested_action = _safe_get_str(context, "requested_action", "noop")
    layer_origin = _safe_get_int(context, "layer_origin", 0)
    decision_id = _safe_get_str(context, "decision_id", "L3-UNSPECIFIED")

    decision = {
        "decision_id": decision_id,
        "requested_action": requested_action,
        "layer_origin": layer_origin,
        "status": "pending",
    }
    return decision


def run_decision(context: Dict[str, Any]) -> L3DecisionResult:
    """
    Run the minimal L3 pipeline.
    """
    # 0) Ensure schema is readable (this is our first integrity hook)
    status = load_decision_engine_status()
    if not status.schema_loaded:
        return L3DecisionResult(
            ok=False,
            status="aborted",
            reason="L3 schema not loaded",
            decision=None,
        )

    # 1) Context evaluation
    if not evaluate_context(context):
        return L3DecisionResult(
            ok=False,
            status="denied",
            reason="Context rejected",
            decision=None,
        )

    # 2) Build decision (minimal)
    decision = select_decision_minimal(context)

    # 3) Authorization
    if not authorize_decision(decision):
        decision["status"] = "denied"
        return L3DecisionResult(
            ok=False,
            status="denied",
            reason="Authorization denied",
            decision=decision,
        )

    decision["status"] = "approved"
    return L3DecisionResult(
        ok=True,
        status="approved",
        reason="Approved (v0.1 minimal)",
        decision=decision,
    )
