from layer9_policy_verdict.src.ruleset import apply_ruleset_v1, score_from_policy_and_rules


def test_ruleset_deterministic_and_reasoned():
    action = {"type": "merge_pr", "target": "main"}
    context = {"actor": "JHO", "checks": "green"}

    rules = apply_ruleset_v1(action=action, context=context)
    rule_ids = [r.rule_id for r in rules]

    assert "R1_CHECKS_GREEN" in rule_ids
    assert "R3_ACTOR_PRESENT" in rule_ids

    score, reasons = score_from_policy_and_rules(base_score=9.8, rules=rules)
    assert 0.0 <= score <= 10.0
    assert len(reasons) >= 2


def test_score_clamps_high_and_low():
    action = {"type": "merge_pr", "target": "main"}
    context = {"checks": "green"}

    rules = apply_ruleset_v1(action=action, context=context)

    score_hi, _ = score_from_policy_and_rules(base_score=10.0, rules=rules)
    assert score_hi == 10.0

    score_lo, _ = score_from_policy_and_rules(base_score=-5.0, rules=rules)
    assert score_lo == 0.0
