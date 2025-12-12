# GUS v4 – PAS Status Script Contract Tests
# Goal: ensure pas_status runs as module, prints once, and returns correct exit code.

import subprocess
import sys


def test_pas_status_module_runs_ok_and_prints_once():
    proc = subprocess.run(
        [sys.executable, "-m", "scripts.pas_status"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
    )

    out = (proc.stdout or "") + (proc.stderr or "")
    HEADER_ANCHOR = "PAS Tamper Grid Status"  # ASCII-only anchor

    assert proc.returncode == 0, f"Expected exit code 0, got {proc.returncode}\n{out}"
    assert out.count(HEADER_ANCHOR) == 1, out
    assert out.count("PAS v0.1 Grid") == 1, out
