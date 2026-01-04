from __future__ import annotations

from layer7_output_contract.output_envelope_v0_1 import OutputEnvelopeV0_1


def test_policy_verdict_ref_is_exported_and_affects_integrity() -> None:
    base = OutputEnvelopeV0_1(
        schema_version="0.1",
        timestamp_utc="2026-01-04T00:00:00Z",
        producer="gus",
        run_id="RUN1",
        input_seal_ref="seal_abc",
        decision_ref="dec_xyz",
        policy_verdict_ref=None,
        score_total=9.9,
        score_breakdown={"TD": 0.99},
        verdict="PASS",
        artifacts=["a1"],
        explainability_trace_ref=None,
    ).with_integrity()

    with_ref = OutputEnvelopeV0_1(
        schema_version="0.1",
        timestamp_utc="2026-01-04T00:00:00Z",
        producer="gus",
        run_id="RUN1",
        input_seal_ref="seal_abc",
        decision_ref="dec_xyz",
        policy_verdict_ref="policy_verdict:pv_001",
        score_total=9.9,
        score_breakdown={"TD": 0.99},
        verdict="PASS",
        artifacts=["a1"],
        explainability_trace_ref=None,
    ).with_integrity()

    d = with_ref.to_dict()
    assert "policy_verdict_ref" in d
    assert d["policy_verdict_ref"] == "policy_verdict:pv_001"

    # Integrity must differ when policy_verdict_ref differs.
    assert base.integrity != with_ref.integrity

    # Verify integrity checks succeed
    assert base.verify_integrity() is True
    assert with_ref.verify_integrity() is True
