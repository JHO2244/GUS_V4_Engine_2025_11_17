# Future: chain engine (stub only for now)
from __future__ import annotations

import json
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from utils import get_guardian_logger, hash_text


logger = get_guardian_logger("GUSv4.Chain")

# We keep the existing file name so we don't break config/status.
CHAIN_LOG_FILENAME = "gus_chain_log_placeholder.txt"


@dataclass
class ChainEntry:
    index: int
    timestamp: float
    event: str
    payload: Dict[str, Any]
    prev_hash: str
    hash: str


def get_default_chain_log_path() -> Path:
    """
    Default path used when no explicit chain_log_path is provided.
    """
    return Path(__file__).resolve().parent / CHAIN_LOG_FILENAME


def _load_raw_lines(path: Path) -> List[str]:
    if not path.exists():
        return []
    return path.read_text(encoding="utf-8").splitlines()


def load_chain(path: Optional[Path] = None) -> List[ChainEntry]:
    """
    Load the chain as a list of ChainEntry objects.
    Ignores malformed lines but logs warnings.
    """
    log_path = path or get_default_chain_log_path()
    entries: List[ChainEntry] = []

    for line in _load_raw_lines(log_path):
        line = line.strip()
        if not line:
            continue
        try:
            data = json.loads(line)
            entries.append(ChainEntry(**data))
        except Exception:
            logger.warning("Skipping malformed chain line in %s", log_path)

    return entries


def _compute_entry_hash(
    index: int,
    timestamp: float,
    event: str,
    payload: Dict[str, Any],
    prev_hash: str,
) -> str:
    """
    Deterministically compute the hash for a chain entry.
    """
    base = json.dumps(
        {
            "index": index,
            "timestamp": timestamp,
            "event": event,
            "payload": payload,
            "prev_hash": prev_hash,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return hash_text(base)


def append_chain_event(
    event: str,
    payload: Dict[str, Any],
    path: Optional[Path] = None,
) -> ChainEntry:
    """
    Append a new event to the chain log and return the ChainEntry.
    Safe in the sense that it only touches the chain file.
    """
    log_path = path or get_default_chain_log_path()
    log_path.parent.mkdir(parents=True, exist_ok=True)

    entries = load_chain(log_path)

    if entries:
        last = entries[-1]
        next_index = last.index + 1
        prev_hash = last.hash
    else:
        next_index = 0
        prev_hash = "GENESIS"

    ts = time.time()
    entry_hash = _compute_entry_hash(next_index, ts, event, payload, prev_hash)

    entry = ChainEntry(
        index=next_index,
        timestamp=ts,
        event=event,
        payload=payload,
        prev_hash=prev_hash,
        hash=entry_hash,
    )

    with log_path.open("a", encoding="utf-8") as f:
        f.write(
            json.dumps(asdict(entry), sort_keys=True, separators=(",", ":"))
            + "\n"
        )

    logger.info(
        "Appended chain event %s index=%s hash=%s path=%s",
        event,
        next_index,
        entry_hash,
        log_path,
    )
    return entry


def verify_chain(path: Optional[Path] = None) -> Tuple[bool, List[str]]:
    """
    Verify the continuity and hash integrity of the chain.
    Returns (ok, errors_list).
    """
    log_path = path or get_default_chain_log_path()
    errors: List[str] = []
    entries = load_chain(log_path)

    if not entries:
        # In skeleton mode, an empty chain is not treated as a hard failure.
        errors.append("chain_empty")
        logger.info(
            "Chain verification: no entries found (%s); treating as OK in skeleton mode.",
            log_path,
        )
        return True, errors

    for i, entry in enumerate(entries):
        expected_index = i
        if entry.index != expected_index:
            msg = f"index_mismatch at stored={entry.index} expected={expected_index}"
            errors.append(msg)
            logger.error("Chain verification failed: %s", msg)
            return False, errors

        if i == 0:
            expected_prev = "GENESIS"
        else:
            expected_prev = entries[i - 1].hash

        if entry.prev_hash != expected_prev:
            msg = f"prev_hash_mismatch at index={i}"
            errors.append(msg)
            logger.error("Chain verification failed: %s", msg)
            return False, errors

        recomputed_hash = _compute_entry_hash(
            entry.index,
            entry.timestamp,
            entry.event,
            entry.payload,
            entry.prev_hash,
        )
        if entry.hash != recomputed_hash:
            msg = f"hash_mismatch at index={i}"
            errors.append(msg)
            logger.error("Chain verification failed: %s", msg)
            return False, errors

    logger.info(
        "Chain verification OK: %s entries, path=%s",
        len(entries),
        log_path,
    )
    return True, errors
