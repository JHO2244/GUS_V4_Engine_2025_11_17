from layer10_policy_verdict.verdict_types_v0_1 import (
    PolicyVerdict,
    RuleHit,
    VerdictCode,
    Severity,
    combine_verdicts,
)


def test_to_dict_is_json_safe_and_stable_keys():
    rh = RuleHit(
        rule_id="R-001",
        rule_version="0.1",
        outcome=VerdictCode.WARN,
        severity=Severity.MED,
        reason="Demo",
        tags=("policy", "test"),
    )
    v = PolicyVerdict(
        code=VerdictCode.WARN,
        severity=Severity.MED,
        summary="Warn summary",
        reason_codes=("RC-1",),
        rule_hits=(rh,),
        tags=("t1",),
        metadata={"a": 1},
    )
    d = v.to_dict()
    assert d["code"] == "WARN"
    assert d["severity"] == "MED"
    assert d["rule_hits"][0]["rule_id"] == "R-001"
    assert d["rule_hits"][0]["tags"] == ["policy", "test"]


def test_combine_denies_override():
    allow = PolicyVerdict(code=VerdictCode.ALLOW, severity=Severity.LOW, summary="ok")
    deny = PolicyVerdict(code=VerdictCode.DENY, severity=Severity.HIGH, summary="no")
    out = combine_verdicts([allow, deny])
    assert out.code == VerdictCode.DENY
    assert out.severity == Severity.HIGH


def test_combine_warn_over_allow():
    allow = PolicyVerdict(code=VerdictCode.ALLOW, severity=Severity.HIGH, summary="ok")
    warn = PolicyVerdict(code=VerdictCode.WARN, severity=Severity.LOW, summary="careful")
    out = combine_verdicts([allow, warn])
    assert out.code == VerdictCode.WARN
    assert out.severity == Severity.HIGH  # max severity fold
