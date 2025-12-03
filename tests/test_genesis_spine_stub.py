from layer1_integrity_core.chain import genesis_spine_stub as gs
from pas.pas_seal_engine_stub import mint_phase2_continuity_seal


def test_spine_has_three_layers_in_order():
    spine = gs.compute_l0_l1_l2_spine()
    layer_ids = [entry["layer_id"] for entry in spine]
    assert layer_ids == ["L0", "L1", "L2"]

    # Root must have no parent; others must daisy-chain correctly.
    assert spine[0]["parent_hash"] is None
    assert spine[1]["parent_hash"] == spine[0]["chain_hash"]
    assert spine[2]["parent_hash"] == spine[1]["chain_hash"]


def test_genesis_hash_matches_last_chain_entry():
    spine = gs.compute_l0_l1_l2_spine()
    genesis_hash = gs.get_genesis_hash()

    assert genesis_hash == spine[-1]["chain_hash"]
    assert isinstance(genesis_hash, str)
    assert len(genesis_hash) == 64  # hex-encoded SHA-256


def test_pas_seal_includes_genesis_hash():
    seal = mint_phase2_continuity_seal()
    payload = seal["payload"]
    meta = payload["meta"]

    genesis_hash = gs.get_genesis_hash()

    assert meta["genesis_hash"] == genesis_hash
    assert isinstance(meta["genesis_hash"], str)
    assert len(meta["genesis_hash"]) == 64
