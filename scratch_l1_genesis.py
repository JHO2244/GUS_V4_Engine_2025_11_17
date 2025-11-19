"""
scratch_l1_genesis.py
One-off helper to write the first real Guardian GENESIS event into the L1 chain.
"""

from __future__ import annotations

from pathlib import Path

from layer1_integrity_core.chain.gus_chain_v4_stub import append_chain_event, CHAIN_LOG_PATH
from utils import get_guardian_logger

logger = get_guardian_logger("GUSv4.Genesis")


if __name__ == "__main__":
    payload = {
        "manifest_version": "v4.0",
        "layers_online": [0, 1, 2, 3, 4],
        "description": "GUS v4 skeleton (Layers 0–4) verified online; genesis chain event.",
    }

    entry = append_chain_event(
        event_type="GENESIS_CORE_ONLINE",
        payload=payload,
        note="First Guardian genesis event for GUS v4 L1 chain.",
        layer=1,
    )

    logger.info("Genesis chain entry written to %s", str(CHAIN_LOG_PATH))

    print("Genesis chain entry:")
    from pprint import pprint
    pprint(entry)
