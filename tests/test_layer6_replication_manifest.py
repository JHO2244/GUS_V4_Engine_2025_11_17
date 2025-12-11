from layer6_replication.replication_manifest_v0_1 import (
    build_replication_plan_from_continuity,
    ReplicationPlan,
    ReplicationTarget,
)


def test_replication_plan_builds_from_continuity_manifest():
    # Provide at least one hypothetical replication target to ensure the list is populated
    default_targets = [r"D:\GuardianReplicas"]

    plan = build_replication_plan_from_continuity(default_targets=default_targets)

    assert isinstance(plan, ReplicationPlan)
    assert isinstance(plan.source_backup, str)

    # In a healthy continuity state, we expect a non-empty source path
    assert plan.source_backup != ""

    # Targets should be correctly constructed from default_targets
    assert plan.targets
    assert isinstance(plan.targets[0], ReplicationTarget)
    assert plan.targets[0].path == default_targets[0]
