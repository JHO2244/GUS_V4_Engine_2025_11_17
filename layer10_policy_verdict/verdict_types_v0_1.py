# layer10_policy_verdict/verdict_types_v0_1.py
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class VerdictCode(str, Enum):
    """
    Stable verdict codes for Policy Verdict Engine v0.1

    Semantics:
      - ALLOW: policy allows the action
      - DENY: policy blocks the action (hard stop)
      - WARN: allowed, but with policy risk/concern
      - ABSTAIN: policy engine cannot decide (insufficient info / rule gap)
    """
    ALLOW = "ALLOW"
    DENY = "DENY"
    WARN = "WARN"
    ABSTAIN = "ABSTAIN"


class Severity(str, Enum):
    """
    Severity is independent of VerdictCode.
    Example: WARN may be LOW/MED/HIGH; DENY is typically HIGH/CRITICAL.
    """
    LOW = "LOW"
    MED = "MED"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass(frozen=True, slots=True)
class RuleHit:
    """
    Evidence of which rule(s) fired.
    Keep fields stable + JSON-safe.
    """
    rule_id: str
    rule_version: str
    outcome: VerdictCode
    severity: Severity
    reason: str
    tags: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "rule_version": self.rule_version,
            "outcome": self.outcome.value,
            "severity": self.severity.value,
            "reason": self.reason,
            "tags": list(self.tags),
        }


@dataclass(frozen=True, slots=True)
class PolicyVerdict:
    """
    Canonical verdict object. Deterministic by construction:
      - rule_hits stored as an ordered tuple
      - tags stored as an ordered tuple
    """
    code: VerdictCode
    severity: Severity
    summary: str

    # Optional structured detail
    reason_codes: Tuple[str, ...] = ()
    rule_hits: Tuple[RuleHit, ...] = ()
    tags: Tuple[str, ...] = ()

    # Optional metadata (MUST remain JSON-serializable)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        # deterministic output ordering (python preserves insertion order)
        return {
            "code": self.code.value,
            "severity": self.severity.value,
            "summary": self.summary,
            "reason_codes": list(self.reason_codes),
            "rule_hits": [rh.to_dict() for rh in self.rule_hits],
            "tags": list(self.tags),
            "metadata": dict(self.metadata),
        }


def combine_verdicts(verdicts: List[PolicyVerdict]) -> PolicyVerdict:
    """
    Deterministic fold:
      - DENY overrides everything
      - WARN overrides ALLOW
      - ABSTAIN only if no DENY/WARN/ALLOW exists, or if all are ABSTAIN

    Severity fold:
      CRITICAL > HIGH > MED > LOW

    Rule hits + tags are concatenated in input order.
    """
    if not verdicts:
        return PolicyVerdict(
            code=VerdictCode.ABSTAIN,
            severity=Severity.MED,
            summary="No verdicts provided (ABSTAIN).",
        )

    rank = {
        VerdictCode.DENY: 4,
        VerdictCode.WARN: 3,
        VerdictCode.ALLOW: 2,
        VerdictCode.ABSTAIN: 1,
    }
    sev_rank = {
        Severity.CRITICAL: 4,
        Severity.HIGH: 3,
        Severity.MED: 2,
        Severity.LOW: 1,
    }

    # pick highest verdict rank
    best = max(verdicts, key=lambda v: (rank[v.code], sev_rank[v.severity]))

    # fold severity to max
    max_sev = max(verdicts, key=lambda v: sev_rank[v.severity]).severity

    # deterministic concatenation
    all_reason_codes: List[str] = []
    all_hits: List[RuleHit] = []
    all_tags: List[str] = []
    merged_meta: Dict[str, Any] = {}

    for v in verdicts:
        all_reason_codes.extend(list(v.reason_codes))
        all_hits.extend(list(v.rule_hits))
        all_tags.extend(list(v.tags))
        # deterministic merge: later keys overwrite earlier keys (stable + explicit)
        for k, val in v.metadata.items():
            merged_meta[k] = val

    # normalize tuples; do NOT sort (sorting can hide causality/order)
    return PolicyVerdict(
        code=best.code,
        severity=max_sev,
        summary=best.summary,
        reason_codes=tuple(all_reason_codes),
        rule_hits=tuple(all_hits),
        tags=tuple(all_tags),
        metadata=merged_meta,
    )
