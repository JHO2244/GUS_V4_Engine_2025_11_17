# layer10_policy_verdict/policy_rules_v0_1.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Mapping, Optional, Protocol, Sequence, Tuple

from layer10_policy_verdict.verdict_types_v0_1 import (
    PolicyVerdict,
    RuleHit,
    Severity,
    VerdictCode,
)


@dataclass(frozen=True, slots=True)
class RuleContext:
    """
    Minimal context object. Keep it boring + stable + JSON-safe.

    action_id: deterministic string describing what is being attempted
    actor_id: deterministic string describing who/what is attempting
    inputs:   JSON-safe dictionary payload (already canonicalized upstream)
    """
    action_id: str
    actor_id: str
    inputs: Mapping[str, Any]


class PolicyRule(Protocol):
    """
    A PolicyRule is a small deterministic evaluator.
    It may return None if the rule does not apply.
    """
    rule_id: str
    rule_version: str

    def evaluate(self, ctx: RuleContext) -> Optional[PolicyVerdict]: ...


@dataclass(frozen=True, slots=True)
class BaseRule:
    rule_id: str
    rule_version: str = "0.1"


def _hit(
    *,
    rule_id: str,
    rule_version: str,
    outcome: VerdictCode,
    severity: Severity,
    reason: str,
    tags: Tuple[str, ...] = (),
) -> RuleHit:
    return RuleHit(
        rule_id=rule_id,
        rule_version=rule_version,
        outcome=outcome,
        severity=severity,
        reason=reason,
        tags=tags,
    )


def _verdict(
    *,
    code: VerdictCode,
    severity: Severity,
    summary: str,
    rule_hit: RuleHit,
    reason_codes: Tuple[str, ...] = (),
    tags: Tuple[str, ...] = (),
    metadata: Optional[Dict[str, Any]] = None,
) -> PolicyVerdict:
    return PolicyVerdict(
        code=code,
        severity=severity,
        summary=summary,
        reason_codes=reason_codes,
        rule_hits=(rule_hit,),
        tags=tags,
        metadata=metadata or {},
    )


@dataclass(frozen=True, slots=True)
class RuleDenyExplicitFlag(BaseRule):
    """
    If inputs contains deny=True then DENY.
    This is a deterministic, test-only baseline rule.
    """
    rule_id: str = "PV-RULE-DENY-EXPLICIT"

    def evaluate(self, ctx: RuleContext) -> Optional[PolicyVerdict]:
        deny_flag = bool(ctx.inputs.get("deny", False))
        if not deny_flag:
            return None

        rh = _hit(
            rule_id=self.rule_id,
            rule_version=self.rule_version,
            outcome=VerdictCode.DENY,
            severity=Severity.HIGH,
            reason="Explicit deny flag present in inputs.",
            tags=("explicit",),
        )
        return _verdict(
            code=VerdictCode.DENY,
            severity=Severity.HIGH,
            summary="Denied by explicit input flag.",
            rule_hit=rh,
            reason_codes=("DENY_EXPLICIT",),
            tags=("policy",),
            metadata={"deny_flag": True},
        )


@dataclass(frozen=True, slots=True)
class RuleWarnMissingRequiredKeys(BaseRule):
    """
    If any required key is missing from inputs, emit WARN (not DENY).
    This keeps policy conservative but non-blocking at v0.1.
    """
    rule_id: str = "PV-RULE-WARN-MISSING-KEYS"
    required_keys: Tuple[str, ...] = ("action", "target")

    def evaluate(self, ctx: RuleContext) -> Optional[PolicyVerdict]:
        missing = tuple(k for k in self.required_keys if k not in ctx.inputs)
        if not missing:
            return None

        rh = _hit(
            rule_id=self.rule_id,
            rule_version=self.rule_version,
            outcome=VerdictCode.WARN,
            severity=Severity.MED,
            reason=f"Missing required keys: {', '.join(missing)}",
            tags=("schema",),
        )
        return _verdict(
            code=VerdictCode.WARN,
            severity=Severity.MED,
            summary="Inputs missing required keys.",
            rule_hit=rh,
            reason_codes=("MISSING_KEYS",),
            tags=("policy", "input"),
            metadata={"missing_keys": list(missing)},
        )


@dataclass(frozen=True, slots=True)
class RuleAbstainOnEmptyInputs(BaseRule):
    """
    If inputs is empty, ABSTAIN (no basis to decide).
    """
    rule_id: str = "PV-RULE-ABSTAIN-EMPTY"

    def evaluate(self, ctx: RuleContext) -> Optional[PolicyVerdict]:
        if ctx.inputs:
            return None

        rh = _hit(
            rule_id=self.rule_id,
            rule_version=self.rule_version,
            outcome=VerdictCode.ABSTAIN,
            severity=Severity.MED,
            reason="Empty inputs; cannot evaluate policy.",
            tags=("empty",),
        )
        return _verdict(
            code=VerdictCode.ABSTAIN,
            severity=Severity.MED,
            summary="Abstained due to empty inputs.",
            rule_hit=rh,
            reason_codes=("EMPTY_INPUTS",),
            tags=("policy",),
            metadata={"empty": True},
        )


def default_rules_v0_1() -> Tuple[PolicyRule, ...]:
    """
    Deterministic default rules for v0.1.
    Order matters: we keep it explicit and testable.
    """
    return (
        RuleAbstainOnEmptyInputs(),
        RuleWarnMissingRequiredKeys(),
        RuleDenyExplicitFlag(),
    )
