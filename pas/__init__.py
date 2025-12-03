# GUS v4 – PAS (Phase Alignment & Shielding) package
# Guardian Hardening & Tamper-Detection utilities.

"""
PAS Package

This package contains the hardening and tamper-detection suite used by
GUS v4 during PAS (Phase 3 Hardening) checks.
"""
import sys
from pathlib import Path

# Ensure project root is on sys.path so `import pas` works
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pas.pas_hardening_suite_v0_1 import (
    run_full_pas_hardening_suite,
    detect_tamper_signals,
    PASHardeningResult,
)

__all__ = [
    "run_full_pas_hardening_suite",
    "detect_tamper_signals",
    "PASHardeningResult",
]

