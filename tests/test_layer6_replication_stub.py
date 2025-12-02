from layer5_continuity import load_continuity_status, verify_continuity

def test_continuity_status_loads():
    status = load_continuity_status()
    assert status.code == "ok"
    assert isinstance(status.errors, list)

def test_continuity_verify_ok():
    assert verify_continuity() is True

