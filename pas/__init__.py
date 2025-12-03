"""
PAS package – Phase 3 Hardening & Tamper Detection (v0.1 stubs).

This module simply re-exports the small public API surface that the
tests and other layers expect to see.
"""

from .pas_hardening_suite_v0_1 import (
    TamperScenarioResult,
    Severity,
    PAS_HARDENING_VERSION,
    run_all_scenarios,
)

__all__ = [
    "TamperScenarioResult",
    "Severity",
    "PAS_HARDENING_VERSION",
    "run_all_scenarios",
]
