from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Tuple

from utils import load_json_config, get_guardian_logger
from .chain import gus_chain_v4_stub


logger = get_guardian_logger("GUSv4.Layer1")

INTEGRITY_CONFIG_FILENAME = "L1_integrity_config.json"


def _get_integrity_config_path() -> Path:
    return Path(__file__).resolve().with_name(INTEGRITY_CONFIG_FILENAME)


def load_integrity_status() -> Dict[str, Any]:
    """
    Load integrity configuration and basic chain status.
    This is read-only and does not mutate the chain.
    """
    errors = []
    config_loaded = False
    chain_module_imported = False
    chain_log_path: Path | None = None
    chain_module_path = "layer1_integrity_core.chain.gus_chain_v4_stub"

    # 1) Load config
    try:
        cfg_path = _get_integrity_config_path()
        cfg: Dict[str, Any] = load_json_config(cfg_path)
        config_loaded = True
    except Exception as exc:
        cfg = {}
        errors.append(f"config_error: {exc!r}")

    # 2) Resolve chain log path (from config or default)
    try:
        chain_log_str = cfg.get("chain_log_path") if config_loaded else None
        if chain_log_str:
            chain_log_path = Path(chain_log_str).resolve()
        else:
            chain_log_path = gus_chain_v4_stub.get_default_chain_log_path()
    except Exception as exc:
        errors.append(f"chain_log_path_error: {exc!r}")

    # 3) Chain module import status (already imported as gus_chain_v4_stub)
    try:
        _ = gus_chain_v4_stub
        chain_module_imported = True
    except Exception as exc:
        errors.append(f"chain_import_error: {exc!r}")

    status: Dict[str, Any] = {
        "config_loaded": config_loaded,
        "chain_module_imported": chain_module_imported,
        "chain_module_path": chain_module_path,
        "chain_log_path": chain_log_path,
        "chain_log_path_exists": bool(chain_log_path and chain_log_path.exists()),
        "errors": errors,
    }

    if errors:
        logger.warning(
            "Integrity Layer status loaded with warnings: %s",
            errors,
        )
    else:
        logger.info(
            "Integrity Layer status loaded successfully (config + chain)."
        )

    return status


def _verify_chain_from_status(status: Dict[str, Any]) -> Tuple[bool, list[str]]:
    """
    Internal helper: run hash-chain verification based on a status dict.
    """
    errors: list[str] = list(status.get("errors") or [])
    chain_log_path = status.get("chain_log_path")

    if chain_log_path is None:
        errors.append("missing_chain_log_path")
        return False, errors

    ok, chain_errors = gus_chain_v4_stub.verify_chain(chain_log_path)
    errors.extend(chain_errors)
    return ok, errors


def verify_integrity() -> bool:
    """
    High-level integrity check for Layer 1.
    Uses the hash chain to verify continuity and hash correctness.

    Returns:
        True if integrity passes (or chain is empty in skeleton mode),
        False otherwise.
    """
    status = load_integrity_status()
    ok, errors = _verify_chain_from_status(status)

    if ok:
        logger.info(
            "Integrity verification: OK (hash spine continuous; errors=%s).",
            errors,
        )
        return True

    logger.error("Integrity verification FAILED: %s", errors)
    return False
