from layer7_certification.L7_certifier_stub import issue_certificate

def test_issue_certificate_requires_locks():
    # Assumes L5/L6 are locked true in repo state (Phase 3).
    res = issue_certificate(subject={"repo":"GUS_V4"}, scores={"TD":1.0,"SC":0.0,"AP":1.0,"RL":1.0})
    assert res.ok is True
    assert res.certificate is not None
    assert "receipt_hash" in res.certificate
    assert len(res.certificate["receipt_hash"]) == 64
