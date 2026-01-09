from layer1_security_spine.gdvs_state_machine_v0_1 import GDVSState, assert_transition, GDVSViolation


def test_gdvs_allows_forward_transitions_only():
    assert_transition(GDVSState.INIT, GDVSState.D1_STRUCTURAL)
    assert_transition(GDVSState.D1_STRUCTURAL, GDVSState.D2_DETERMINISM)
    assert_transition(GDVSState.D2_DETERMINISM, GDVSState.D3_SECURITY)
    assert_transition(GDVSState.D3_SECURITY, GDVSState.D4_POLICY)
    assert_transition(GDVSState.D4_POLICY, GDVSState.D5_PRIVACY)
    assert_transition(GDVSState.D5_PRIVACY, GDVSState.D6_WORLD)
    assert_transition(GDVSState.D6_WORLD, GDVSState.D7_FUTURE_AI)
    assert_transition(GDVSState.D7_FUTURE_AI, GDVSState.D8_OPERATIONAL)
    assert_transition(GDVSState.D8_OPERATIONAL, GDVSState.SEALED)
    assert_transition(GDVSState.SEALED, GDVSState.LOCKED)


def test_gdvs_rejects_invalid_transitions():
    try:
        assert_transition(GDVSState.INIT, GDVSState.D2_DETERMINISM)
        raise AssertionError("Expected GDVSViolation not raised")
    except GDVSViolation:
        pass

    try:
        assert_transition(GDVSState.D4_POLICY, GDVSState.D3_SECURITY)
        raise AssertionError("Expected GDVSViolation not raised")
    except GDVSViolation:
        pass
