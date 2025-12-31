from __future__ import annotations

from typing import Any, Dict

from layer9_policy_verdict.src.policy_engine import evaluate_policy
from layer9_policy_verdict.src.policy_loader import load_policy
from layer9_policy_verdict.src.verdict_ledger_bridge import append_verdict_to_ledger
from layer9_policy_verdict.src.verdict_types import PolicyVerdict


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

    verdict: PolicyVerdict = evaluate_policy(
        action=action,
        context=context,
        policy=policy,
        epoch_ref=epoch_ref,
        chain_head=chain_head,
    )

    ledger_result = append_verdict_to_ledger(verdict)

    return {
        "ok": True,
        "level": verdict.level.value,
        "score": verdict.score,
        "verdict": verdict,
        "ledger_hash": ledger_result["hash"],
    }
