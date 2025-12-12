from __future__ import annotations

import sys
from pathlib import Path

# Allow running as "python scripts/pas_status.py" from repo root without PYTHONPATH.
# This does NOT promote PAS v0.2; it only fixes import resolution for the status script.
_repo_root = Path(__file__).resolve().parents[1]
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

import sys
from typing import List

from pas.pas_hardening_suite_v0_1 import (
    run_all_scenarios as run_pas_v0_1,
    TamperScenarioResult as V01Result,
    PAS_HARDENING_VERSION as PAS_V01,
)

try:
    from pas.pas_hardening_suite_v0_2 import (
        run_all_scenarios as run_pas_v0_2,
        TamperScenarioResult as V02Result,
        PAS_HARDENING_VERSION as PAS_V02,
    )

    HAS_PAS_V02 = True
except ModuleNotFoundError:
    HAS_PAS_V02 = False
    PAS_V02 = None
    V02Result = V01Result  # type: ignore[assignment]


def _overall_status(results: List[V01Result]) -> str:
    if not results:
        return "UNKNOWN"
    if any(r.status not in ("OK", "INFO") for r in results):
        return "ALERT"
    return "OK"


def _print_results(label: str, results: List[V01Result]) -> None:
    print()
    print(label)
    for r in results:
        # v0.1 and v0.2 both have: check_id, status, severity, name
        sev = getattr(r.severity, "value", str(r.severity))
        print(f"{r.check_id} {r.status:<5} {sev:<7} {r.name}")
    print()


def main() -> None:
    print("🛡  GUS v4 – PAS Tamper Grid Status")

    # --- Canonical baseline: PAS v0.1 (blocking) ---
    v01_results = run_pas_v0_1()
    _print_results(f"PAS v0.1 Grid (version={PAS_V01})", v01_results)

    base_status = _overall_status(v01_results)
    print(f"Overall PAS status: {base_status}")

    # --- Overlay: PAS v0.2 (non-blocking enrichment) ---
    if HAS_PAS_V02:
        v02_results = run_pas_v0_2()
        _print_results(
            f"PAS v0.2 Overlay Grid (version={PAS_V02}, non-blocking)", v02_results
        )
    else:
        print()
        print("PAS v0.2 Overlay Grid not available (module import failed).")
        print()

    # Exit code rule:
    # - Only PAS v0.1 can fail the process.
    if base_status != "OK":
        sys.exit(1)
# GUS v4 – PAS v0.2 Overlay Grid (L5–L6 Continuity + Replication)
# Non-blocking, import-only diagnostics.


def _pas_v02_print(code: str, status: str, message: str) -> None:
    """
    Small helper for consistent PAS v0.2 status lines.
    Example: PAS-010 [OK] L5 continuity manifest importable.
    """
    print(f"{code} [{status}] {message}")


def check_pas_010_l5_importable():
    try:
        from layer5_continuity.continuity_manifest_v0_1 import load_manifest

        _ = load_manifest()
        _pas_v02_print("PAS-010", "OK", "L5 continuity manifest importable.")
    except Exception as exc:  # noqa: BLE001 (intentional broad catch for diagnostics)
        _pas_v02_print("PAS-010", "FAIL", f"L5 continuity manifest import failed: {exc!r}")


def check_pas_011_l5_has_entries():
    try:
        from layer5_continuity.continuity_manifest_v0_1 import load_manifest

        manifest = load_manifest()
        entries = manifest.get("continuity_entries", [])
        if isinstance(entries, list) and len(entries) >= 1:
            _pas_v02_print("PAS-011", "OK", "L5 continuity manifest has ≥ 1 continuity entry.")
        else:
            _pas_v02_print(
                "PAS-011",
                "WARN",
                "L5 continuity manifest has no entries or invalid structure.",
            )
    except Exception as exc:  # noqa: BLE001
        _pas_v02_print("PAS-011", "FAIL", f"Error inspecting L5 continuity manifest: {exc!r}")


def check_pas_013_l6_importable():
    try:
        from layer6_replication.replication_manifest_v0_1 import load_manifest

        _ = load_manifest()
        _pas_v02_print("PAS-013", "OK", "L6 replication manifest importable.")
    except Exception as exc:  # noqa: BLE001
        _pas_v02_print("PAS-013", "FAIL", f"L6 replication manifest import failed: {exc!r}")


def check_pas_014_replication_plan_basic():
    try:
        from layer6_replication.replication_manifest_v0_1 import (
            build_replication_plan_from_continuity,
        )

        dummy_targets = ["D:\\GuardianReplicas"]
        plan = build_replication_plan_from_continuity(default_targets=dummy_targets)

        ok = (
            isinstance(plan, dict)
            and isinstance(plan.get("targets"), list)
            and len(plan["targets"]) >= 1
            and plan["targets"][0] == dummy_targets[0]
        )

        if ok:
            _pas_v02_print(
                "PAS-014",
                "OK",
                "Replication plan builds from continuity with valid first target.",
            )
        else:
            _pas_v02_print(
                "PAS-014",
                "WARN",
                "Replication plan structure/targets not as expected.",
            )
    except Exception as exc:  # noqa: BLE001
        _pas_v02_print("PAS-014", "FAIL", f"Error building replication plan: {exc!r}")


def check_pas_015_replication_policy_invariants():
    try:
        from layer6_replication.replication_manifest_v0_1 import load_manifest

        manifest = load_manifest()
        freq = manifest.get("frequency")
        require_all_green = manifest.get("require_all_green")
        max_snapshots = manifest.get("max_snapshots", 0)

        if freq == "on_demand" and require_all_green is True and max_snapshots >= 1:
            _pas_v02_print(
                "PAS-015",
                "OK",
                "Replication policy invariants hold (on_demand, require_all_green=True, max_snapshots ≥ 1).",
            )
        else:
            _pas_v02_print(
                "PAS-015",
                "WARN",
                f"Replication policy invariants drift detected: "
                f"frequency={freq!r}, require_all_green={require_all_green!r}, "
                f"max_snapshots={max_snapshots!r}.",
            )
    except Exception as exc:  # noqa: BLE001
        _pas_v02_print("PAS-015", "FAIL", f"Error reading replication policy invariants: {exc!r}")

# GUS v4 – PAS v0.2 Overlay Grid (L5–L6 Continuity + Replication)
# Non-blocking, import-only diagnostics.


def _pas_v02_print(code: str, status: str, message: str) -> None:
    """
    Small helper for consistent PAS v0.2 status lines.
    Example: PAS-010 [OK] L5 continuity manifest importable.
    """
    print(f"{code} [{status}] {message}")


def check_pas_010_l5_importable():
    try:
        from layer5_continuity.continuity_manifest_v0_1 import load_manifest

        _ = load_manifest()
        _pas_v02_print("PAS-010", "OK", "L5 continuity manifest importable.")
    except Exception as exc:  # noqa: BLE001
        _pas_v02_print("PAS-010", "FAIL", f"L5 continuity manifest import failed: {exc!r}")


def check_pas_011_l5_has_entries():
    try:
        from layer5_continuity.continuity_manifest_v0_1 import load_manifest

        manifest = load_manifest()
        entries = manifest.get("continuity_entries", [])
        if isinstance(entries, list) and len(entries) >= 1:
            _pas_v02_print("PAS-011", "OK", "L5 continuity manifest has ≥ 1 continuity entry.")
        else:
            _pas_v02_print(
                "PAS-011",
                "WARN",
                "L5 continuity manifest has no entries or invalid structure.",
            )
    except Exception as exc:  # noqa: BLE001
        _pas_v02_print("PAS-011", "FAIL", f"Error inspecting L5 continuity manifest: {exc!r}")


def check_pas_013_l6_importable():
    try:
        from layer6_replication.replication_manifest_v0_1 import load_manifest

        _ = load_manifest()
        _pas_v02_print("PAS-013", "OK", "L6 replication manifest importable.")
    except Exception as exc:  # noqa: BLE001
        _pas_v02_print("PAS-013", "FAIL", f"L6 replication manifest import failed: {exc!r}")


def check_pas_014_replication_plan_basic():
    try:
        from layer6_replication.replication_manifest_v0_1 import (
            build_replication_plan_from_continuity,
        )

        dummy_targets = ["D:\\GuardianReplicas"]
        plan = build_replication_plan_from_continuity(default_targets=dummy_targets)

        ok = (
            isinstance(plan, dict)
            and isinstance(plan.get("targets"), list)
            and len(plan["targets"]) >= 1
            and plan["targets"][0] == dummy_targets[0]
        )

        if ok:
            _pas_v02_print(
                "PAS-014",
                "OK",
                "Replication plan builds from continuity with valid first target.",
            )
        else:
            _pas_v02_print(
                "PAS-014",
                "WARN",
                "Replication plan structure/targets not as expected.",
            )
    except Exception as exc:  # noqa: BLE001
        _pas_v02_print("PAS-014", "FAIL", f"Error building replication plan: {exc!r}")


def check_pas_015_replication_policy_invariants():
    try:
        from layer6_replication.replication_manifest_v0_1 import load_manifest

        manifest = load_manifest()
        freq = manifest.get("frequency")
        require_all_green = manifest.get("require_all_green")
        max_snapshots = manifest.get("max_snapshots", 0)

        if freq == "on_demand" and require_all_green is True and max_snapshots >= 1:
            _pas_v02_print(
                "PAS-015",
                "OK",
                "Replication policy invariants hold (on_demand, require_all_green=True, max_snapshots ≥ 1).",
            )
        else:
            _pas_v02_print(
                "PAS-015",
                "WARN",
                f"Replication policy invariants drift detected: "
                f"frequency={freq!r}, require_all_green={require_all_green!r}, "
                f"max_snapshots={max_snapshots!r}.",
            )
    except Exception as exc:  # noqa: BLE001
        _pas_v02_print("PAS-015", "FAIL", f"Error reading replication policy invariants: {exc!r}")

def run_pas_v02_overlay_grid():
    """
    PAS v0.2 L5–L6 overlay grid.
    Non-blocking: diagnostics only, no I/O mutations.
    """
    print("\n[ PAS v0.2 Overlay Grid — L5–L6 Continuity & Replication ]")
    check_pas_010_l5_importable()
    check_pas_011_l5_has_entries()
    check_pas_013_l6_importable()
    check_pas_014_replication_plan_basic()
    check_pas_015_replication_policy_invariants()

def main():
    # Base PAS v0.1 grid
    run_pas_v0_1()

    # PAS v0.2 overlay grid (L5–L6)
    run_pas_v02_overlay_grid()


if __name__ == "__main__":
    main()


def run_pas_v02_overlay_grid():
    """
    PAS v0.2 L5–L6 overlay grid.
    Non-blocking: diagnostics only, no I/O mutations.
    """
    print("\n[ PAS v0.2 Overlay Grid — L5–L6 Continuity & Replication ]")
    check_pas_010_l5_importable()
    check_pas_011_l5_has_entries()
    check_pas_013_l6_importable()
    check_pas_014_replication_plan_basic()
    check_pas_015_replication_policy_invariants()

if __name__ == "__main__":
    main()
