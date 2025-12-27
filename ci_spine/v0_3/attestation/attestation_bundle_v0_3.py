from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict


@dataclass(frozen=True)
class AttestationBundleV03:
    """
    A minimal, deterministic, portable output bundle for verification results.

    Guardian rules:
    - Must be deterministic for the same inputs.
    - Must be safe to export (no secrets).
    - Must be descriptive, not authoritative beyond what it records.
    """
    schema_version: str = "ci_spine_attestation_v0_3"

    def write_json(self, out_path: Path, payload: Dict[str, Any]) -> None:
        safe_payload = dict(payload)
        safe_payload["schema_version"] = self.schema_version
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(safe_payload, indent=2, sort_keys=True), encoding="utf-8")
