"""
PAS Hardening Suite v0.1

Tiny, well-typed baseline so the PAS tests can verify wiring and shape
without us committing to heavy logic yet.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Dict, List

# Public version tag used by tests and other PAS modules
PAS_HARDENING_VERSION: str = "0.1"


class Severity(Enum):
    """Basic severity levels for PAS tamper scenarios."""
    INFO = auto()
    WARNING = auto()
    CRITICAL = auto()


@dataclass
class TamperScenarioResult:
    """
    Result for a single PAS tamper scenario.

    Fields are shaped to match what the tests expect:
    - name: human-readable identifier for the scenario
    - severity: Severity enum
    - detected: whether the condition was observed
    - details: free-form metadata payload
    """
    name: str
    severity: Severity
    detected: bool
    details: Dict[str, Any]


def _build_baseline_scenarios() -> List[TamperScenarioResult]:
    """
    Build the minimal baseline set of scenarios for v0.1.

    We only wire a single “sanity check” scenario for now – the point
    is to prove the API and integration work, not to implement
    real tamper detection yet.
    """
    return [
        TamperScenarioResult(
            name="PAS-000: baseline sanity check",
            severity=Severity.INFO,
            detected=True,
            details={
                "note": "PAS hardening suite imported and baseline scenario executed.",
                "version": PAS_HARDENING_VERSION,
            },
        )
    ]


def run_all_scenarios() -> List[TamperScenarioResult]:
    """
    Run all configured PAS tamper scenarios and return their results.

    In v0.1 this just returns the baseline wiring scenario.
    """
    return _build_baseline_scenarios()


__all__ = [
    "TamperScenarioResult",
    "Severity",
    "PAS_HARDENING_VERSION",
    "run_all_scenarios",
]
