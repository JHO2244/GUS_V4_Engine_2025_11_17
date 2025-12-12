from __future__ import annotations

from pathlib import Path
from typing import List
import sys
sys.stdout.reconfigure(encoding="utf-8")

def _bootstrap_repo_root_for_script_run() -> None:
    """
    Allow running as:  python scripts/pas_status.py  (from repo root)
    without requiring PYTHONPATH.

    Security posture:
    - Only adjust sys.path when executed as a SCRIPT (not when imported).
    - Insert repo root at sys.path[0] to prefer local modules intentionally.
    """
    if __package__ is not None:
        # Running as module (python -m scripts.pas_status) or imported: do nothing.
        return

    repo_root = Path(__file__).resolve().parents[1]
    repo_root_str = str(repo_root)

    if sys.path and sys.path[0] == repo_root_str:
        return

    if repo_root_str not in sys.path:
        sys.path.insert(0, repo_root_str)


_bootstrap_repo_root_for_script_run()

# Imports after bootstrap (only impacts script-run mode)
from pas.pas_hardening_suite_v0_1 import (  # noqa: E402
    run_all_scenarios as run_pas_v0_1,
    TamperScenarioResult as V01Result,
    PAS_HARDENING_VERSION as PAS_V01,
)

try:
    from pas.pas_hardening_suite_v0_2 import (  # noqa: E402
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
        sev = getattr(r.severity, "value", str(r.severity))
        print(f"{r.check_id} {r.status:<5} {sev:<7} {r.name}")
    print()


def main() -> int:
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

    # Exit code rule: only PAS v0.1 can fail the process.
    return 0 if base_status == "OK" else 1


if __name__ == "__main__":
    raise SystemExit(main())
