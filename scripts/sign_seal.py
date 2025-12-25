#!/usr/bin/env python
from __future__ import annotations

import argparse
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization
from utils.console_symbols import sym

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("seal", type=Path)
    ap.add_argument("--key", type=Path, required=True)
    args = ap.parse_args()

    seal_bytes = args.seal.read_bytes()

    key = serialization.load_pem_private_key(
        args.key.read_bytes(),
        password=None,
    )
    if not isinstance(key, Ed25519PrivateKey):
        raise SystemExit("ERROR: Not an Ed25519 private key")

    sig = key.sign(seal_bytes)
    sig_path = args.seal.with_suffix(args.seal.suffix + ".sig")
    sig_path.write_bytes(sig)

    print(f"OK: signed {args.seal.name} {sym('arrow')} {sig_path.name}")


if __name__ == "__main__":
    main()

