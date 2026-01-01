from __future__ import annotations
from gus_purpose_charter_gate import require_charter_v4

from typing import Any, Dict

from layer9_policy_verdict.src.policy_engine import evaluate_policy
from layer9_policy_verdict.src.policy_loader import load_policy
from layer9_policy_verdict.src.verdict_ledger_bridge import append_verdict_to_ledger
from layer9_policy_verdict.src.verdict_types import PolicyVerdict

def _verdict_to_jsonable(v: PolicyVerdict) -> Dict[str, Any]:
    to_dict = getattr(v, "to_dict", None)
    if callable(to_dict):
        out = to_dict()
        if isinstance(out, dict):
            return out

    return {
        "level": v.level.value,
        "score": v.score,
        "reasons": list(v.reasons),
        "evidence": dict(v.evidence),
        "policy_id": v.policy_id,
        "epoch_ref": v.epoch_ref,
        "chain_head": v.chain_head,
        "object_hash": v.object_hash,
    }

def govern_action(
    *,
    action: Dict[str, Any],
    context: Dict[str, Any],
    policy_filename: str,
    epoch_ref: str,
    chain_head: str

) -> Dict[str, Any]:
    """
    Stable governance entrypoint (v1).
    Pipeline:
    1) Load + validate policy
    2) Evaluate to PolicyVerdict
    3) Append verdict into L8 audit ledger (mandatory)
    4) Return compact response
    """
    policy = load_policy(policy_filename)
    require_charter_v4()  # fail-closed if charter missing/invalid

    verdict: PolicyVerdict = evaluate_policy(
        action=action,
        context=context,
        policy=policy,
        epoch_ref=epoch_ref,
        chain_head=chain_head,
    )

    ledger_result = append_verdict_to_ledger(verdict)

    ok = bool(ledger_result.get("ok", True))
    ledger_hash = ledger_result.get("hash")

    if (not ok) or (not ledger_hash):
        err = ledger_result.get("error") or "Ledger append failed (missing hash)"
        raise RuntimeError(err)

    return {
        "ok": True,
        "level": verdict.level.value,
        "score": verdict.score,
        "policy_id": verdict.policy_id,
        "object_hash": verdict.object_hash,
        "verdict": _verdict_to_jsonable(verdict),
        "ledger_hash": ledger_hash,
    }


