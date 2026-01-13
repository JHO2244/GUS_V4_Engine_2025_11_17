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
"""

from __future__ import annotations

import os
import sys
import platform
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List


# ------------------------------------------------------------
# Severity Levels
# ------------------------------------------------------------
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


# ------------------------------------------------------------
# Project Structure Markers
# ------------------------------------------------------------
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
    """Detect GUS project root based on this file’s location."""
    here = Path(__file__).resolve()
    return here.parents[1]


# ------------------------------------------------------------
# Individual Checks
# ------------------------------------------------------------
def check_os_info() -> EnvCheckResult:
    info = {
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "python": sys.version.split()[0],
    }
    return EnvCheckResult("ENV-001", "OS & Python info", Severity.INFO, True, info)


def check_venv_active() -> EnvCheckResult:
    in_venv = sys.prefix != getattr(sys, "base_prefix", sys.prefix)
    severity = Severity.INFO if in_venv else Severity.WARN

    return EnvCheckResult(
        "ENV-002",
        "Python virtual environment active",
        severity,
        in_venv,
        {
            "sys_prefix": sys.prefix,
            "base_prefix": getattr(sys, "base_prefix", None),
            "in_venv": in_venv,
        },
    )


def check_project_root_structure(root: Path) -> EnvCheckResult:
    missing, present = [], []

    for marker in PROJECT_ROOT_MARKERS:
        if (root / marker).exists():
            present.append(marker)
        else:
            missing.append(marker)

    ok = len(missing) == 0
    severity = Severity.INFO if ok else Severity.CRITICAL

    return EnvCheckResult(
        "ENV-003",
        "GUS v4 project structure baseline",
        severity,
        ok,
        {"root": str(root), "present": present, "missing": missing},
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
        "ENV-004",
        "Logs directory structure",
        severity,
        ok,
        paths,
    )


def check_git_repo(root: Path) -> EnvCheckResult:
    git_dir = root / ".git"
    ok = git_dir.exists()
    severity = Severity.INFO if ok else Severity.WARN

    return EnvCheckResult(
        "ENV-005",
        "Git repository presence",
        severity,
        ok,
        {"git_dir": str(git_dir), "exists": ok},
    )


def check_backup_configuration(root: Path) -> EnvCheckResult:
    backup_env = os.environ.get("GUS_BACKUP_PATH")
    if not backup_env:
        return EnvCheckResult(
            "ENV-006",
            "Backup configuration (GUS_BACKUP_PATH)",
            Severity.WARN,
            False,
            {
                "configured": False,
                "message": "Environment variable GUS_BACKUP_PATH not set.",
            },
        )

    backup_path = Path(backup_env)
    exists = backup_path.exists()

    return EnvCheckResult(
        "ENV-006",
        "Backup configuration (GUS_BACKUP_PATH)",
        Severity.INFO if exists else Severity.WARN,
        exists,
        {"configured": True, "backup_path": str(backup_path), "exists": exists},
    )


# ------------------------------------------------------------
# Aggregate Runner
# ------------------------------------------------------------
def run_checks() -> List[EnvCheckResult]:
    root = _find_project_root()
    return [
        check_os_info(),
        check_venv_active(),
        check_project_root_structure(root),
        check_logs_structure(root),
        check_git_repo(root),
        check_backup_configuration(root),
    ]


def _overall_status(results: List[EnvCheckResult]) -> str:
    if any((not r.ok) and r.severity == Severity.CRITICAL for r in results):
        return "ALERT"
    if any((not r.ok) and r.severity == Severity.WARN for r in results):
        return "WARN"
    return "OK"


def print_results(results: List[EnvCheckResult]) -> None:
    print("🛡  GUS v4 – Environment Verification v0.1\n")
    for r in results:
        status = "OK" if r.ok else "FAIL"
        print(f"{r.check_id:7} {status:5} {r.severity.value:8} {r.name}")
    print(f"\nOverall environment status: {_overall_status(results)}")


# ------------------------------------------------------------
# Exit Code Mapping
# ------------------------------------------------------------
if __name__ == "__main__":
    results = run_checks()
    print_results(results)

    severities = [r.severity for r in results]
    worst = max(severities) if severities else Severity.INFO

    if worst is Severity.CRITICAL:
        sys.exit(2)
    elif worst is Severity.WARN:
        sys.exit(1)
    else:
        sys.exit(0)
