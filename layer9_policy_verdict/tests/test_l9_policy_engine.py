from __future__ import annotations
from layer9_policy_verdict.src.policy_engine import evaluate_policy
from layer9_policy_verdict.src.verdict_types import VerdictLevel

def test_deterministic_hash_and_verdict():
    action = {"type": "merge", "target": "main"}
    context = {"repo": "GUS_V4_Engine_2025_11_17", "drift_commits": 0}
    policy = {"policy_id": "L9_BASE", "thresholds": {"allow": 9.7, "warn": 8.5}, "base_score": 9.8}

    v1 = evaluate_policy(action=action, context=context, policy=policy, epoch_ref="epoch_X", chain_head="head_A")
    v2 = evaluate_policy(action=action, context=context, policy=policy, epoch_ref="epoch_X", chain_head="head_A")

    assert v1.level == v2.level
    assert v1.score == v2.score
    assert v1.object_hash == v2.object_hash
    assert v1.object_hash and len(v1.object_hash) == 64


def test_merge_pr_to_main_is_allow_when_base_score_high():
    from layer9_policy_verdict.src.policy_engine import evaluate_policy
    from layer9_policy_verdict.src.verdict_types import VerdictLevel

    action = {"type": "merge_pr", "target": "main"}
    context = {"repo": "GUS_V4_Engine_2025_11_17", "drift_commits": 0}
    policy = {"policy_id": "L9_BASE", "thresholds": {"allow": 9.7, "warn": 8.5}, "base_score": 9.8}

    v = evaluate_policy(action=action, context=context, policy=policy, epoch_ref="epoch_X", chain_head="head_A")
    assert v.level == VerdictLevel.ALLOW
    assert v.score >= 9.7
    assert v.reasons

def test_threshold_mapping_allow_warn_block():
    action = {"type": "test"}
    context = {"drift_commits": 2}

    p_allow = {"policy_id": "P_ALLOW", "thresholds": {"allow": 9.7, "warn": 8.5}, "base_score": 9.7}
    v_allow = evaluate_policy(action=action, context=context, policy=p_allow, epoch_ref="epoch_X", chain_head="h")
    assert v_allow.level == VerdictLevel.ALLOW

    p_warn = {"policy_id": "P_WARN", "thresholds": {"allow": 9.7, "warn": 8.5}, "base_score": 8.5}
    v_warn = evaluate_policy(action=action, context=context, policy=p_warn, epoch_ref="epoch_X", chain_head="h")
    assert v_warn.level == VerdictLevel.WARN

    p_block = {"policy_id": "P_BLOCK", "thresholds": {"allow": 9.7, "warn": 8.5}, "base_score": 8.49}
    v_block = evaluate_policy(action=action, context=context, policy=p_block, epoch_ref="epoch_X", chain_head="h")
    assert v_block.level == VerdictLevel.BLOCK

def test_rejects_invalid_policy_missing_thresholds():
    import pytest
    from layer9_policy_verdict.src.policy_schema import PolicySchemaError

    action = {"type": "action"}
    context = {"x": 1}
    policy = {"policy_id": "P", "base_score": 9.0}  # missing thresholds

    with pytest.raises(PolicySchemaError):
        evaluate_policy(action=action, context=context, policy=policy, epoch_ref="epoch_X", chain_head="h")


def test_valid_policy_base_score_within_bounds():
    action = {"type": "action"}
    context = {"x": 1}
    policy = {
        "policy_id": "P",
        "thresholds": {"allow": 9.7, "warn": 8.5},
        "base_score": 9.9
    }

    v = evaluate_policy(
        action=action,
        context=context,
        policy=policy,
        epoch_ref="epoch_X",
        chain_head="h"
    )

    assert 0.0 <= v.score <= 10.0
    assert v.score == 9.9
    assert v.level.value in {"allow", "warn", "block"}
    assert v.policy_id == "P"
