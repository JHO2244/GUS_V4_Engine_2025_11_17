from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class CISpineV03Capabilities:
    """
    CI Spine v0.3 (Full Expansion) capabilities.

    DESIGN RULES (Guardian):
    - Additive only: capabilities can be added, never removed.
    - Non-retroactive: enabling a capability cannot change the meaning of v0.2 results.
    - Deterministic: same inputs -> same outputs.
    """
    # Core: always safe
    verify_seal_by_sha: bool = True
    resolve_anchor_without_checkout: bool = True
    content_only_verification: bool = True  # --no-sig mode supported

    # v0.3 expansions (A2)
    multi_epoch_replay: bool = True
    attestation_bundle: bool = True
    policy_profiles: bool = True
    external_attestation_output: bool = True

    def as_dict(self) -> Dict[str, bool]:
        return {
            "verify_seal_by_sha": self.verify_seal_by_sha,
            "resolve_anchor_without_checkout": self.resolve_anchor_without_checkout,
            "content_only_verification": self.content_only_verification,
            "multi_epoch_replay": self.multi_epoch_replay,
            "attestation_bundle": self.attestation_bundle,
            "policy_profiles": self.policy_profiles,
            "external_attestation_output": self.external_attestation_output,
        }
