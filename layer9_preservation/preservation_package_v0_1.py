from __future__ import annotations

import fnmatch
import hashlib
import json
import os
import pathlib
import zipfile
from dataclasses import dataclass
from typing import Iterable, List, Dict, Optional, Tuple


_CANON_SEPARATORS: Tuple[str, str] = (",", ":")
_CANON_ZIP_DT = (1980, 1, 1, 0, 0, 0)  # deterministic ZIP timestamp (min supported)


@dataclass(frozen=True)
class PreservationPackageResult:
    package_dir: str
    manifest_path: str
    seal_path: str
    zip_path: Optional[str]


def _sha256_bytes(data: bytes) -> str:
    h = hashlib.sha256()
    h.update(data)
    return h.hexdigest()


def _sha256_file(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _canon_json_bytes(obj: object) -> bytes:
    s = json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=_CANON_SEPARATORS)
    return s.encode("utf-8")


def _norm_relpath(root: pathlib.Path, p: pathlib.Path) -> str:
    rel = p.relative_to(root).as_posix()
    return rel


def _match_any(name: str, patterns: Iterable[str]) -> bool:
    for pat in patterns:
        if fnmatch.fnmatch(name, pat):
            return True
    return False


def _iter_files(root: pathlib.Path) -> List[pathlib.Path]:
    files: List[pathlib.Path] = []
    for dirpath, _, filenames in os.walk(root):
        for fn in filenames:
            files.append(pathlib.Path(dirpath) / fn)
    return files


def build_preservation_package(
    *,
    repo_root: str,
    out_dir: str,
    include_globs: Optional[List[str]] = None,
    exclude_globs: Optional[List[str]] = None,
    note: str = "",
    anchor: str = "",
    create_zip: bool = True,
) -> PreservationPackageResult:
    """
    Create a deterministic preservation package in out_dir.

    Output files:
      - preservation_manifest_v0_1.json   (canonical JSON)
      - preservation_seal_v0_1.sha256     (sha256(manifest_bytes))
      - preservation_package_v0_1.zip     (optional deterministic zip)

    include_globs/exclude_globs match *relative paths* (posix style).
    Defaults are conservative and repo-safe.
    """
    root = pathlib.Path(repo_root).resolve()
    outp = pathlib.Path(out_dir).resolve()
    outp.mkdir(parents=True, exist_ok=True)

    inc = include_globs[:] if include_globs else [
        "layer*/**/*.py",
        "tests/**/*.py",
        "scripts/**/*.py",
        "*.md",
        "*.txt",
        "*.json",
    ]
    exc = exclude_globs[:] if exclude_globs else [
        "**/__pycache__/**",
        "**/*.pyc",
        ".git/**",
        ".venv/**",
        "venv/**",
        ".pytest_cache/**",
        ".mypy_cache/**",
        ".idea/**",
        ".vscode/**",
        "dist/**",
        "build/**",
    ]

    all_files = _iter_files(root)
    selected: List[pathlib.Path] = []
    for p in all_files:
        rel = _norm_relpath(root, p)
        if _match_any(rel, exc):
            continue
        if _match_any(rel, inc):
            selected.append(p)

    # Deterministic order
    selected.sort(key=lambda x: _norm_relpath(root, x))

    file_entries: List[Dict[str, object]] = []
    for p in selected:
        rel = _norm_relpath(root, p)
        file_entries.append({
            "path": rel,
            "sha256": _sha256_file(p),
            "bytes": p.stat().st_size,
        })

    manifest_obj: Dict[str, object] = {
        "schema": "gus.layer9.preservation_manifest",
        "version": "v0.1",
        "anchor": anchor,
        "note": note,
        "root": root.name,
        "file_count": len(file_entries),
        "files": file_entries,
    }

    manifest_bytes = _canon_json_bytes(manifest_obj)
    manifest_hash = _sha256_bytes(manifest_bytes)

    manifest_path = outp / "preservation_manifest_v0_1.json"
    seal_path = outp / "preservation_seal_v0_1.sha256"
    zip_path = outp / "preservation_package_v0_1.zip" if create_zip else None

    # Write canonical manifest
    manifest_path.write_bytes(manifest_bytes)

    # Write seal (text) deterministically
    seal_path.write_text(manifest_hash + "\n", encoding="utf-8", newline="\n")

    # Optional deterministic zip
    if create_zip and zip_path is not None:
        if zip_path.exists():
            zip_path.unlink()

        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            # Always include manifest + seal first
            for special in [manifest_path, seal_path]:
                info = zipfile.ZipInfo(filename=special.name, date_time=_CANON_ZIP_DT)
                info.compress_type = zipfile.ZIP_DEFLATED
                zf.writestr(info, special.read_bytes())

            # Then include repo files with deterministic paths + timestamps
            for p in selected:
                rel = _norm_relpath(root, p)
                info = zipfile.ZipInfo(filename=rel, date_time=_CANON_ZIP_DT)
                info.compress_type = zipfile.ZIP_DEFLATED
                zf.writestr(info, p.read_bytes())

    return PreservationPackageResult(
        package_dir=str(outp),
        manifest_path=str(manifest_path),
        seal_path=str(seal_path),
        zip_path=str(zip_path) if zip_path else None,
    )


def verify_preservation_package(*, repo_root: str, package_dir: str) -> bool:
    """
    Verify:
      1) seal matches canonical manifest bytes
      2) each file listed in manifest exists under repo_root and matches sha256
    """
    root = pathlib.Path(repo_root).resolve()
    pkg = pathlib.Path(package_dir).resolve()

    manifest_path = pkg / "preservation_manifest_v0_1.json"
    seal_path = pkg / "preservation_seal_v0_1.sha256"

    if not manifest_path.exists() or not seal_path.exists():
        return False

    manifest_bytes = manifest_path.read_bytes()
    seal_expected = seal_path.read_text(encoding="utf-8").strip()

    if _sha256_bytes(manifest_bytes) != seal_expected:
        return False

    try:
        manifest = json.loads(manifest_bytes.decode("utf-8"))
    except Exception:
        return False

    files = manifest.get("files", [])
    if not isinstance(files, list):
        return False

    for entry in files:
        if not isinstance(entry, dict):
            return False
        rel = entry.get("path")
        expected = entry.get("sha256")
        if not isinstance(rel, str) or not isinstance(expected, str):
            return False
        p = root / pathlib.Path(rel)
        if not p.exists() or not p.is_file():
            return False
        if _sha256_file(p) != expected:
            return False

    return True
