# layer10_policy_verdict/policy_verdict_engine_v0_1.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence, Tuple

from layer10_policy_verdict.policy_rules_v0_1 import PolicyRule, RuleContext, default_rules_v0_1
from layer10_policy_verdict.verdict_types_v0_1 import PolicyVerdict, Severity, VerdictCode, combine_verdicts


@dataclass(frozen=True, slots=True)
class PolicyVerdictEngine:
    """
    Deterministic policy engine v0.1:
      - evaluates rules in declared order
      - collects applicable (non-None) verdicts
      - combines verdicts deterministically
    """
    rules: Tuple[PolicyRule, ...] = default_rules_v0_1()

    def evaluate(self, ctx: RuleContext) -> PolicyVerdict:
        verdicts = []
        for r in self.rules:
            v = r.evaluate(ctx)
            if v is not None:
                verdicts.append(v)

        if not verdicts:
            # If no rule applies, we allow but warn lightly:
            # v0.1 posture: "not prohibited" ≠ "perfectly safe"
            return PolicyVerdict(
                code=VerdictCode.ALLOW,
                severity=Severity.LOW,
                summary="No applicable policy rules; default ALLOW.",
                reason_codes=("DEFAULT_ALLOW",),
                rule_hits=(),
                tags=("policy", "default"),
                metadata={},
            )

        return combine_verdicts(verdicts)

