from __future__ import annotations
import hashlib
import json
from typing import Any, Dict, List, Optional

from .verdict_types import PolicyVerdict, VerdictLevel

def _stable_hash(obj: Dict[str, Any]) -> str:
    blob = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()

def evaluate_policy(
    *,
    action: Dict[str, Any],
    context: Dict[str, Any],
    policy: Dict[str, Any],
    epoch_ref: str,
    chain_head: str,
) -> PolicyVerdict:
    """
    TEST-BACKED CONTRACT (do not change without updating tests):
    - Deterministic: same inputs => same verdict + object_hash
    - score in [0.0, 10.0]
    - level derived from score thresholds in policy["thresholds"] with defaults:
        allow >= 9.7
        warn  >= 8.5
        else block
    - reasons non-empty
    - object_hash hashes (action, context, policy, epoch_ref, chain_head, derived fields except object_hash)
    """
    thresholds = policy.get("thresholds", {})
    t_allow = float(thresholds.get("allow", 9.7))
    t_warn = float(thresholds.get("warn", 8.5))

    # Placeholder scoring logic (will be upgraded after tests are green)
    base_score = float(policy.get("base_score", 9.7))
    score = max(0.0, min(10.0, base_score))

    if score >= t_allow:
        level = VerdictLevel.ALLOW
        reasons = ["Policy thresholds satisfied (ALLOW)."]
    elif score >= t_warn:
        level = VerdictLevel.WARN
        reasons = ["Policy thresholds satisfied (WARN)."]
    else:
        level = VerdictLevel.BLOCK
        reasons = ["Policy thresholds failed (BLOCK)."]

    evidence: Dict[str, Any] = {
        "thresholds": {"allow": t_allow, "warn": t_warn},
        "base_score": base_score,
    }

    object_core = {
        "level": level.value,
        "score": score,
        "reasons": reasons,
        "evidence": evidence,
        "policy_id": str(policy.get("policy_id", "POLICY_UNSET")),
        "epoch_ref": epoch_ref,
        "chain_head": chain_head,
        "action": action,
        "context": context,
        "policy": policy,
    }
    object_hash = _stable_hash(object_core)

    return PolicyVerdict(
        level=level,
        score=score,
        reasons=reasons,
        evidence=evidence,
        policy_id=object_core["policy_id"],
        epoch_ref=epoch_ref,
        chain_head=chain_head,
        object_hash=object_hash,
    )
