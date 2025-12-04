"""
Basic tests for scripts.verify_environment v0.1

We only assert structural properties to avoid flaky,
machine-specific failures. This keeps the suite reliable.
"""

from scripts import verify_environment


def test_run_checks_returns_non_empty_list():
    results = verify_environment.run_checks()
    assert isinstance(results, list)
    assert results, "Expected at least one environment check result"


def test_each_result_has_core_fields():
    results = verify_environment.run_checks()
    for r in results:
        assert hasattr(r, "check_id")
        assert hasattr(r, "name")
        assert hasattr(r, "severity")
        assert hasattr(r, "ok")
        assert hasattr(r, "details")
