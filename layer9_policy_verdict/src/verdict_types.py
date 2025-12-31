from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

class VerdictLevel(str, Enum):
    ALLOW = "allow"
    WARN = "warn"
    BLOCK = "block"

@dataclass(frozen=True)
class PolicyVerdict:
    level: VerdictLevel
    score: float  # 0.0–10.0
    reasons: List[str]
    evidence: Dict[str, Any]
    policy_id: str
    epoch_ref: str
    chain_head: str
    object_hash: str
