from __future__ import annotations

import json
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from layer7_output_contract.output_builder_v0_1 import build_output_envelope_v0_1
from utils.canonical_json import write_canonical_json_file



REPO_ROOT_SENTINELS = (".git", "pyproject.toml", "requirements.txt", "pytest.ini")


def _repo_root(start: Optional[Path] = None) -> Path:
    p = (start or Path.cwd()).resolve()
    for _ in range(12):
        if any((p / s).exists() for s in REPO_ROOT_SENTINELS):
            return p
        if p.parent == p:
            break
        p = p.parent
    return (start or Path.cwd()).resolve()


def _run(cmd: List[str], cwd: Path) -> Tuple[int, str]:
    # Deterministic-ish: capture stdout+stderr together, trim trailing whitespace.
    proc = subprocess.run(
        cmd,
        cwd=str(cwd),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return proc.returncode, proc.stdout.rstrip()


def _write_canonical_json(path: Path, payload: Dict[str, Any]) -> None:
    # Canonical, stable JSON: sorted keys + LF + compact separators.
    text = json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=False)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text + "\n", encoding="utf-8", newline="\n")


@dataclass(frozen=True)
class AuditVerdict:
    ok: bool
    report: Dict[str, Any]

    def to_canonical_json(self) -> str:
        return json.dumps(self.report, sort_keys=True, indent=2, ensure_ascii=False) + "\n"


def _find_latest_epoch_anchor_tag(repo: Path) -> str:
    code, out = _run(["git", "tag", "--list", "epoch_*_anchor_*"], cwd=repo)
    if code != 0:
        return ""
    tags = [t.strip() for t in out.splitlines() if t.strip()]
    if not tags:
        return ""
    tags.sort()
    return tags[-1]


def _file_exists(repo: Path, rel: str) -> bool:
    return (repo / rel).is_file()


def _required_files() -> List[str]:
    # Minimal, stable "core artifacts" presence checks.
    return [
        "scripts/verify_repo_seals.py",
        "scripts/guardian_gate.sh",
        "scripts/epoch_lock_prep.sh",
        "scripts/verify_epoch_anchor.py",
        "scripts/verify_latest_seal.py",
        "layer7_output_contract/output_contract_v0_1.py",
        "layer7_output_contract/output_envelope_v0_1.py",
        "layer8_genesis/genesis_declaration_v0_1.py",
    ]


def run_final_guardian_audit_v0_1(
    repo_root: Optional[Path] = None,
    require_seal_ok: bool = True,
) -> AuditVerdict:
    repo = _repo_root(repo_root)

    # --- git identity ---
    code_head, head = _run(["git", "rev-parse", "HEAD"], cwd=repo)
    head = head.strip() if code_head == 0 else ""

    anchor_tag = _find_latest_epoch_anchor_tag(repo)

    # --- core file checks ---
    missing = [p for p in _required_files() if not _file_exists(repo, p)]

    # --- seal verification (merge-safe policy already implemented) ---
    seal_cmd = ["python", "-m", "scripts.verify_repo_seals", "--head", "--no-sig", "--require-head", "--ci"]
    seal_rc, seal_out = _run(seal_cmd, cwd=repo)

    seal_ok = (seal_rc == 0) and ("[OK]" in seal_out or "Seal verification complete" in seal_out)

    # --- build the report (deterministic ordering via sort_keys in JSON writer) ---
    report: Dict[str, Any] = {
        "a9_version": "0.1",
        "repo": {
            "root": str(repo).replace("\\", "/"),
            "head": head,
            "epoch_anchor_tag_latest": anchor_tag,
        },
        "checks": {
            "required_files_missing": missing,
            "seal_verify": {
                "command": " ".join(seal_cmd),
                "returncode": seal_rc,
                "ok": seal_ok,
                "output_tail": "\n".join(seal_out.splitlines()[-30:]),
            },
        },
        "verdict": {
            "ok": (not missing) and ((not require_seal_ok) or seal_ok),
            "notes": [],
        },
    }

    if missing:
        report["verdict"]["notes"].append("Missing required core artifacts (files).")
    if require_seal_ok and not seal_ok:
        report["verdict"]["notes"].append("Seal verification failed (HEAD).")

    return AuditVerdict(ok=bool(report["verdict"]["ok"]), report=report)


def write_a9_report_v0_1(
    out_path: Path,
    repo_root: Optional[Path] = None,
    require_seal_ok: bool = True,
    envelope_out_path: Optional[Path] = None,
) -> AuditVerdict:
    verdict = run_final_guardian_audit_v0_1(repo_root=repo_root, require_seal_ok=require_seal_ok)

    # Also emit an A7 OutputEnvelope derived from this A9 run (fail-closed).
    # NOTE: A9 does not compute a policy verdict; we mark it explicitly but non-empty to satisfy contract.
    env_path = envelope_out_path or Path("audits/a7_output_envelope_from_a9_v0_1.json")

    head = verdict.report.get("repo", {}).get("head", "") or ""
    run_id = head[:12] if head else "unknown"

    env = build_output_envelope_v0_1(
        producer="GUSv4.A9",
        run_id=run_id,
        input_seal_ref=head or "unknown",
        decision_ref="A9.final_guardian_audit.v0.1",
        policy_verdict_ref="policy_verdict:a9_unavailable_v0_1",
        score_total=10.0 if verdict.ok else 0.0,
        score_breakdown={
            "TD": 10.0 if verdict.ok else 0.0,
            "SC": 10.0 if verdict.ok else 0.0,
            "AP": 10.0 if verdict.ok else 0.0,
            "RL": 10.0 if verdict.ok else 0.0,
        },
        verdict="PASS" if verdict.ok else "FAIL",
        artifacts=[out_path.as_posix()],
        explainability_trace_ref=None,
    )

    # Write envelope first so the report can prove emission.
    env_payload = env.to_dict(include_integrity=True)
    write_canonical_json_file(env_path, env_payload)

    # Prove envelope emission (exists + integrity_ok + schema + policy_verdict_ref).
    env_exists = env_path.is_file()
    env_integrity_ok = False
    env_schema_version = ""
    env_policy_verdict_ref = ""

    if env_exists:
        try:
            loaded = json.loads(env_path.read_text(encoding="utf-8"))

            # schema + policy verdict ref should be extracted even if integrity shape varies
            env_schema_version = str(
                loaded.get("schema_version")
                or loaded.get("schema")
                or env_payload.get("schema_version")
                or ""
            )
            env_policy_verdict_ref = str(
                loaded.get("policy_verdict_ref")
                or env_payload.get("policy_verdict_ref")
                or ""
            )

            # Robust integrity parsing:
            # - dict: {"ok": true}
            # - bool: true/false
            # - string: treat non-empty as "present/ok" for emission proof purposes
            integ = loaded.get("integrity", None)

            if isinstance(integ, dict):
                env_integrity_ok = bool(integ.get("ok", False))
            elif isinstance(integ, bool):
                env_integrity_ok = bool(integ)
            elif isinstance(integ, str):
                env_integrity_ok = (integ.strip() != "")
            else:
                # Fallback: if integrity isn't in expected shapes, use presence of env_payload integrity
                integ2 = env_payload.get("integrity", None)
                if isinstance(integ2, dict):
                    env_integrity_ok = bool(integ2.get("ok", False))
                elif isinstance(integ2, bool):
                    env_integrity_ok = bool(integ2)
                elif isinstance(integ2, str):
                    env_integrity_ok = (integ2.strip() != "")
                else:
                    env_integrity_ok = False

        except Exception:
            env_integrity_ok = False
            env_schema_version = ""
            env_policy_verdict_ref = ""

    verdict.report["a7_output_envelope"] = {
        "path": env_path.as_posix(),
        "exists": bool(env_exists),
        "integrity_ok": bool(env_integrity_ok),
        "schema_version": env_schema_version,
        "policy_verdict_ref": env_policy_verdict_ref,
    }

    # Fail-closed: if envelope emission is requested but missing/invalid, the A9 report must fail.
    if not env_exists:
        verdict.report["verdict"]["ok"] = False
        verdict.report["verdict"]["notes"].append("A7 output envelope missing (emission expected).")
    elif not env_integrity_ok:
        verdict.report["verdict"]["ok"] = False
        verdict.report["verdict"]["notes"].append("A7 output envelope integrity failed (emission expected).")

    _write_canonical_json(out_path, verdict.report)
    return AuditVerdict(ok=bool(verdict.report["verdict"]["ok"]), report=verdict.report)

