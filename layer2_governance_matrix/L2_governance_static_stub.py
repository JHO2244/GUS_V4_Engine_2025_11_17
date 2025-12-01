from dataclasses import dataclass
from typing import List
import json
import os

# ---------------------------------------------------------
# Dataclass required by the tests
# ---------------------------------------------------------

@dataclass
class GovernanceStatus:
    councils_count: int
    pillars_count: int
    construction_laws_count: int
    errors: List[str]


# ---------------------------------------------------------
# Loader: Reads the JSON files in layer2_governance_matrix
# ---------------------------------------------------------

def load_governance_status() -> GovernanceStatus:
    base = os.path.dirname(__file__)

    errors = []

    # Load councils map
    try:
        with open(os.path.join(base, "L2_councils_map.json"), "r") as f:
            councils_map = json.load(f)
        councils_count = len(councils_map.get("councils", []))
    except Exception as e:
        councils_count = 0
        errors.append(f"Failed to load councils map: {e}")

    # Load pillars/laws map
    try:
        with open(os.path.join(base, "L2_pillars_laws_map.json"), "r") as f:
            pillars_laws = json.load(f)
        pillars_count = len(pillars_laws.get("pillars", []))
        construction_laws_count = len(pillars_laws.get("construction_laws", []))
    except Exception as e:
        pillars_count = 0
        construction_laws_count = 0
        errors.append(f"Failed to load pillars/laws map: {e}")

    return GovernanceStatus(
        councils_count=councils_count,
        pillars_count=pillars_count,
        construction_laws_count=construction_laws_count,
        errors=errors
    )


# ---------------------------------------------------------
# Verifier: Returns True if no errors were found
# ---------------------------------------------------------

def verify_governance() -> bool:
    status = load_governance_status()
    return bool(status.errors == [])
