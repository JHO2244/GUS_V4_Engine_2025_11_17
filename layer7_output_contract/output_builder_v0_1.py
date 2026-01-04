from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List, Optional

from layer7_output_contract.output_contract_v0_1 import OutputContractV0_1
from layer7_output_contract.output_envelope_v0_1 import OutputEnvelopeV0_1, Verdict


def utc_now_iso_z() -> str:
    # ISO8601 UTC with trailing Z, no micros (stable formatting).
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def build_output_envelope_v0_1(
    *,
    producer: str,
    run_id: str,
    input_seal_ref: str,
    decision_ref: str,
    policy_verdict_ref: str,
    score_total: float,
    score_breakdown: Dict[str, float],
    verdict: Verdict,
    artifacts: Optional[List[str]] = None,
    explainability_trace_ref: Optional[str] = None,
    timestamp_utc: Optional[str] = None,
    signature_policy: str = "seal-only",
) -> OutputEnvelopeV0_1:
    """
    Fail-closed builder:
    - constructs envelope
    - computes integrity
    - validates OutputContractV0_1
    """
    env = OutputEnvelopeV0_1(
        schema_version=OutputContractV0_1.SCHEMA,
        timestamp_utc=timestamp_utc or utc_now_iso_z(),
        producer=producer,
        run_id=run_id,
        input_seal_ref=input_seal_ref,
        decision_ref=decision_ref,
        policy_verdict_ref=policy_verdict_ref,
        score_total=float(score_total),
        score_breakdown=dict(score_breakdown),
        verdict=verdict,
        artifacts=list(artifacts or []),
        explainability_trace_ref=explainability_trace_ref,
        signature_policy=signature_policy,
        integrity="",
    ).with_integrity()

    ok, violations = OutputContractV0_1.validate(env)
    if not ok:
        details = "; ".join([f"{v.field}:{v.message}" for v in violations])
        raise ValueError(f"Output envelope contract failed: {details}")

    return env
