#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def run(cmd: list[str]) -> tuple[int, str]:
    p = subprocess.run(cmd, text=True, capture_output=True)
    out = (p.stdout or "") + (p.stderr or "")
    return p.returncode, out


def repo_root() -> Path:
    rc, out = run(["git", "rev-parse", "--show-toplevel"])
    if rc != 0:
        raise SystemExit("FAIL: not inside a git repo")
    return Path(out.strip())


def main() -> int:
    ap = argparse.ArgumentParser(description="GUS v4: Verify epoch anchor seal (CI-safe).")
    ap.add_argument(
        "--manifest",
        type=Path,
        default=Path("epochs/epoch_bada220e_20251221T120542Z/epoch_manifest_v0_1.json"),
        help="Path to epoch manifest JSON",
    )
    ap.add_argument("--pub", type=Path, default=Path("keys/gus_seal_signing_ed25519_pub.pem"))
    args = ap.parse_args()

    root = repo_root()
    manifest_path = (root / args.manifest) if not args.manifest.is_absolute() else args.manifest
    pubkey = (root / args.pub) if not args.pub.is_absolute() else args.pub

    if not manifest_path.exists():
        raise SystemExit(f"FAIL: manifest missing: {manifest_path}")

    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    epoch = data["epoch"]
    seal_json = (root / epoch["seal_json"]).resolve()
    seal_sig = (root / epoch["seal_sig"]).resolve()

    print(f"[EPOCH-CI] Manifest: {manifest_path}")
    print(f"[EPOCH-CI] Anchor commit: {epoch['head_commit']}")
    print(f"[EPOCH-CI] Anchor seal JSON: {seal_json}")
    print(f"[EPOCH-CI] Anchor seal SIG:  {seal_sig}")

    if not seal_json.exists():
        raise SystemExit("FAIL: epoch seal JSON missing")

    rc, out = run([sys.executable, "-m", "scripts.verify_seal", str(seal_json)])
    print(out.rstrip())
    if rc != 0:
        raise SystemExit("FAIL: epoch seal content verification failed")

    if not seal_sig.exists():
        raise SystemExit("FAIL: epoch seal signature missing")

    rc, out = run([sys.executable, "-m", "scripts.verify_seal_signature", str(seal_json), "--pub", str(pubkey)])
    print(out.rstrip())
    if rc != 0:
        raise SystemExit("FAIL: epoch seal signature verification failed")

    print("[OK] Epoch anchor verified (CI-safe).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
