from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from layer9_policy_verdict.src.policy_schema import require_policy_v1


POLICY_DIR = Path(__file__).resolve().parent.parent / "policies"


def load_policy(policy_filename: str) -> Dict[str, Any]:
    path = POLICY_DIR / policy_filename
    if not path.exists():
        raise FileNotFoundError(f"Policy not found: {path}")
    policy = json.loads(path.read_text(encoding="utf-8"))
    require_policy_v1(policy)
    return policy
