from layer10_policy_verdict.policy_rules_v0_1 import (
    RuleContext,
    RuleAbstainOnEmptyInputs,
    RuleWarnMissingRequiredKeys,
    RuleDenyExplicitFlag,
)
from layer10_policy_verdict.verdict_types_v0_1 import VerdictCode


def test_abstain_on_empty_inputs():
    r = RuleAbstainOnEmptyInputs()
    v = r.evaluate(RuleContext(action_id="A", actor_id="X", inputs={}))
    assert v is not None
    assert v.code == VerdictCode.ABSTAIN
    assert v.rule_hits[0].rule_id == "PV-RULE-ABSTAIN-EMPTY"


def test_warn_missing_required_keys():
    r = RuleWarnMissingRequiredKeys(required_keys=("action", "target"))
    v = r.evaluate(RuleContext(action_id="A", actor_id="X", inputs={"action": "do"}))
    assert v is not None
    assert v.code == VerdictCode.WARN
    assert "missing_keys" in v.metadata
    assert v.metadata["missing_keys"] == ["target"]


def test_deny_explicit_flag():
    r = RuleDenyExplicitFlag()
    v = r.evaluate(RuleContext(action_id="A", actor_id="X", inputs={"deny": True}))
    assert v is not None
    assert v.code == VerdictCode.DENY
    assert v.metadata.get("deny_flag") is True
