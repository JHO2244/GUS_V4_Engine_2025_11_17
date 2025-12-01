from layer2_governance_matrix.L2_governance_stub import (
    load_governance_status,
    load_councils,
    load_construction_laws,
    load_schema
)

def test_L2_schema_loads():
    assert load_schema() is True


def test_L2_councils_load():
    councils, errors = load_councils()
    assert isinstance(councils, list)
    assert len(errors) == 0


def test_L2_laws_load():
    laws, errors = load_construction_laws()
    assert isinstance(laws, list)
    assert len(errors) == 0


def test_L2_governance_status_ok():
    status = load_governance_status()
    assert status.councils_count >= 3
    assert status.laws_count >= 2
    assert status.schema_loaded is True
    assert isinstance(status.errors, list)
