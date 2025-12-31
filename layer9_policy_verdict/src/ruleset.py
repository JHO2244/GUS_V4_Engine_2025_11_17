from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple


@dataclass(frozen=True)
class RuleResult:
    rule_id: str
    delta: float
    reason: str


def _clamp_score(x: float) -> float:
    return 0.0 if x < 0.0 else 10.0 if x > 10.0 else float(x)


def apply_ruleset_v1(*, action: Dict[str, Any], context: Dict[str, Any]) -> List[RuleResult]:
    """
    Deterministic, stdlib-only ruleset.
    Rules are intentionally simple v1 scaffolds (expand later).
    """
    out: List[RuleResult] = []

    # R1: If context says checks are green, small boost.
    if str(context.get("checks", "")).lower() in {"green", "pass", "passed"}:
        out.append(RuleResult("R1_CHECKS_GREEN", +0.2, "CI checks green."))

    # R2: If action targets main, require extra discipline (slight penalty unless explicitly merge_pr).
    if str(action.get("target", "")).lower() == "main" and str(action.get("type", "")).lower() != "merge_pr":
        out.append(RuleResult("R2_MAIN_TARGET_GUARD", -0.3, "Target is main; non-PR action is risky."))

    # R3: If actor present, small neutral confirmation (no delta) – keeps audit trail.
    if "actor" in context:
        out.append(RuleResult("R3_ACTOR_PRESENT", 0.0, "Actor present in context."))

    return out


def score_from_policy_and_rules(
    *,
    base_score: float,
    rules: List[RuleResult],
) -> Tuple[float, List[str]]:
    score = float(base_score)
    reasons: List[str] = ["Base score applied."]

    for r in rules:
        score += float(r.delta)
        reasons.append(f"{r.rule_id}: {r.reason} ({r.delta:+.1f})")

    score = _clamp_score(score)
    return score, reasons
