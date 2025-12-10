"""PAS Hardening Suite v0.2

Guardian-style PAS tamper grid – enriched metadata and extra scenarios.

This module is *additive* to v0.1:
- v0.1 remains the canonical, frozen baseline.
- v0.2 reuses v0.1 logic, then upgrades the results with richer metadata.
- New, non-breaking scenarios PAS-010+ are appended.

Callers can choose to keep using v0.1 or opt into v0.2.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List

import subprocess

# We reuse the *behaviour* of v0.1 but return v0.2 result objects.
from pas.pas_hardening_suite_v0_1 import (
    TamperScenarioResult as V01Result,
    Severity as _BaseSeverity,
    run_all_scenarios as run_all_scenarios_v0_1,
)


PAS_HARDENING_VERSION = "0.2"


class Severity(str, Enum):
    """Severity level for PAS checks (duplicated for explicitness in v0.2)."""

    INFO = "INFO"
    WARN = "WARN"
    ALERT = "ALERT"
    CRITICAL = "CRITICAL"


@dataclass
class TamperScenarioResult:
    """Single PAS hardening / tamper scenario result (v0.2 schema).

    This extends the v0.1 shape with richer metadata for continuity,
    observability and cross-layer linking.

    Fields preserved from v0.1:
    - check_id
    - name
    - status
    - severity
    - detected
    - details

    New v0.2 metadata:
    - scenario_id: canonical identifier for the scenario (usually == check_id)
    - component: which subsystem this scenario belongs to (e.g. "env", "git", "pas")
    - tags: free-form tags for filtering and grouping
    """

    check_id: str          # e.g. "PAS-000"
    name: str              # human-readable
    status: str            # "OK", "WARN", "ALERT"
    severity: Severity
    detected: bool
    details: Dict[str, Any]

    # v0.2+ metadata
    scenario_id: str = field(default="")
    component: str = field(default="core")       # e.g. "env", "git", "pas"
    tags: List[str] = field(default_factory=list)


# Alias used by scripts and tests; keeps the semantic meaning.
PasCheckResult = TamperScenarioResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _upgrade_result(
    r: V01Result,
    *,
    component: str = "core",
    tags: List[str] | None = None,
) -> TamperScenarioResult:
    """Upgrade a v0.1 result into the v0.2 dataclass.

    This keeps v0.1 behaviour intact while giving v0.2 callers
    richer metadata and a uniform result type.
    """
    if tags is None:
        tags = []

    # Map v0.1 Severity -> v0.2 Severity (same value space).
    severity = Severity(r.severity.value) if isinstance(r.severity, _BaseSeverity) else Severity.INFO

    scenario_id = getattr(r, "scenario_id", "") or r.check_id

    return TamperScenarioResult(
        check_id=r.check_id,
        name=r.name,
        status=r.status,
        severity=severity,
        detected=r.detected,
        details=dict(r.details),
        scenario_id=scenario_id,
        component=component,
        tags=list(tags),
    )


def _safe_run_git_status() -> Dict[str, Any]:
    """Run a very small 'git status --porcelain' probe, safely.

    Any exception is caught and represented in the return dict instead
    of bubbling up – PAS checks must *never* crash the engine.
    """
    try:
        proc = subprocess.run(
            ["git", "status", "--porcelain"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "error": str(exc),
            "dirty": None,
            "stdout": "",
            "stderr": "",
        }

    output = proc.stdout.strip()
    dirty = bool(output)
    return {
        "ok": proc.returncode == 0,
        "dirty": dirty,
        "stdout": output,
        "stderr": proc.stderr.strip(),
    }


def _safe_import_pytest() -> Dict[str, Any]:
    """Check whether pytest can be imported.

    We treat absence as a WARN (non-fatal) condition, not a crash.
    """
    try:
        import pytest  # type: ignore[import]  # noqa: F401
    except Exception as exc:  # noqa: BLE001
        return {"available": False, "error": str(exc)}
    return {"available": True}


def _check_continuity_manifest_presence() -> Dict[str, Any]:
    """Check whether the continuity manifest file exists.

    This is intentionally gentle in v0.2:
    - Missing manifest → WARN, not a failure.
    - Later versions of L5 can tighten this rule.
    """
    manifest_path = Path("continuity") / "gus_v4_continuity_manifest.json"
    exists = manifest_path.exists()
    return {
        "exists": exists,
        "path": str(manifest_path),
    }


# ---------------------------------------------------------------------------
# v0.2 scenarios
# ---------------------------------------------------------------------------


def _build_pas_010_git_cleanliness() -> TamperScenarioResult:
    """PAS-010: Git cleanliness probe.

    Observes whether the working tree is clean. A dirty tree is reported
    as WARN rather than a hard failure, since developers often work
    with modified files during normal operation.
    """
    details = _safe_run_git_status()
    if not details.get("ok", False):
        status = "WARN"
        severity = Severity.WARN
        detected = True
    elif details.get("dirty"):
        status = "WARN"
        severity = Severity.WARN
        detected = True
    else:
        status = "OK"
        severity = Severity.INFO
        detected = False

    base = V01Result(
        check_id="PAS-010",
        name="Git working tree cleanliness probe",
        status=status,
        severity=_BaseSeverity(severity.value),
        detected=detected,
        details=details,
    )
    return _upgrade_result(
        base,
        component="git",
        tags=["git", "cleanliness", "env"],
    )


def _build_pas_011_pytest_available() -> TamperScenarioResult:
    """PAS-011: pytest availability probe.

    Confirms that pytest can be imported in the current environment.
    """
    details = _safe_import_pytest()
    if details.get("available"):
        status = "OK"
        severity = Severity.INFO
        detected = False
    else:
        status = "WARN"
        severity = Severity.WARN
        detected = True

    base = V01Result(
        check_id="PAS-011",
        name="pytest availability probe",
        status=status,
        severity=_BaseSeverity(severity.value),
        detected=detected,
        details=details,
    )
    return _upgrade_result(
        base,
        component="env",
        tags=["pytest", "tests", "env"],
    )


def _build_pas_012_continuity_manifest_presence() -> TamperScenarioResult:
    """PAS-012: Continuity manifest presence check.

    In v0.2 this only *observes* whether the manifest exists.
    Enforcement (e.g. commit matching) is deferred to later versions.
    """
    details = _check_continuity_manifest_presence()
    if details.get("exists"):
        status = "OK"
        severity = Severity.INFO
        detected = False
    else:
        status = "WARN"
        severity = Severity.WARN
        detected = True

    base = V01Result(
        check_id="PAS-012",
        name="Continuity manifest presence",
        status=status,
        severity=_BaseSeverity(severity.value),
        detected=detected,
        details=details,
    )
    return _upgrade_result(
        base,
        component="continuity",
        tags=["continuity", "manifest", "layer5"],
    )


# ---------------------------------------------------------------------------
# Public runner
# ---------------------------------------------------------------------------


def run_all_scenarios() -> List[TamperScenarioResult]:
    """Run all configured PAS tamper scenarios (v0.2 view).

    The sequence is:
    1. Run v0.1 scenarios (PAS-000, PAS-001, ...)
    2. Upgrade them to the v0.2 schema
    3. Append v0.2-only scenarios PAS-010+
    """
    results_v01 = run_all_scenarios_v0_1()
    upgraded: List[TamperScenarioResult] = [
        _upgrade_result(r, component="pas", tags=["baseline", "v0.1"])
        for r in results_v01
    ]

    upgraded.append(_build_pas_010_git_cleanliness())
    upgraded.append(_build_pas_011_pytest_available())
    upgraded.append(_build_pas_012_continuity_manifest_presence())

    return upgraded


__all__ = [
    "TamperScenarioResult",
    "PasCheckResult",
    "Severity",
    "PAS_HARDENING_VERSION",
    "run_all_scenarios",
]


if __name__ == "__main__":  # pragma: no cover - manual debug helper
    results = run_all_scenarios()
    print(f"PAS Hardening Suite v{PAS_HARDENING_VERSION}")
    for r in results:
        print(
            f"{r.check_id} | {r.name} | status={r.status} "
            f"severity={r.severity} detected={r.detected} "
            f"[component={r.component}] tags={r.tags}"
        )
