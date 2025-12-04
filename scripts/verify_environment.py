"""
GUS v4 – Environment Verification v0.1
--------------------------------------
Purpose:
    Lightweight, non-destructive verification of the local environment
    that GUS v4 runs inside.

    Focus in v0.1:
        - OS + Python introspection
        - venv detection
        - GUS folder structure sanity
        - Git repo presence
        - Backup configuration placeholder

    This is intentionally conservative and read-only.
    Future versions (v0.2+) can add:
        - BitLocker / VeraCrypt status hooks
        - ESET / firewall / VPN checks
        - More detailed backup verification

Usage:
    python -m scripts.verify_environment
"""

from __future__ import annotations

import os
import sys
import platform
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List


class Severity(str, Enum):
    INFO = "INFO"
    WARN = "WARN"
    CRITICAL = "CRITICAL"


@dataclass
class EnvCheckResult:
    check_id: str
    name: str
    severity: Severity
    ok: bool
    details: Dict[str, Any]


PROJECT_ROOT_MARKERS = [
    "gus_v4_manifest.json",
    "layer0_uam_v4",
    "layer1_integrity_core",
    "layer2_governance_matrix",
    "layer3_decision_engine",
    "layer4_execution",
    "layer5_continuity",
    "layer6_replication",
    "layer7_ecosystem",
    "layer8_meta_governance",
    "layer9_preservation",
]


def _find_project_root() -> Path:
    """
    Best-effort detection of GUS v4 project root based on this file location.
    """
    here = Path(__file__).resolve()
    # scripts/verify_environment.py → project root = parent of scripts
    root = here.parents[1]
    return root


def check_os_info() -> EnvCheckResult:
    info = {
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "python": sys.version.split()[0],
    }
    # v0.1: Always OK; we just record metadata.
    return EnvCheckResult(
        check_id="ENV-001",
        name="OS & Python info",
        severity=Severity.INFO,
        ok=True,
        details=info,
    )


def check_venv_active() -> EnvCheckResult:
    in_venv = getattr(sys, "base_prefix", sys.prefix) != sys.prefix
    details = {
        "sys_prefix": sys.prefix,
        "base_prefix": getattr(sys, "base_prefix", None),
        "in_venv": in_venv,
    }

    if in_venv:
        return EnvCheckResult(
            check_id="ENV-002",
            name="Python virtual environment active",
            severity=Severity.INFO,
            ok=True,
            details=details,
        )
    else:
        # Not critical for basic dev, but we flag a WARN for Guardian discipline.
        return EnvCheckResult(
            check_id="ENV-002",
            name="Python virtual environment active",
            severity=Severity.WARN,
            ok=False,
            details=details,
        )


def check_project_root_structure(root: Path) -> EnvCheckResult:
    missing: List[str] = []
    present: List[str] = []

    for marker in PROJECT_ROOT_MARKERS:
        p = root / marker
        if p.exists():
            present.append(marker)
        else:
            missing.append(marker)

    ok = len(missing) == 0
    severity = Severity.INFO if ok else Severity.CRITICAL

    return EnvCheckResult(
        check_id="ENV-003",
        name="GUS v4 project structure baseline",
        severity=severity,
        ok=ok,
        details={
            "root": str(root),
            "present": present,
            "missing": missing,
        },
    )


def check_logs_structure(root: Path) -> EnvCheckResult:
    logs_root = root / "logs"
    paths = {
        "logs_root": logs_root.exists(),
        "logs_integrity": (logs_root / "integrity").exists(),
        "logs_governance": (logs_root / "governance").exists(),
        "logs_execution": (logs_root / "execution").exists(),
    }

    ok = all(paths.values())
    severity = Severity.INFO if ok else Severity.WARN

    return EnvCheckResult(
        check_id="ENV-004",
        name="Logs directory structure",
        severity=severity,
        ok=ok,
        details=paths,
    )


def check_git_repo(root: Path) -> EnvCheckResult:
    git_dir = root / ".git"
    ok = git_dir.exists()
    severity = Severity.INFO if ok else Severity.WARN

    return EnvCheckResult(
        check_id="ENV-005",
        name="Git repository presence",
        severity=severity,
        ok=ok,
        details={"git_dir": str(git_dir), "exists": ok},
    )


def check_backup_configuration(root: Path) -> EnvCheckResult:
    """
    v0.1 placeholder:
        - If env var GUS_BACKUP_PATH is set, we check the path exists.
        - Otherwise we WARN but do not fail.

    This allows you to wire in your encrypted backup volume later
    without hardcoding paths in the repo.
    """
    backup_path_env = os.environ.get("GUS_BACKUP_PATH")
    if not backup_path_env:
        return EnvCheckResult(
            check_id="ENV-006",
            name="Backup configuration (GUS_BACKUP_PATH)",
            severity=Severity.WARN,
            ok=False,
            details={
                "configured": False,
                "message": (
                    "Environment variable GUS_BACKUP_PATH not set. "
                    "Set this to your encrypted backup root to enable automated checks."
                ),
            },
        )

    backup_path = Path(backup_path_env)
    exists = backup_path.exists()

    severity = Severity.INFO if exists else Severity.WARN
    ok = exists

    return EnvCheckResult(
        check_id="ENV-006",
        name="Backup configuration (GUS_BACKUP_PATH)",
        severity=severity,
        ok=ok,
        details={
            "configured": True,
            "backup_path": str(backup_path),
            "exists": exists,
        },
    )


def run_checks() -> List[EnvCheckResult]:
    """
    Run all environment checks and return structured results.
    Non-destructive and safe to run on any dev machine.
    """
    root = _find_project_root()

    checks: List[EnvCheckResult] = []
    checks.append(check_os_info())
    checks.append(check_venv_active())
    checks.append(check_project_root_structure(root))
    checks.append(check_logs_structure(root))
    checks.append(check_git_repo(root))
    checks.append(check_backup_configuration(root))

    return checks


def _overall_status(results: List[EnvCheckResult]) -> str:
    """
    Derive a simple HUD-level status: OK / WARN / ALERT.
    """
    if any((not r.ok) and r.severity == Severity.CRITICAL for r in results):
        return "ALERT"
    if any((not r.ok) and r.severity == Severity.WARN for r in results):
        return "WARN"
    return "OK"


def _format_status_line(r: EnvCheckResult) -> str:
    status_str = "OK" if r.ok else "FAIL"
    return f"{r.check_id:7} {status_str:5} {r.severity.value:8} {r.name}"


def main() -> None:
    results = run_checks()

    print("🛡  GUS v4 – Environment Verification v0.1\n")
    for r in results:
        print(_format_status_line(r))

    overall = _overall_status(results)
    print(f"\nOverall environment status: {overall}")


if __name__ == "__main__":
    main()
