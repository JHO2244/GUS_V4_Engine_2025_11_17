"""
tests/test_engine_health.py
Basic sanity checks for the unified GUS v4 engine health summary.
"""

from gus_engine_health import get_engine_health, get_engine_health_as_dict


def test_engine_health_object_ok():
    health = get_engine_health()

    # EngineHealth should say overall_ok when all layers are green
    assert hasattr(health, "overall_ok")
    assert hasattr(health, "layers")
    assert isinstance(health.layers, dict)
    # We expect layers 0–9 at this stage
    assert set(health.layers.keys()) == set(range(10))

    # Every layer should report verified=True and no errors
    for layer_id, layer_health in health.layers.items():
        assert layer_health.verified is True
        assert isinstance(layer_health.errors, list)
        assert len(layer_health.errors) == 0


def test_engine_health_dict_shape():
    health_dict = get_engine_health_as_dict()

    assert "overall_ok" in health_dict
    assert "layers" in health_dict
    assert isinstance(health_dict["layers"], dict)
    assert set(health_dict["layers"].keys()) == {str(i) for i in range(10)} or set(
        health_dict["layers"].keys()
    ) == set(range(10))
