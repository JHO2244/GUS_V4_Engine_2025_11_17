# scripts/pas_status.py

from __future__ import annotations

import sys
from typing import List

from pas.pas_hardening_suite_v0_1 import run_all_scenarios, PasCheckResult


def _format_status_line(r: PasCheckResult) -> str:
    return f"{r.check_id:7} {r.status:6} {r.severity.value:8} {r.name}"


def _overall_from_pas000(results: List[PasCheckResult]) -> str:
    # Prefer the PAS-000 derived status if present
    for r in results:
        if r.check_id == "PAS-000":
            return r.status
    # Fallback: if PAS-000 ever missing, default to ALERT
    return "ALERT"


def main() -> None:
    results = run_all_scenarios()

    print("🛡  GUS v4 – PAS Tamper Grid Status\n")
    for r in results:
        print(_format_status_line(r))

    overall = _overall_from_pas000(results)

    if overall == "OK":
        print("\nOverall PAS status: OK")
        exit_code = 0
    elif overall == "WARN":
        print("\nOverall PAS status: WARN ⚠")
        exit_code = 1
    else:
        # ALERT or anything worse → non-zero
        print("\nOverall PAS status: ALERT ⚠")
        exit_code = 2

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
