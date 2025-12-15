# scripts/verify_repo_seals.py
from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path
import sys

SEALS_DIR = Path("seals")
SEAL_RE = re.compile(r"^seal_([0-9a-fA-F]+)_(\d{8,})\.json$")  # timestamp len flexible


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, text=True, capture_output=True)


def sh(cmd: list[str]) -> str:
    p = subprocess.run(cmd, text=True, capture_output=True)
    if p.returncode != 0:
        raise SystemExit(f"✖ Command failed: {' '.join(cmd)}\n{p.stderr.strip()}")
    return p.stdout.strip()


def head_short() -> str:
    return sh(["git", "rev-parse", "--short", "HEAD"])


def list_seals() -> list[Path]:
    if not SEALS_DIR.exists():
        return []
    seals = []
    for p in SEALS_DIR.glob("seal_*_*.json"):
        m = SEAL_RE.match(p.name)
        if m:
            seals.append((m.group(2), p))  # timestamp string
    # sort by timestamp then name (stable)
    seals.sort(key=lambda t: (t[0], t[1].name))
    return [p for _, p in seals]


def find_latest_seal_for_short_hash(short_hash: str) -> Path | None:
    seals = list_seals()
    matches = [p for p in seals if p.name.startswith(f"seal_{short_hash}_")]
    return matches[-1] if matches else None


def module_exists(mod: str) -> bool:
    p = run([sys.executable, "-c", f"import importlib; importlib.import_module('{mod}')"])
    return p.returncode == 0


def verify_one(seal_path: Path, verify_sig: bool, strict_sig: bool) -> None:
    if not seal_path.exists():
        raise SystemExit(f"✖ Seal file missing: {seal_path}")

    # 1) Structural + content verification
    p = run([sys.executable, "-m", "scripts.verify_seal", str(seal_path)])
    if p.returncode != 0:
        raise SystemExit(
            f"✖ verify_seal failed for {seal_path.name}\n{p.stdout.strip()}\n{p.stderr.strip()}"
        )

    # 2) Signature verification (optional)
    if verify_sig:
        if not module_exists("scripts.verify_seal_signature"):
            msg = "✖ scripts.verify_seal_signature not found/importable."
            if strict_sig:
                raise SystemExit(msg)
            print(f"⚠ {msg} (continuing because --strict-sig not set)")
        else:
            p = run([sys.executable, "-m", "scripts.verify_seal_signature", str(seal_path)])
            if p.returncode != 0:
                raise SystemExit(
                    f"✖ verify_seal_signature failed for {seal_path.name}\n{p.stdout.strip()}\n{p.stderr.strip()}"
                )

    print(f"✔ OK: {seal_path.name}")


def main() -> int:
    ap = argparse.ArgumentParser(description="GUS v4: Verify repo seals (HEAD or last N).")
    ap.add_argument("--head", action="store_true", help="verify latest seal for HEAD")
    ap.add_argument("--last", type=int, default=0, help="verify last N seals (chronological)")
    ap.add_argument("--no-sig", action="store_true", help="skip signature verification")
    ap.add_argument("--strict-sig", action="store_true", help="fail if signature verifier missing")
    args = ap.parse_args()

    verify_sig = not args.no_sig
    seals = list_seals()
    if not seals:
        raise SystemExit("✖ No seals found in ./seals/")

    did_any = False

    if args.head or (not args.head and args.last == 0):
        hs = head_short()
        p = find_latest_seal_for_short_hash(hs)
        if not p:
            raise SystemExit(f"✖ No seal found for HEAD short hash: {hs}")
        print(f"→ Verifying HEAD seal: {p}")
        verify_one(p, verify_sig=verify_sig, strict_sig=args.strict_sig)
        did_any = True

    if args.last > 0:
        batch = seals[-args.last:]
        print(f"→ Verifying last {len(batch)} seal(s)")
        for p in batch:
            verify_one(p, verify_sig=verify_sig, strict_sig=args.strict_sig)
        did_any = True

    if not did_any:
        raise SystemExit("✖ Nothing to verify (unexpected argument state).")

    print("✅ Seal verification complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
