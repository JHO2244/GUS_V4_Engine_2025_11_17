#!/usr/bin/env python
from __future__ import annotations

import argparse
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("seal", type=Path)
    ap.add_argument("--priv", type=Path, required=True, help="Ed25519 private key (PEM, PKCS8)")
    args = ap.parse_args()

    if not args.seal.exists():
        raise SystemExit("ERROR: seal file missing")

    priv = serialization.load_pem_private_key(args.priv.read_bytes(), password=None)
    if not isinstance(priv, Ed25519PrivateKey):
        raise SystemExit("ERROR: Not an Ed25519 private key")

    sig = priv.sign(args.seal.read_bytes())
    sig_path = args.seal.with_suffix(args.seal.suffix + ".sig")
    sig_path.write_bytes(sig)
    print(f"OK: wrote signature {sig_path}")


if __name__ == "__main__":
    main()
