from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class NonRetroactivityGuard:
    """
    Guardian rule: CI Spine v0.3 must NEVER reinterpret v0.2.
    Meaning: if v0.2 says PASS for a given seal, v0.3 cannot call it FAIL.
    v0.3 may only add extra checks as "additional signals" (warnings/notes), not verdict flips.
    """
    allow_verdict_flip_from_v02: bool = False

    def enforce(self, v02_verdict: str, v03_verdict: str) -> None:
        v02 = (v02_verdict or "").strip().upper()
        v03 = (v03_verdict or "").strip().upper()

        # We keep this strict and simple: v0.2 PASS cannot become v0.3 FAIL.
        if not self.allow_verdict_flip_from_v02:
            if v02 == "PASS" and v03 == "FAIL":
                raise RuntimeError(
                    "NonRetroactivityGuard triggered: v0.3 attempted to flip v0.2 PASS -> FAIL."
                )
