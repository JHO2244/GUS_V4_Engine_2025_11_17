#!/usr/bin/env python
from __future__ import annotations

import argparse
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.hazmat.primitives import serialization


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("seal", type=Path)
    ap.add_argument("--pub", type=Path, required=True)
    ap.add_argument(
        "--allow-missing-sig",
        action="store_true",
        help="Relaxed mode: if .sig is missing, print NOTE and exit 0 (content may still be valid).",
    )
    args = ap.parse_args()

    sig_path = args.seal.with_suffix(args.seal.suffix + ".sig")
    if not sig_path.exists():
        if args.allow_missing_sig:
            print("NOTE: signature file missing (allowed by policy)")
            return 0
        raise SystemExit("ERROR: signature file missing")

    pub = serialization.load_pem_public_key(args.pub.read_bytes())
    if not isinstance(pub, Ed25519PublicKey):
        raise SystemExit("ERROR: Not an Ed25519 public key")

    pub.verify(sig_path.read_bytes(), args.seal.read_bytes())
    print("OK: signature valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
