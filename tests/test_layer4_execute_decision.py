def test_execute_decision_blocks_non_approved():
    from layer4_execution.L4_decision_bridge import execute_decision

    denied = {
        "decision_id": "X",
        "requested_action": "noop",
        "layer_origin": 3,
        "status": "denied",
    }

    assert execute_decision(denied, {"k": "v"}) is False
