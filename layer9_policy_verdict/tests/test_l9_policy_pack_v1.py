from layer9_policy_verdict.src.policy_loader import load_policy


def test_policy_pack_files_load_and_validate():
    for fname in [
        "L9_BASE_STRICT.json",
        "L9_MERGE_MAIN.json",
        "L9_HOTFIX.json",
        "L9_READONLY.json",
    ]:
        p = load_policy(fname)
        assert "policy_id" in p
        assert "thresholds" in p
        assert 0.0 <= float(p.get("base_score", 0.0)) <= 10.0


def test_policy_ids_are_unique():
    files = [
        "L9_BASE_STRICT.json",
        "L9_MERGE_MAIN.json",
        "L9_HOTFIX.json",
        "L9_READONLY.json",
    ]
    ids = [load_policy(f)["policy_id"] for f in files]
    assert len(ids) == len(set(ids))
