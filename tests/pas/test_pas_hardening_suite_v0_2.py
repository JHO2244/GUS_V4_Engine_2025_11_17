from pathlib import Path

from pas.pas_hardening_suite_v0_2 import (
    TamperScenarioResult,
    Severity,
    PAS_HARDENING_VERSION,
    run_all_scenarios,
)


def test_pas_version_tag_v0_2():
    assert PAS_HARDENING_VERSION == "0.2"


def test_run_all_scenarios_returns_enriched_results():
    results = run_all_scenarios()
    assert isinstance(results, list)
    assert results, "Expected at least one PAS result"

    for r in results:
        assert isinstance(r, TamperScenarioResult)
        assert isinstance(r.name, str)
        assert isinstance(r.check_id, str)
        assert r.check_id.startswith("PAS-")

        assert isinstance(r.detected, bool)
        assert isinstance(r.details, dict)
        assert isinstance(r.severity, Severity)

        # v0.2 metadata
        assert isinstance(r.scenario_id, str)
        assert r.scenario_id.startswith("PAS-")
        assert isinstance(r.component, str)
        assert isinstance(r.tags, list)
