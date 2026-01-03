from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
import json
import subprocess


def _utc_now_iso() -> str:
    # ISO-8601 with Z, deterministic format
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _run_git(args: List[str]) -> str:
    out = subprocess.check_output(["git", *args], text=True).strip()
    return out


def _detect_repo_root() -> str:
    # CI-safe, local-safe
    return _run_git(["rev-parse", "--show-toplevel"])


def _head_sha() -> str:
    return _run_git(["rev-parse", "HEAD"])


def _latest_epoch_anchor_tag() -> Optional[str]:
    tags = _run_git(["tag", "--list", "epoch_*_anchor_*"])
    if not tags:
        return None
    tag_list = [t.strip() for t in tags.splitlines() if t.strip()]
    if not tag_list:
        return None
    # sort lexicographically; your tags are timestamped, so this works.
    return sorted(tag_list)[-1]


def _anchor_sha(tag: str) -> str:
    return _run_git(["rev-list", "-n", "1", tag])


def _canonical_json(obj: Any) -> str:
    # canonical: sorted keys, stable separators, LF
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"


@dataclass(frozen=True)
class GenesisDeclarationV0_1:
    version: str = "v0.1"

    # Identity
    system_name: str = "GUS v4"
    repo_root: str = ""
    head_sha: str = ""
    epoch_anchor_tag: str = ""
    epoch_anchor_sha: str = ""

    # Policies (canonical statements)
    seal_policy: str = "seal-only HEAD verifies introduced ancestor seal (merge-safe)"
    signature_policy: str = "signatures optional by policy unless strict mode; verification supports no-sig"
    determinism_policy: str = "canonical JSON writer + LF normalization + deterministic traces"

    # Non-negotiables (short list; stable order)
    invariants: List[str] = field(default_factory=lambda: [
        "Integrity > convenience",
        "Deterministic artifacts (canonical JSON, stable ordering)",
        "Merge-safe seal verification (parents + head)",
        "CI gates enforce drift limits and epoch anchors",
        "Tests must pass before push (guardian gate)",
    ])

    created_utc: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "created_utc": self.created_utc,
            "determinism_policy": self.determinism_policy,
            "epoch_anchor_sha": self.epoch_anchor_sha,
            "epoch_anchor_tag": self.epoch_anchor_tag,
            "head_sha": self.head_sha,
            "invariants": list(self.invariants),
            "repo_root": self.repo_root,
            "seal_policy": self.seal_policy,
            "signature_policy": self.signature_policy,
            "system_name": self.system_name,
            "version": self.version,
        }

    def to_canonical_json(self) -> str:
        return _canonical_json(self.to_dict())


def build_genesis_declaration_v0_1(
    created_utc: Optional[str] = None,
    repo_root: Optional[str] = None,
    head_sha: Optional[str] = None,
    epoch_anchor_tag: Optional[str] = None,
) -> GenesisDeclarationV0_1:
    rr = repo_root or _detect_repo_root()
    hs = head_sha or _head_sha()

    tag = epoch_anchor_tag or _latest_epoch_anchor_tag()
    if not tag:
        raise RuntimeError("No epoch_*_anchor_* tag found. Create an epoch anchor before A8.")
    asha = _anchor_sha(tag)

    return GenesisDeclarationV0_1(
        repo_root=str(Path(rr).as_posix()),
        head_sha=hs,
        epoch_anchor_tag=tag,
        epoch_anchor_sha=asha,
        created_utc=created_utc or _utc_now_iso(),
    )


def write_genesis_declaration(
    out_path: Path,
    decl: GenesisDeclarationV0_1,
) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(decl.to_canonical_json(), encoding="utf-8", newline="\n")
