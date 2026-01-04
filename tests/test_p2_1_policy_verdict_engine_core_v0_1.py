from layer10_policy_verdict.policy_rules_v0_1 import RuleContext
from layer10_policy_verdict.policy_verdict_engine_v0_1 import PolicyVerdictEngine
from layer10_policy_verdict.verdict_types_v0_1 import VerdictCode


def test_engine_default_allow_when_no_rules_apply():
    eng = PolicyVerdictEngine()
    ctx = RuleContext(action_id="A", actor_id="X", inputs={"action": "do", "target": "t"})
    out = eng.evaluate(ctx)
    assert out.code == VerdictCode.ALLOW


def test_engine_warn_missing_keys():
    eng = PolicyVerdictEngine()
    ctx = RuleContext(action_id="A", actor_id="X", inputs={"action": "do"})
    out = eng.evaluate(ctx)
    assert out.code == VerdictCode.WARN


def test_engine_deny_overrides_warn():
    eng = PolicyVerdictEngine()
    ctx = RuleContext(action_id="A", actor_id="X", inputs={"action": "do", "deny": True})
    out = eng.evaluate(ctx)
    assert out.code == VerdictCode.DENY


def test_engine_abstain_on_empty_inputs():
    eng = PolicyVerdictEngine()
    ctx = RuleContext(action_id="A", actor_id="X", inputs={})
    out = eng.evaluate(ctx)
    assert out.code == VerdictCode.ABSTAIN
