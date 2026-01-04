from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

from layer7_output_contract.output_envelope_v0_1 import OutputEnvelopeV0_1


@dataclass(frozen=True)
class ContractViolation:
    field: str
    message: str


class OutputContractV0_1:
    """
    A7 Output Contract v0.1
    Enforces minimum structure + sanity bounds.
    """

    SCHEMA = "A7.output_envelope.v0.1"
    REQUIRED_BREAKDOWN_KEYS = ("TD", "SC", "AP", "RL")

    @classmethod
    def validate(cls, env: OutputEnvelopeV0_1) -> Tuple[bool, List[ContractViolation]]:
        violations: List[ContractViolation] = []

        if env.schema_version != cls.SCHEMA:
            violations.append(ContractViolation("schema_version", f"Expected '{cls.SCHEMA}'"))

        if not env.timestamp_utc.endswith("Z"):
            violations.append(ContractViolation("timestamp_utc", "Must be ISO8601 UTC ending with 'Z'"))

        if not env.producer:
            violations.append(ContractViolation("producer", "Must be non-empty"))

        if not env.run_id:
            violations.append(ContractViolation("run_id", "Must be non-empty"))

        if not env.input_seal_ref:
            violations.append(ContractViolation("input_seal_ref", "Must be non-empty"))

        if not env.decision_ref:
            violations.append(ContractViolation("decision_ref", "Must be non-empty"))

        # policy verdict reference must be present (fail-closed)
        pv_ref = getattr(env, 'policy_verdict_ref', None)
        if not isinstance(pv_ref, str) or not pv_ref.strip():
            violations.append(ContractViolation('policy_verdict_ref', 'Must be non-empty'))

        if not (0.0 <= float(env.score_total) <= 10.0):
            violations.append(ContractViolation("score_total", "Must be within [0.0, 10.0]"))

        # breakdown must have required keys and values within [0,10]
        for k in cls.REQUIRED_BREAKDOWN_KEYS:
            if k not in env.score_breakdown:
                violations.append(ContractViolation("score_breakdown", f"Missing key '{k}'"))

        for k, v in env.score_breakdown.items():
            try:
                fv = float(v)
            except Exception:
                violations.append(ContractViolation("score_breakdown", f"Non-numeric value for '{k}'"))
                continue
            if not (0.0 <= fv <= 10.0):
                violations.append(ContractViolation("score_breakdown", f"'{k}' out of [0.0,10.0]"))

        # integrity must verify
        if not env.verify_integrity():
            violations.append(ContractViolation("integrity", "Integrity hash missing or invalid"))

        return (len(violations) == 0), violations
