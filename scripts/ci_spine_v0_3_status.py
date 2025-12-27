from __future__ import annotations

from pathlib import Path

from ci_spine.v0_3.capabilities.capabilities_v0_3 import CISpineV03Capabilities
from ci_spine.v0_3.attestation.attestation_bundle_v0_3 import AttestationBundleV03


def main() -> None:
    caps = CISpineV03Capabilities()
    bundle = AttestationBundleV03()

    out = {
        "capabilities": caps.as_dict(),
        "note": "CI Spine v0.3 status stub. This does not modify v0.2 verification.",
    }

    # Local, deterministic output (safe; no secrets)
    bundle.write_json(Path("attestations/ci_spine_v0_3_status.json"), out)
    print("OK: wrote attestations/ci_spine_v0_3_status.json")


if __name__ == "__main__":
    main()
