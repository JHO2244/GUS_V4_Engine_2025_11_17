from __future__ import annotations
from layer9_policy_verdict.src.ruleset import apply_ruleset_v1, score_from_policy_and_rules

import hashlib
import json

from utils.canonical_json import canonical_json_bytes
from typing import Any, Dict, List, Optional

from .verdict_types import PolicyVerdict, VerdictLevel
from .policy_schema import require_policy_v1

def _stable_hash(obj: Dict[str, Any]) -> str:
    blob = canonical_json_bytes(obj)
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
    require_policy_v1(policy)

    thresholds = policy.get("thresholds", {})
    t_allow = float(thresholds.get("allow", 9.7))
    t_warn = float(thresholds.get("warn", 8.5))

    # Apply deterministic ruleset v1 and compute final score + reasons
    base_score = float(policy.get("base_score", 10.0))
    rules = apply_ruleset_v1(action=action, context=context)
    score, reasons = score_from_policy_and_rules(base_score=base_score, rules=rules)

    # Level decision by thresholds (use defaults-safe values)
    if score >= t_allow:
        level = VerdictLevel.ALLOW
    elif score >= t_warn:
        level = VerdictLevel.WARN
    else:
        level = VerdictLevel.BLOCK

    # Evidence is reserved for future expansion (keep deterministic)
    evidence: Dict[str, Any] = {}

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
