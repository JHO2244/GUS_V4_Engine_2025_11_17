from pas.pas_hardening_suite_v0_1 import (
    run_all_scenarios,
    TamperScenarioResult,
    Severity,
)


def test_run_all_scenarios_returns_list():
    results = run_all_scenarios()
    assert isinstance(results, list)


def test_results_are_well_formed_if_present():
    results = run_all_scenarios()

    for r in results:
        assert isinstance(r, TamperScenarioResult)
        assert isinstance(r.name, str)
        assert isinstance(r.detected, bool)
        assert isinstance(r.details, dict)
        assert isinstance(r.severity, Severity)
