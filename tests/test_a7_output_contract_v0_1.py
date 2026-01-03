from layer7_output_contract.output_envelope_v0_1 import OutputEnvelopeV0_1
from layer7_output_contract.output_contract_v0_1 import OutputContractV0_1


def _good_env() -> OutputEnvelopeV0_1:
    env = OutputEnvelopeV0_1(
        schema_version=OutputContractV0_1.SCHEMA,
        timestamp_utc="2026-01-03T12:00:00Z",
        producer="GUS_V4_ENGINE",
        run_id="run-123",
        input_seal_ref="seals/seal_example.json",
        decision_ref="decision:abc123",
        score_total=9.9,
        score_breakdown={"TD": 9.9, "SC": 9.9, "AP": 9.9, "RL": 9.9},
        verdict="PASS",
        artifacts=["artifact:a"],
        explainability_trace_ref="trace:xyz",
        signature_policy="seal-only",
        integrity="",
    ).with_integrity()
    return env


def test_contract_accepts_valid_envelope():
    env = _good_env()
    ok, violations = OutputContractV0_1.validate(env)
    assert ok is True
    assert violations == []


def test_contract_rejects_missing_integrity():
    env = _good_env()
    env2 = OutputEnvelopeV0_1(**{**env.to_dict(include_integrity=True), "integrity": ""})  # type: ignore
    ok, violations = OutputContractV0_1.validate(env2)
    assert ok is False
    assert any(v.field == "integrity" for v in violations)


def test_contract_rejects_bad_score_total():
    env = _good_env()
    env2 = OutputEnvelopeV0_1(**{**env.to_dict(include_integrity=True), "score_total": 99.0})  # type: ignore
    ok, violations = OutputContractV0_1.validate(env2)
    assert ok is False
    assert any(v.field == "score_total" for v in violations)


def test_contract_requires_breakdown_keys():
    env = _good_env()
    bad_breakdown = {"TD": 9.9, "SC": 9.9}  # missing AP, RL
    env2 = OutputEnvelopeV0_1(**{**env.to_dict(include_integrity=True), "score_breakdown": bad_breakdown}).with_integrity()  # type: ignore
    ok, violations = OutputContractV0_1.validate(env2)
    assert ok is False
    assert any(v.field == "score_breakdown" for v in violations)
