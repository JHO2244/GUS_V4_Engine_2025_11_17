"""
GUS v4.0 — L8 Execution Layer
Execution Packet (Sealed Export) v0.1

Purpose:
- Deterministically wrap an ExecutionRecord into a portable export packet.
- Packet includes a packet_hash that commits to record_hash + packet fields.

Guardian constraints:
- Deterministic ordering only.
- No non-deterministic timestamps (caller must supply if needed).
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Mapping, Dict

from .execution_record_v0_1 import ExecutionRecord
from .execution_export_v0_1 import export_execution_record
from .execution_runtime_v0_1 import _hash_str, _stable_json


def build_execution_packet_v0_1(
    record: ExecutionRecord,
    *,
    packet_version: str = "0.1",
) -> Dict[str, Any]:
    """
    Build a deterministic export packet for an ExecutionRecord.
    Returns a plain dict suitable for canonical JSON writing.

    packet_hash covers:
    - packet_version
    - record_hash
    - exported record fields (export_execution_record_v0_1 output)
    """
    exported = export_execution_record(record)

    # record_hash is embedded in ExecutionRecord, but we also pin it here explicitly
    record_hash = getattr(record, "record_hash", "")
    if not isinstance(record_hash, str) or not record_hash.strip():
        raise ValueError("ExecutionRecord must include non-empty record_hash")

    core = {
        "packet_version": packet_version,
        "record_hash": record_hash,
        "execution_record": exported,
    }

    packet_hash = _hash_str(_stable_json(core))

    # Final packet: hash included (hash commits to the pre-hash core)
    return {
        "packet_version": packet_version,
        "record_hash": record_hash,
        "packet_hash": packet_hash,
        "execution_record": exported,
    }
