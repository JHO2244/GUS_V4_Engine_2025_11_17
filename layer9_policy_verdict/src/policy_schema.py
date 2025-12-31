from __future__ import annotations
from typing import Any, Dict, List, Tuple

class PolicySchemaError(ValueError):
    pass

def validate_policy_v1(policy: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Minimal validator (stdlib only).
    Contract:
    - policy_id: non-empty str
    - thresholds: dict with allow/warn in [0,10]
    - allow >= warn (recommended invariant)
    - base_score if present in [0,10]
    Returns (ok, errors)
    """
    errors: List[str] = []

    pid = policy.get("policy_id")
    if not isinstance(pid, str) or not pid.strip():
        errors.append("policy_id must be a non-empty string.")

    th = policy.get("thresholds")
    if not isinstance(th, dict):
        errors.append("thresholds must be an object/dict.")
    else:
        allow = th.get("allow")
        warn = th.get("warn")
        if not (isinstance(allow, int | float) and 0.0 <= float(allow) <= 10.0):
            errors.append("thresholds.allow must be a number in [0,10].")
        if not (isinstance(warn, int | float) and 0.0 <= float(warn) <= 10.0):
            errors.append("thresholds.warn must be a number in [0,10].")
        if not errors:
            if float(allow) < float(warn):
                errors.append("thresholds.allow must be >= thresholds.warn.")

    if "base_score" in policy:
        bs = policy.get("base_score")
        if not (isinstance(bs, int | float) and 0.0 <= float(bs) <= 10.0):
            errors.append("base_score must be a number in [0,10].")

    return (len(errors) == 0), errors

def require_policy_v1(policy: Dict[str, Any]) -> None:
    ok, errors = validate_policy_v1(policy)
    if not ok:
        raise PolicySchemaError("; ".join(errors))
