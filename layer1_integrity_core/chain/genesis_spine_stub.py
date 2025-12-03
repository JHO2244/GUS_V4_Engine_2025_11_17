"""
GUS v4 – L0→L1→L2 hash spine (stub module)

This module computes a minimal "genesis spine" hash chain that commits to the
anchor manifests of Layers 0, 1 and 2.

Design:
- Each layer contributes a canonical manifest payload (JSON → dict).
- We compute a manifest_hash = sha256(canonical_json(payload)).
- We then chain these per-layer hashes together so that each chain_hash
  depends on its own manifest_hash and the parent chain_hash.

The final L2 chain_hash is used as the global genesis_hash embedded into
PAS seals and other lineage-critical artifacts.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, TypedDict

from utils.hash_tools_stub import hash_payload


class LayerSpineEntry(TypedDict):
    layer_id: str
    """Canonical layer identifier, e.g. 'L0', 'L1', 'L2'."""

    manifest_path: str
    """Relative path to the JSON manifest used as input."""

    manifest_hash: str
    """SHA-256 of the canonical JSON representation of the manifest."""

    parent_hash: Optional[str]
    """Previous chain_hash in the spine (None for L0 root)."""

    chain_hash: str
    """Hash that binds this layer into the spine."""


# <root>/layer1_integrity_core/chain/genesis_spine_stub.py
PROJECT_ROOT = Path(__file__).resolve().parents[2]

LAYER_MANIFESTS: Dict[str, Path] = {
    "L0": PROJECT_ROOT / "layer0_uam_v4" / "L0_uam_lock_manifest.json",
    "L1": PROJECT_ROOT / "layer1_integrity_core" / "L1_manifest_baseline.json",
    "L2": PROJECT_ROOT / "layer2_governance_matrix" / "L2_lock_manifest.json",
}


def _load_manifest(layer_id: str) -> Dict:
    import json  # local import to keep module import light

    try:
        manifest_path = LAYER_MANIFESTS[layer_id]
    except KeyError as exc:
        raise KeyError(f"Unknown layer_id for spine: {layer_id!r}") from exc

    if not manifest_path.is_file():
        raise FileNotFoundError(
            f"Expected manifest for {layer_id} at {manifest_path} but it does not exist"
        )

    with manifest_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _compute_manifest_hash(payload: Dict) -> str:
    """
    Compute a canonical SHA-256 hash for a manifest payload using the same
    semantics as PAS seals (utils.hash_tools_stub.hash_payload).
    """
    return hash_payload(payload)


def _compute_chain_hash(
    layer_id: str,
    manifest_hash: str,
    parent_hash: Optional[str],
) -> str:
    """
    Compute the chain_hash for a single layer entry.

    We deliberately use a small, explicit payload to avoid accidental
    inclusion of non-deterministic fields (timestamps, etc.).
    """
    payload = {
        "layer_id": layer_id,
        "manifest_hash": manifest_hash,
        "parent_hash": parent_hash,
    }
    return hash_payload(payload)


def compute_l0_l1_l2_spine() -> List[LayerSpineEntry]:
    """
    Build the ordered L0→L1→L2 spine.

    Returns a list of LayerSpineEntry dicts. The final entry's chain_hash
    is the canonical genesis_hash for the current repo state.
    """
    spine: List[LayerSpineEntry] = []
    parent_hash: Optional[str] = None

    for layer_id in ("L0", "L1", "L2"):
        manifest_payload = _load_manifest(layer_id)
        manifest_hash = _compute_manifest_hash(manifest_payload)
        chain_hash = _compute_chain_hash(layer_id, manifest_hash, parent_hash)

        entry: LayerSpineEntry = {
            "layer_id": layer_id,
            "manifest_path": str(LAYER_MANIFESTS[layer_id].relative_to(PROJECT_ROOT)),
            "manifest_hash": manifest_hash,
            "parent_hash": parent_hash,
            "chain_hash": chain_hash,
        }
        spine.append(entry)
        parent_hash = chain_hash

    return spine


def get_genesis_hash() -> str:
    """
    Return the canonical genesis hash derived from the current L0→L2 spine.

    This is simply the chain_hash of the final L2 spine entry.
    """
    spine = compute_l0_l1_l2_spine()
    if not spine:
        raise RuntimeError("Genesis spine is empty; expected at least L0, L1, L2")
    return spine[-1]["chain_hash"]


if __name__ == "__main__":
    # Small debug / inspection helper:
    import json

    spine = compute_l0_l1_l2_spine()
    payload = {
        "scheme": "GUS_v4_L0_L1_L2_spine_v1",
        "layers": spine,
        "genesis_hash": spine[-1]["chain_hash"] if spine else None,
    }
    print(json.dumps(payload, indent=2))
