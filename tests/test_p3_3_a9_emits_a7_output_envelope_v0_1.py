from __future__ import annotations

import json
from pathlib import Path

from layer7_output_contract.output_contract_v0_1 import OutputContractV0_1
from layer7_output_contract.output_envelope_v0_1 import OutputEnvelopeV0_1
from layer9_final_guardian_audit.final_guardian_audit_v0_1 import write_a9_report_v0_1


def test_a9_writes_a7_output_envelope(tmp_path: Path) -> None:
    out_report = tmp_path / "a9.json"
    out_env = tmp_path / "a7_env.json"

    verdict = write_a9_report_v0_1(
        out_path=out_report,
        require_seal_ok=False,
        envelope_out_path=out_env,
    )

    assert out_report.is_file()
    assert out_env.is_file()

    payload = json.loads(out_env.read_text(encoding="utf-8"))

    # Required field introduced in P3.2
    assert isinstance(payload.get("policy_verdict_ref"), str)
    assert payload["policy_verdict_ref"] != ""

    env = OutputEnvelopeV0_1(
        schema_version=payload["schema_version"],
        timestamp_utc=payload["timestamp_utc"],
        producer=payload["producer"],
        run_id=payload["run_id"],
        input_seal_ref=payload["input_seal_ref"],
        decision_ref=payload["decision_ref"],
        policy_verdict_ref=payload["policy_verdict_ref"],
        score_total=payload["score_total"],
        score_breakdown=payload["score_breakdown"],
        verdict=payload["verdict"],
        artifacts=payload.get("artifacts", []),
        explainability_trace_ref=payload.get("explainability_trace_ref"),
        signature_policy=payload.get("signature_policy", "seal-only"),
        integrity=payload.get("integrity", ""),
    )

    ok, violations = OutputContractV0_1.validate(env)
    assert ok is True, [f"{v.field}:{v.message}" for v in violations]

    # Sanity: envelope verdict should correspond to audit verdict
    assert (env.verdict == "PASS") == bool(verdict.ok)
