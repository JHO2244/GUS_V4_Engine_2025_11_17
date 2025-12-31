from layer9_policy_verdict.src.policy_engine import evaluate_policy
from layer9_policy_verdict.src.verdict_types import VerdictLevel


def test_engine_applies_ruleset_and_sets_level():
    action = {"type": "merge_pr", "target": "main"}
    context = {"actor": "JHO", "checks": "green"}
    policy = {"policy_id": "P", "thresholds": {"allow": 9.8, "warn": 9.0}, "base_score": 9.8}

    v = evaluate_policy(action=action, context=context, policy=policy, epoch_ref="epoch_X", chain_head="h")

    assert v.score == 10.0  # 9.8 + 0.2 from checks green → clamps to 10
    assert v.level == VerdictLevel.ALLOW
    assert any("R1_CHECKS_GREEN" in r for r in v.reasons)
