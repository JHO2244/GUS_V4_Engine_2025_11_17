from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class ReplayPlanV03:
    """
    A deterministic plan for verifying multiple epochs in a fixed order.
    This does not interpret governance; it only replays verification.
    """
    epoch_tags_in_order: List[str]

    def validate(self) -> None:
        if not self.epoch_tags_in_order:
            raise ValueError("ReplayPlanV03 requires at least one epoch tag.")
        # Determinism: no duplicates
        if len(set(self.epoch_tags_in_order)) != len(self.epoch_tags_in_order):
            raise ValueError("ReplayPlanV03 must not contain duplicate epoch tags.")
