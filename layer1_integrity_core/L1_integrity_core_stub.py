# NOTE: Any change to files listed in L1_manifest_baseline.json
# MUST be followed by a deliberate manifest rebaseline (see PAS docs).

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any, Tuple
import hashlib
import json

# Location of the Layer-1 manifest. PAS Phase 3 populates this file.
L1_MANIFEST_PATH: Path = Path("layer1_integrity_core/L1_manifest_baseline.json")
L1_STATUS_PATH: Path = Path("logs/integrity/L1_integrity_status.json")


@dataclass
class IntegrityIssue:
    path: str
    reason: str


@dataclass
class FileIntegrityResult:
    path: str
    expected_hash: str | None
    actual_hash: str | None
    ok: bool
    reason: str | None = None


@dataclass
class IntegrityStatus:
    overall_ok: bool
    files: List[FileIntegrityResult]


@dataclass
class IntegritySummary:
    files_checked: int
    files_ok: int
    files_failed: int
    note: str = ""


def _load_manifest() -> Dict[str, Any]:
    if not L1_MANIFEST_PATH.exists():
        # Empty manifest is a valid state but forces overall_ok = False.
        return {
            "version": "L1_manifest_v0.0",
            "note": "no manifest present on disk",
            "files": [],
        }
    try:
        return json.loads(L1_MANIFEST_PATH.read_text(encoding="utf-8"))
    except Exception as exc:  # pragma: no cover - extremely unlikely
        return {
            "version": "L1_manifest_v0.0",
            "note": f"failed to read manifest: {exc}",
            "files": [],
        }


def _hash_file(path: Path) -> str:
    """
    Platform-stable hashing:
    - If the file is tracked and not dirty, hash the committed blob bytes (git show HEAD:<path>).
      This avoids CRLF/LF checkout differences across OS/CI.
    - If the file is dirty/untracked, hash the working-tree bytes (tamper visibility locally).
    """
    import subprocess

    rel = path.as_posix()

    # If untracked, hash working tree
    rc = subprocess.run(["git", "ls-files", "--error-unmatch", rel],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode
    if rc != 0:
        h = hashlib.sha256()
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()

    # If tracked but dirty, hash working tree
    out = subprocess.check_output(["git", "status", "--porcelain", "--", rel], text=True).strip()
    if out:
        h = hashlib.sha256()
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()

    # Tracked + clean => hash committed blob bytes
    blob = subprocess.check_output(["git", "show", f"HEAD:{rel}"])
    h = hashlib.sha256()
    h.update(blob)
    return h.hexdigest()


def verify_integrity() -> Tuple[bool, List[IntegrityIssue]]:
    """
    Core verification primitive used by higher-level health checks.

    Returns:
        (ok, issues)
        ok      – True if all required files match the manifest hashes.
        issues  – List of IntegrityIssue entries describing any problems.
    """
    manifest = _load_manifest()
    files = manifest.get("files", [])

    if not files:
        # No files registered yet – this is an explicit red flag at this stage.
        return False, [
            IntegrityIssue(
                path=str(L1_MANIFEST_PATH),
                reason="Layer 1 integrity manifest has no files registered",
            )
        ]

    issues: List[IntegrityIssue] = []

    for entry in files:
        path_str = entry.get("path")
        expected = entry.get("sha256")
        if not path_str or not expected:
            issues.append(
                IntegrityIssue(
                    path=str(path_str),
                    reason="manifest entry missing path or sha256",
                )
            )
            continue

        p = Path(path_str)
        if not p.exists():
            issues.append(
                IntegrityIssue(
                    path=str(p),
                    reason="missing",
                )
            )
            continue

        actual = _hash_file(p)
        if actual != expected:
            issues.append(
                IntegrityIssue(
                    path=str(p),
                    reason=f"hash mismatch (expected={expected}, actual={actual})",
                )
            )

    ok = not issues
    return ok, issues


def run_integrity_check() -> IntegrityStatus:
    """
    Higher-level helper that expands verify_integrity() into a structured object.
    """
    manifest = _load_manifest()
    files = manifest.get("files", [])

    ok, issues = verify_integrity()
    issues_by_path = {iss.path: iss for iss in issues}

    results: List[FileIntegrityResult] = []
    for entry in files:
        path_str = entry.get("path")
        expected = entry.get("sha256")
        p = Path(path_str)
        issue = issues_by_path.get(str(p)) or issues_by_path.get(path_str)

        if issue is None:
            # File exists and hash matched.
            actual = _hash_file(p) if p.exists() else None
            results.append(
                FileIntegrityResult(
                    path=str(p),
                    expected_hash=expected,
                    actual_hash=actual,
                    ok=True,
                    reason=None,
                )
            )
        else:
            # Something went wrong for this file.
            actual = _hash_file(p) if p.exists() else None
            results.append(
                FileIntegrityResult(
                    path=str(p),
                    expected_hash=expected,
                    actual_hash=actual,
                    ok=False,
                    reason=issue.reason,
                )
            )

    return IntegrityStatus(overall_ok=ok, files=results)


def summarize_integrity_status(status: IntegrityStatus) -> IntegritySummary:
    files_checked = len(status.files)
    files_ok = sum(1 for f in status.files if f.ok)
    files_failed = files_checked - files_ok
    note = "manifest empty – integrity not yet established" if files_checked == 0 else ""
    return IntegritySummary(
        files_checked=files_checked,
        files_ok=files_ok,
        files_failed=files_failed,
        note=note,
    )


def load_integrity_status() -> IntegrityStatus:
    """
    Load the last persisted status if available, otherwise run a fresh check.

    For now this is a thin convenience wrapper; PAS can later evolve this
    into a richer time-series log.
    """
    if L1_STATUS_PATH.exists():
        try:
            raw = json.loads(L1_STATUS_PATH.read_text(encoding="utf-8"))
            files: List[FileIntegrityResult] = []
            for f in raw.get("files", []):
                files.append(
                    FileIntegrityResult(
                        path=f.get("path", ""),
                        expected_hash=f.get("expected_hash"),
                        actual_hash=f.get("actual_hash"),
                        ok=bool(f.get("ok")),
                        reason=f.get("reason"),
                    )
                )
            return IntegrityStatus(
                overall_ok=bool(raw.get("overall_ok")),
                files=files,
            )
        except Exception:
            # Fall back to a fresh run if the log is malformed.
            pass  # pragma: no cover

    status = run_integrity_check()
    # Persist a simple snapshot for inspection / later PAS use.
    L1_STATUS_PATH.parent.mkdir(parents=True, exist_ok=True)
    L1_STATUS_PATH.write_text(
        json.dumps(
            {
                "overall_ok": status.overall_ok,
                "files": [
                    {
                        "path": f.path,
                        "expected_hash": f.expected_hash,
                        "actual_hash": f.actual_hash,
                        "ok": f.ok,
                        "reason": f.reason,
                    }
                    for f in status.files
                ],
            },
            indent=2,
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    return status
