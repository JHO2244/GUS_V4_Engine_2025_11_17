from layer9_policy_verdict.src.verdict_ledger_bridge import append_verdict_to_ledger
from layer9_policy_verdict.src.verdict_types import PolicyVerdict, VerdictLevel


def test_verdict_appended_to_ledger():
    verdict = PolicyVerdict(
        level=VerdictLevel.ALLOW,
        score=9.9,
        reasons=["test"],
        evidence={},
        policy_id="P_TEST",
        epoch_ref="epoch_test",
        chain_head="head_test",
        object_hash="abc123" * 10
    )

    result = append_verdict_to_ledger(verdict)

    assert "hash" in result
    assert result["hash"] is not None
    assert result["entry"]["decision"]["verdict_hash"] == verdict.object_hash
    assert result["entry"]["decision"]["policy_id"] == "P_TEST"

