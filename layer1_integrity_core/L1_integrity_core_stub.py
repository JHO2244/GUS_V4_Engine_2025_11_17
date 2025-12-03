from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any, Tuple
import hashlib
import json

L1_MANIFEST_PATH = Path("layer1_integrity_core/L1_manifest_baseline.json")

@dataclass
class IntegrityIssue:
    path: str
    reason: str

def _load_manifest() -> Dict[str, Any]:
    if not L1_MANIFEST_PATH.exists():
        return {"files": []}
    with L1_MANIFEST_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)

def _hash_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def verify_integrity() -> Tuple[bool, List[IntegrityIssue]]:
    """
    Returns:
        ok: True only if manifest is non-empty AND all files match hashes.
        issues: list of IntegrityIssue describing any problems.
    """
    manifest = _load_manifest()
    files = manifest.get("files", [])
    issues: List[IntegrityIssue] = []

    if not files:
        issues.append(IntegrityIssue(
            path="*",
            reason="Layer 1 integrity manifest has no files registered"
        ))
        return False, issues

    for entry in files:
        p = Path(entry["path"])
        expected = entry["sha256"]

        if not p.exists():
            issues.append(IntegrityIssue(
                path=str(p),
                reason="missing"
            ))
            continue

        actual = _hash_file(p)
        if actual != expected:
            issues.append(IntegrityIssue(
                path=str(p),
                reason=f"hash mismatch (expected={expected}, actual={actual})"
            ))

    ok = not issues
    return ok, issues
