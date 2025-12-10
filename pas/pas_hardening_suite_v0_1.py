"""
PAS Hardening Suite v0.1

Guardian-style PAS tamper grid baseline.

This module intentionally stays small and strongly typed in v0.1:
- It exposes a single dataclass `TamperScenarioResult` describing a PAS check.
- `run_all_scenarios()` returns a list of these results.
- `PAS_HARDENING_VERSION` announces the schema version for callers.

The tests only care about the *shape* of the data, not the specific logic.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List


# ---------------------------------------------------------------------------
# Public version tag
# ---------------------------------------------------------------------------

PAS_HARDENING_VERSION: str = "0.1"


# ---------------------------------------------------------------------------
# Core types
# ---------------------------------------------------------------------------


class Severity(str, Enum):
    """Minimal severity scale for PAS checks."""

    INFO = "INFO"
    WARN = "WARN"
    ALERT = "ALERT"
    CRITICAL = "CRITICAL"


@dataclass
class TamperScenarioResult:
    """
    Single PAS hardening / tamper scenario result.

    The test suite expects *at least* these fields:
      - name: str
      - detected: bool
      - details: dict
      - severity: Severity

    We also include a few extra fields that are convenient for scripts,
    such as a machine-identifiable check_id and a simple status code.
    """

    check_id: str
    name: str
    status: str        # e.g. "OK", "WARN", "ALERT"
    severity: Severity
    detected: bool
    details: Dict[str, Any]

    # v0.2+ extra; non-breaking, default maps to check_id semantics
    scenario_id: str = field(default="")


# Alias used by scripts.pas_status and tests; keeping it as a direct alias
# means isinstance(x, TamperScenarioResult) is still true.
PasCheckResult = TamperScenarioResult


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _build_pas_000_baseline() -> TamperScenarioResult:
    """
    PAS-000: Baseline sanity check.

    v0.1 keeps this intentionally lightweight: if this code is executing,
    the PAS module imported correctly and the basic wiring is intact.
    We treat that as "no tamper detected".
    """

    return TamperScenarioResult(
        check_id="PAS-000",
        name="PAS-000: baseline sanity check",
        status="OK",
        severity=Severity.INFO,
        detected=False,  # no tamper detected
        details={
            "description": "PAS module imported and baseline check executed.",
        },
        scenario_id="PAS-000",
    )


def _build_pas_001_genesis_import() -> TamperScenarioResult:
    """
    PAS-001: Verify that the genesis spine can be imported.

    This gives us a second concrete check that lightly touches the
    integrity chain without enforcing heavy semantics.
    """

    try:
        # Import side-effect is enough for this v0.1.
        from layer1_integrity_core.chain import genesis_spine_stub  # type: ignore  # noqa: F401

        import_ok = True
        status = "OK"
        severity = Severity.INFO
        message = "Genesis spine imported successfully."
    except Exception as exc:  # pragma: no cover - error path
        import_ok = False
        status = "ALERT"
        severity = Severity.CRITICAL
        message = f"Genesis spine import failed: {exc.__class__.__name__}: {exc}"

    return TamperScenarioResult(
        check_id="PAS-001",
        name="PAS-001: genesis spine importable",
        status=status,
        severity=severity,
        detected=not import_ok,  # detected == True → something is wrong
        details={
            "import_success": import_ok,
            "message": message,
        },
        scenario_id="PAS-001",
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def run_all_scenarios() -> List[TamperScenarioResult]:
    """
    Run all configured PAS tamper scenarios and return their results.

    In v0.1 we keep this very small: just PAS-000 and PAS-001.
    More checks can be appended later without breaking the tests.
    """
    return [
        _build_pas_000_baseline(),
        _build_pas_001_genesis_import(),
    ]


__all__ = [
    "TamperScenarioResult",
    "PasCheckResult",
    "Severity",
    "PAS_HARDENING_VERSION",
    "run_all_scenarios",
]


if __name__ == "__main__":
    # Tiny debug runner, optional, safe to leave in.
    results = run_all_scenarios()
    print(f"PAS Hardening Suite v{PAS_HARDENING_VERSION}")
    for r in results:
        print(
            f"{r.check_id} | {r.name} | status={r.status} "
            f"severity={r.severity} detected={r.detected}"
        )
