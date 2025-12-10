"""
PAS package initialization.

Minimal public API for the PAS hardening layer.
"""

from .pas_hardening_suite_v0_1 import (
    PAS_HARDENING_VERSION,
    Severity,
    TamperScenarioResult,
    PasCheckResult,
    run_all_scenarios,
)

__all__ = [
    "PAS_HARDENING_VERSION",
    "Severity",
    "TamperScenarioResult",
    "PasCheckResult",
    "run_all_scenarios",
]
