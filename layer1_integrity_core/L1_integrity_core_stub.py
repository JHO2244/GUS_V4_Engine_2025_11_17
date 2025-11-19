# Placeholder for integrity checks
"""
GUS v4 – Layer 1 Integrity Core stub.

Responsibility (skeleton mode):
- Load integrity configuration (JSON).
- Verify that the hash spine module + log path are present.
- Provide a simple IntegrityStatus snapshot to higher layers.

No real hash-chain logic is implemented here yet.
"""

from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from pathlib import Path
from typing import List, Optional

from utils import load_json_config, get_guardian_logger

BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "L1_integrity_config.json"

logger = get_guardian_logger("GUSv4.Layer1")


@dataclass
class IntegrityStatus:
    """
    Minimal status snapshot for Layer 1 – Integrity Core.
    """
    config_loaded: bool
    chain_module_path: Optional[str]
    chain_log_path: Optional[Path]
    chain_module_imported: bool
    chain_log_path_exists: bool
    errors: List[str]


def _load_config() -> Optional[dict]:
    """
    Internal helper: load the integrity config JSON.
    Returns None on failure.
    """
    return load_json_config(CONFIG_PATH)


def load_integrity_status() -> IntegrityStatus:
    """
    Load the integrity configuration and perform basic structural checks.

    Skeleton checks:
    - Can we read the config JSON?
    - Does the declared chain module import?
    - Does the declared chain log path exist?

    We only log and return a status object; no exceptions are raised.
    """
    errors: List[str] = []

    config = _load_config()
    if config is None:
        errors.append("Failed to load L1_integrity_config.json.")
        # safe defaults
        chain_module_path: Optional[str] = None
        chain_log_path: Optional[Path] = None
        config_loaded = False
        chain_module_imported = False
        chain_log_exists = False
    else:
        config_loaded = True

        chain_module_path = config.get(
            "chain_module", "layer1_integrity_core.chain.gus_chain_v4_stub"
        )
        raw_log_path = config.get(
            "chain_log_file", "layer1_integrity_core/chain/gus_chain_log_placeholder.txt"
        )
        chain_log_path = (BASE_DIR.parent / raw_log_path).resolve()

        # Try to import the chain module
        try:
            import_module(chain_module_path)
            chain_module_imported = True
        except Exception as exc:  # noqa: BLE001
            chain_module_imported = False
            errors.append(f"Failed to import chain module '{chain_module_path}': {exc!r}")

        # Check log path existence (non-fatal)
        chain_log_exists = chain_log_path.exists()
        if not chain_log_exists:
            errors.append(f"Chain log file does not exist at '{chain_log_path}'.")

    if errors:
        logger.warning("Integrity Layer status loaded with issues: %s", "; ".join(errors))
    else:
        logger.info("Integrity Layer status loaded successfully (config + chain).")

    return IntegrityStatus(
        config_loaded=config_loaded,
        chain_module_path=chain_module_path,
        chain_log_path=chain_log_path,
        chain_module_imported=chain_module_imported,
        chain_log_path_exists=chain_log_exists,
        errors=errors,
    )


def verify_integrity() -> bool:
    """
    High-level check used by higher layers.

    Returns:
        True  -> basic integrity structure looks OK
        False -> configuration/module/log problems detected
    """
    status = load_integrity_status()
    ok = (
        status.config_loaded
        and status.chain_module_imported
        and status.chain_log_path_exists
    )

    if ok:
        logger.info("Integrity verification: OK (skeleton mode).")
    else:
        logger.warning("Integrity verification: FAILED (skeleton mode).")

    return ok
