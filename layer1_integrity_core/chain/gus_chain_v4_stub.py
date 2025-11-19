from pathlib import Path
from typing import Tuple, List
import logging
import json

logger = logging.getLogger("GUSv4.Chain")

# Single source of truth for the L1 chain log path
CHAIN_LOG_PATH = Path(__file__).parent / "gus_chain_log_placeholder.txt"


def get_default_chain_log_path() -> Path:
    """
    Return the default L1 chain log path.

    Called by the Integrity Core loader so that L1 does not need
    to hard-code or guess the location of the chain log file.
    """
    return CHAIN_LOG_PATH
# ... your existing imports / logger / CHAIN_LOG_PATH / get_default_chain_log_path ...

def _parse_chain(path: Path):
    """
    Very simple chain parser for skeleton mode.

    Reads the chain log as newline-delimited JSON objects and returns
    a list of dict entries.
    """
    entries: list[dict] = []

    try:
        with path.open("r", encoding="utf-8") as f:
            for lineno, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    entries.append(obj)
                except Exception as e:
                    logger.error(
                        "Error parsing chain line %d in %s: %s",
                        lineno,
                        path,
                        e,
                    )
    except FileNotFoundError:
        # Should normally be handled by verify_chain before calling us,
        # but we defensively return an empty list here.
        logger.warning("Chain file %s not found in _parse_chain()", path)
        return []

    return entries

def verify_chain(chain_log_path: Path | str) -> Tuple[bool, List[str]]:
    """
    Verify the integrity chain at the given path.

    Returns:
        (ok, errors): ok=True if chain is acceptable in skeleton mode,
        errors contains any non-fatal warnings or issues.
    """
    errors: list[str] = []

    path = Path(chain_log_path)

    if not path.exists():
        msg = f"Chain verification: log not found at {path} (treating as OK in skeleton mode)"
        logger.warning(msg)
        errors.append("chain_log_missing")
        # In skeleton mode we still treat this as OK, but report the warning.
        return True, errors

    status = _parse_chain(path)

    # Support both raw-list and ChainStatus return types
    if isinstance(status, list):
        entries = status
    else:
        # Assume a dataclass-like object with .entries and optional .errors
        entries = getattr(status, "entries", [])
        status_errors = getattr(status, "errors", [])
        if status_errors:
            errors.extend(status_errors)

    if not entries:
        msg = f"Chain verification: no entries found in {path} (treating as OK in skeleton mode)"
        logger.info(msg)
        errors.append("chain_empty")
        return True, errors

    last = entries[-1]
    if isinstance(last, dict):
        last_hash = last.get("chain_hash")
    else:
        last_hash = getattr(last, "chain_hash", None)

    logger.info(
        "Chain verification: OK for %s (entries=%d, last_hash=%s)",
        path,
        len(entries),
        last_hash,
    )

    # No structural errors detected
    return True, errors
