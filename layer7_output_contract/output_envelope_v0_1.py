from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional
import hashlib
import json


Verdict = Literal["PASS", "FAIL", "WARN"]


def _canonical_json_bytes(payload: Dict[str, Any]) -> bytes:
    """
    Canonical JSON serialization (stable for hashing):
    - sort keys
    - UTF-8
    - no whitespace
    """
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def canonical_sha256(payload: Dict[str, Any]) -> str:
    return hashlib.sha256(_canonical_json_bytes(payload)).hexdigest()


@dataclass(frozen=True)
class OutputEnvelopeV0_1:
    """
    A7 Output Envelope v0.1
    Minimal, deterministic wrapper for any GUS "output".
    """
    schema_version: str
    timestamp_utc: str
    producer: str
    run_id: str

    input_seal_ref: str
    decision_ref: str

    # P3.1: wire policy verdict reference (string ref, not full payload)
    policy_verdict_ref: Optional[str] = None

    score_total: float = 0.0
    score_breakdown: Dict[str, float] = field(default_factory=dict)

    verdict: Verdict = "PASS"

    artifacts: List[str] = field(default_factory=list)
    explainability_trace_ref: Optional[str] = None

    signature_policy: str = "seal-only"
    integrity: str = ""  # sha256 of canonical dict (computed)

    def to_dict(self, include_integrity: bool = True) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "schema_version": self.schema_version,
            "timestamp_utc": self.timestamp_utc,
            "producer": self.producer,
            "run_id": self.run_id,
            "input_seal_ref": self.input_seal_ref,
            "decision_ref": self.decision_ref,
            "policy_verdict_ref": self.policy_verdict_ref,
            "score_total": self.score_total,
            "score_breakdown": dict(self.score_breakdown),
            "verdict": self.verdict,
            "artifacts": list(self.artifacts),
            "explainability_trace_ref": self.explainability_trace_ref,
            "signature_policy": self.signature_policy,
        }
        if include_integrity:
            d["integrity"] = self.integrity
        return d

    def compute_integrity(self) -> str:
        """
        Compute integrity hash over the envelope content excluding 'integrity' itself.
        """
        base = self.to_dict(include_integrity=False)
        return canonical_sha256(base)

    def with_integrity(self) -> "OutputEnvelopeV0_1":
        """
        Return a new instance with integrity computed.
        """
        return OutputEnvelopeV0_1(
            schema_version=self.schema_version,
            timestamp_utc=self.timestamp_utc,
            producer=self.producer,
            run_id=self.run_id,
            input_seal_ref=self.input_seal_ref,
            decision_ref=self.decision_ref,
            policy_verdict_ref=self.policy_verdict_ref,
            score_total=self.score_total,
            score_breakdown=dict(self.score_breakdown),
            verdict=self.verdict,
            artifacts=list(self.artifacts),
            explainability_trace_ref=self.explainability_trace_ref,
            signature_policy=self.signature_policy,
            integrity=self.compute_integrity(),
        )

    def verify_integrity(self) -> bool:
        if not self.integrity:
            return False
        return self.integrity == self.compute_integrity()
