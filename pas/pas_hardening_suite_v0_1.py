"""
PAS Hardening Suite v0.2

Guardian-style PAS tamper grid:
- v0.1: proved the shape and wiring.
- v0.2: adds a small, deterministic tamper grid over critical GUS surfaces.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Callable

# Public version tag used by tests and other PAS modules
PAS_HARDENING_VERSION: str = "0.2"


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

    v0.2 extensions (non-breaking):
    - scenario_id: stable PAS-XXX identifier for the scenario
    - description: short human-facing description of what was checked
    - recommendation: optional remediation hint if a problem is detected
    """
    name: str
    severity: Severity
    detected: bool
    details: Dict[str, Any]
    scenario_id: str = "PAS-UNSET"
    description: str = ""
    recommendation: str | None = None


# ---- Internal scenario registry ------------------------------------------------

ScenarioFn = Callable[[], TamperScenarioResult]
_SCENARIO_REGISTRY: List[ScenarioFn] = []


def register_scenario(fn: ScenarioFn) -> ScenarioFn:
    """Decorator to register a PAS scenario in the internal registry."""
    _SCENARIO_REGISTRY.append(fn)
    return fn


# ---- v0.2 scenarios ------------------------------------------------------------

@register_scenario
def scenario_pas_000_baseline() -> TamperScenarioResult:
    """
    PAS-000 – Baseline sanity check.

    Confirms that the PAS hardening suite imported correctly and that the
    scenario grid can execute at least one scenario.
    """
    return TamperScenarioResult(
        scenario_id="PAS-000",
        name="PAS-000: baseline sanity check",
        description="PAS hardening suite imported and baseline scenario executed.",
        severity=Severity.INFO,
        detected=True,
        details={
            "note": "PAS hardening suite imported and baseline scenario executed.",
            "version": PAS_HARDENING_VERSION,
        },
        recommendation=None,
    )


@register_scenario
def scenario_genesis_spine_importable() -> TamperScenarioResult:
    """
    PAS-001 – Genesis spine importability.

    Check: can we import the Layer 1 genesis spine stub module?
    This is a Guardian-critical surface; failure indicates structural
    tamper or misconfiguration.
    """
    module_name = "layer1_integrity_core.chain.genesis_spine_stub"
    import_ok = False
    error_repr: str | None = None

    try:
        __import__(module_name, fromlist=["*"])
        import_ok = True
    except Exception as exc:  # pragma: no cover - defensive
        error_repr = repr(exc)

    if import_ok:
        severity = Severity.INFO
        detected = False  # no tamper detected
        description = "Genesis spine stub is importable."
        recommendation = None
    else:
        severity = Severity.WARNING
        detected = True
        description = "Genesis spine stub could not be imported."
        recommendation = (
            "Ensure layer1_integrity_core.chain.genesis_spine_stub exists and "
            "is importable in the current environment."
        )

    details: Dict[str, Any] = {
        "module": module_name,
        "import_ok": import_ok,
    }
    if error_repr is not None:
        details["error"] = error_repr

    return TamperScenarioResult(
        scenario_id="PAS-001",
        name="PAS-001: genesis spine importable",
        description=description,
        severity=severity,
        detected=detected,
        details=details,
        recommendation=recommendation,
    )


@register_scenario
def scenario_chain_directory_presence() -> TamperScenarioResult:
    """
    PAS-002 – Chain directory presence.

    Check: does the Layer 1 chain directory exist, and are the key files present?
    This is a safe, read-only filesystem check.
    """
    repo_root = Path(__file__).resolve().parent.parent
    chain_dir = repo_root / "layer1_integrity_core" / "chain"
    expected_files = [
        "genesis_spine_stub.py",
        "gus_chain_v4_stub.py",
        "__init__.py",
    ]

    exists = chain_dir.exists() and chain_dir.is_dir()
    missing_files: List[str] = []

    if exists:
        present_names = {p.name for p in chain_dir.iterdir() if p.is_file()}
        missing_files = [name for name in expected_files if name not in present_names]

    if not exists:
        severity = Severity.CRITICAL
        detected = True
        description = "Layer 1 chain directory is missing."
        recommendation = (
            "Create layer1_integrity_core/chain and restore required chain modules."
        )
    elif missing_files:
        severity = Severity.WARNING
        detected = True
        description = "Layer 1 chain directory is present but missing key files."
        recommendation = (
            "Restore missing chain files to maintain the integrity spine surface."
        )
    else:
        severity = Severity.INFO
        detected = False
        description = "Layer 1 chain directory and key files are present."
        recommendation = None

    details: Dict[str, Any] = {
        "chain_dir": str(chain_dir),
        "exists": exists,
        "expected_files": expected_files,
        "missing_files": missing_files,
    }

    return TamperScenarioResult(
        scenario_id="PAS-002",
        name="PAS-002: chain directory presence",
        description=description,
        severity=severity,
        detected=detected,
        details=details,
        recommendation=recommendation,
    )


@register_scenario
def scenario_logs_surface_presence() -> TamperScenarioResult:
    """
    PAS-003 – Logs surface presence.

    Check: do the integrity / governance / execution log directories exist?
    These are non-destructive, directory-level checks only.
    """
    repo_root = Path(__file__).resolve().parent.parent
    log_paths = {
        "logs/integrity": repo_root / "logs" / "integrity",
        "logs/governance": repo_root / "logs" / "governance",
        "logs/execution": repo_root / "logs" / "execution",
    }

    exists_map = {key: path.exists() and path.is_dir() for key, path in log_paths.items()}
    missing = [key for key, ok in exists_map.items() if not ok]

    if missing:
        severity = Severity.WARNING
        detected = True
        description = "One or more log directories are missing."
        recommendation = (
            "Create the missing log directories to ensure audit surfaces are available."
        )
    else:
        severity = Severity.INFO
        detected = False
        description = "All core log directories are present."
        recommendation = None

    details: Dict[str, Any] = {
        "paths": {key: str(path) for key, path in log_paths.items()},
        "exists": exists_map,
        "missing": missing,
    }

    return TamperScenarioResult(
        scenario_id="PAS-003",
        name="PAS-003: logs surface presence",
        description=description,
        severity=severity,
        detected=detected,
        details=details,
        recommendation=recommendation,
    )


# ---- Public API ----------------------------------------------------------------


def _build_baseline_scenarios() -> List[TamperScenarioResult]:
    """
    v0.2 keeps this helper for backwards compatibility with any code that
    still expects the original baseline builder.

    It currently returns only the PAS-000 baseline scenario.
    """
    return [scenario_pas_000_baseline()]


def run_all_scenarios() -> List[TamperScenarioResult]:
    """
    Run all configured PAS tamper scenarios and return their results.

    In v0.2 this returns all registered scenarios (baseline + grid).
    """
    results: List[TamperScenarioResult] = []

    for fn in _SCENARIO_REGISTRY:
        try:
            results.append(fn())
        except Exception as exc:  # pragma: no cover - defensive
            # If a scenario itself blows up, surface this as a synthetic,
            # high-severity PAS error scenario instead of failing hard.
            results.append(
                TamperScenarioResult(
                    scenario_id="PAS-ERR",
                    name=f"Exception in {fn.__name__}",
                    description="PAS scenario raised an exception.",
                    severity=Severity.CRITICAL,
                    detected=True,
                    details={"error": repr(exc)},
                    recommendation="Inspect PAS scenario implementation.",
                )
            )

    return results


def summarize_by_severity(results: List[TamperScenarioResult]) -> Dict[Severity, int]:
    """
    Small helper to aggregate counts by Severity for dashboards or logs.
    Not used by tests, but useful for higher-level reporting.
    """
    summary: Dict[Severity, int] = {s: 0 for s in Severity}
    for r in results:
        summary[r.severity] += 1
    return summary


__all__ = [
    "TamperScenarioResult",
    "Severity",
    "PAS_HARDENING_VERSION",
    "run_all_scenarios",
    "summarize_by_severity",
]
