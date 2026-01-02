from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import json
import re

from utils.canonical_json import write_canonical_json_file

# Explicit writer only (never auto-write into repo)
DEFAULT_POLICY_PATH = Path("layer8_safety") / "anti_weaponization_policy_v0_1.json"
DEFAULT_EVAL_REPORT_PATH = Path("layer8_safety") / "anti_weaponization_eval_report_v0_1.json"


@dataclass(frozen=True)
class PolicyVerdict:
    """
    Deterministic verdict contract:
      - decision: "allow" | "review" | "deny"
      - allowed: bool (True only if decision == "allow")
      - reasons: stable-sorted list of human-readable reasons
      - matches: stable-sorted list of rule IDs
      - schema/version: fixed identifiers
    """
    decision: str
    allowed: bool
    reasons: Tuple[str, ...]
    matches: Tuple[str, ...]
    schema: str = "gus_v4_anti_weaponization_verdict"
    version: str = "0.1"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema": self.schema,
            "version": self.version,
            "decision": self.decision,
            "allowed": self.allowed,
            "reasons": list(self.reasons),
            "matches": list(self.matches),
            "notes": "Deterministic A5 anti-weaponization verdict (no timestamps, no entropy).",
        }


def _default_policy_dict() -> Dict[str, Any]:
    """
    Pure in-memory default policy. NO file I/O.
    Rules are conservative by design: deny direct weaponization instructions,
    and mark ambiguous high-risk content as review.
    """
    return {
        "schema": "gus_v4_anti_weaponization_policy",
        "version": "0.1",
        "description": "A5 strict anti-weaponization policy (deterministic).",
        "mode": "strict",
        "rules": [
            # DENY: explicit weapon-building or attack instructions (high-level patterns only)
            {
                "id": "DENY-WEAPON-INSTRUCTIONS",
                "decision": "deny",
                "reason": "Weaponization or attack-instruction intent detected.",
                "patterns": [
                    r"\bhow to (make|build)\b.*\b(weapon|bomb|explosive)\b",
                    r"\bmake\b.*\b(explosive|bomb)\b",
                    r"\bbuild\b.*\b(bomb|explosive|weapon)\b",
                    r"\bimprovised\b.*\b(explosive|device)\b",
                ],
            },
            # DENY: wrongdoing/hacking intent (broad, non-technical)
            {
                "id": "DENY-ILLEGAL-INTRUSION",
                "decision": "deny",
                "reason": "Illegal intrusion or malicious hacking intent detected.",
                "patterns": [
                    r"\bhow to\b.*\b(hack|break into|steal password)\b",
                    r"\b(phish|phishing)\b.*\b(template|script)\b",
                    r"\b(bypass|crack)\b.*\b(password|paywall|license)\b",
                ],
            },
            # REVIEW: ambiguous high-risk “help me hurt” phrasing without direct instructions
            {
                "id": "REVIEW-HARM-AMBIGUOUS",
                "decision": "review",
                "reason": "Potential harm intent detected; requires human judgment or safer reframing.",
                "patterns": [
                    r"\b(hurt|harm)\b.*\b(someone|people|them)\b",
                    r"\bmake\b.*\b(suffer)\b",
                ],
            },
        ],
        "invariants": {
            "no_entropy_fields": True,
            "no_timestamps": True,
            "canonical_json": True,
            "side_effect_free_default": True,
        },
    }


def read_policy(path: Optional[Path] = None) -> Dict[str, Any]:
    target = path or DEFAULT_POLICY_PATH
    if not target.exists():
        return {}
    with target.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_policy(policy: Dict[str, Any], path: Optional[Path] = None) -> Path:
    """
    Explicit writer only.
    """
    target = path or DEFAULT_POLICY_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    write_canonical_json_file(target, policy)
    return target


def load_policy(path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Side-effect free default:
    - If policy file missing: return in-memory default
    - Never writes automatically
    """
    raw = read_policy(path)
    if not raw:
        return _default_policy_dict()
    return raw


def _compile_rules(policy: Dict[str, Any]) -> List[Tuple[str, str, str, List[re.Pattern]]]:
    """
    Returns list of tuples:
      (rule_id, decision, reason, compiled_patterns)
    Deterministic compilation order: as listed in policy["rules"].
    """
    rules = policy.get("rules", []) or []
    compiled: List[Tuple[str, str, str, List[re.Pattern]]] = []
    for r in rules:
        rid = str(r.get("id", "")).strip()
        decision = str(r.get("decision", "")).strip()
        reason = str(r.get("reason", "")).strip()
        pats = r.get("patterns", []) or []
        cps = [re.compile(p, flags=re.IGNORECASE) for p in pats]
        compiled.append((rid, decision, reason, cps))
    return compiled


def evaluate_text(text: str, *, policy: Optional[Dict[str, Any]] = None) -> PolicyVerdict:
    """
    Deterministic evaluation:
    - Finds all rule hits
    - Escalation order: deny > review > allow
    - Stable outputs: sorted reasons/matches by rule id
    """
    p = policy or load_policy()
    compiled = _compile_rules(p)

    hits: List[Tuple[str, str, str]] = []  # (id, decision, reason)
    normalized = text or ""

    for rid, decision, reason, cps in compiled:
        for rx in cps:
            if rx.search(normalized):
                hits.append((rid, decision, reason))
                break  # one hit per rule is enough

    if not hits:
        return PolicyVerdict(
            decision="allow",
            allowed=True,
            reasons=tuple(),
            matches=tuple(),
        )

    # Deterministic: sort by rule id
    hits_sorted = sorted(hits, key=lambda x: x[0])

    # Escalation
    decisions = {d for _, d, _ in hits_sorted}
    if "deny" in decisions:
        final = "deny"
    elif "review" in decisions:
        final = "review"
    else:
        final = "allow"

    allowed = final == "allow"

    reasons = tuple([r for _, _, r in hits_sorted])
    matches = tuple([rid for rid, _, _ in hits_sorted])

    return PolicyVerdict(
        decision=final,
        allowed=allowed,
        reasons=reasons,
        matches=matches,
    )


def write_eval_report(verdict: PolicyVerdict, *, path: Optional[Path] = None) -> Path:
    """
    Explicit writer only (canonical JSON).
    """
    target = path or DEFAULT_EVAL_REPORT_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    write_canonical_json_file(target, verdict.to_dict())
    return target
