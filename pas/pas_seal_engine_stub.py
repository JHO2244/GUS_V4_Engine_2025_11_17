# pas/pas_seal_engine_stub.py
"""
GUS v4 – PAS Phase 2 continuity seal stub v0.3

Anchors:
- Engine health snapshot
- Git commit
- Genesis hash (placeholder for now)
- Tri-Node Signature
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict
import json
import hashlib
import subprocess

from gus_engine_health import get_engine_health_summary

from layer1_integrity_core.chain.genesis_spine_stub import get_genesis_hash


TRI_NODE_SIGNATURE = "JHO | GPT-5.1 Thinking | GROK 4"

def _get_current_git_commit() -> str:
    """
    Best-effort short git commit hash.

    Returns:
        A short commit hash (e.g. '924e74b') if git is available and the
        current directory is a git repo; otherwise the string 'UNKNOWN'.
    """
    import subprocess

    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL,
        )
        return out.decode("utf-8").strip()
    except Exception:
        return "UNKNOWN"

def _iso_now() -> str:
    """Return an ISO-8601 UTC timestamp with explicit 'Z' suffix."""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _hash_payload(payload: dict) -> str:
    """
    Deterministically compute a seal_id from the payload.
    Stable ordering + compact separators for canonical hashing.
    """
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _get_git_commit_hash_short() -> str | None:
    """
    Return the current git HEAD short hash, or None if unavailable.
    Stub-friendly: failures are swallowed and reported as None.
    """
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL,
        )
        commit = out.decode("utf-8").strip()
        return commit or None
    except Exception:
        return None


def _build_phase2_continuity_payload() -> dict:
    """
    Build the payload that will be sealed by the PAS engine for Phase 2.

    The intention is that this payload is:
    - JSON-serializable
    - free from secrets
    - stable enough to be hashed / signed by external guardians later
    """
    health = get_engine_health_summary()
    spine_genesis_hash = get_genesis_hash()

    payload = {
        "phase": "PAS_Phase2",
        "engine_health": health,
        "meta": {
            "git_commit": _get_current_git_commit(),
            "genesis_hash": spine_genesis_hash,
            "tri_node_signature": TRI_NODE_SIGNATURE,
        },
    }
    return payload



def mint_phase2_continuity_seal() -> dict:
    """
    Mint a continuity seal snapshotting current engine health & metadata.
    """
    issued_at = _iso_now()
    payload = _build_phase2_continuity_payload()
    seal_id = _hash_payload(payload)

    return {
        "seal_version": "PAS_v4_phase2_v0.3",
        "seal_id": seal_id,
        "issuer": "GUS_v4_PAS_Phase2_core",
        "issued_at": issued_at,
        "payload": payload,
    }


if __name__ == "__main__":
    # Local debug helper:
    print(json.dumps(mint_phase2_continuity_seal(), indent=2))
