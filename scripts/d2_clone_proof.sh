#!/usr/bin/env bash
set -euo pipefail

echo "=== D2 CLONE PROOF v0.1 ==="
echo "utc: $(python - <<'PY'
from datetime import datetime, timezone
print(datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
PY
)"
echo "head: $(git rev-parse HEAD)"

echo "--- seal verify (ci) ---"
python -m scripts.verify_repo_seals --head --require-head --no-sig --ci

echo "--- pytest ---"
python -m pytest -q

echo "--- tracked tree hash x2 ---"
python - <<'PY'
import hashlib, subprocess

def tracked_files():
    out = subprocess.check_output(["git","ls-files","-z"])
    files = out.split(b"\x00")
    return [f.decode("utf-8") for f in files if f]

def file_sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()

def tree_hash() -> str:
    h = hashlib.sha256()
    files = tracked_files()
    for p in files:
        h.update(p.encode("utf-8")); h.update(b"\n")
        h.update(file_sha256(p).encode("ascii")); h.update(b"\n")
    return h.hexdigest(), len(files)

h1, n1 = tree_hash()
h2, n2 = tree_hash()
print("files:", n1, n2)
print("hash1:", h1)
print("hash2:", h2)
print("match:", h1 == h2 and n1 == n2)
if not (h1 == h2 and n1 == n2):
    raise SystemExit(2)
PY

echo "=== D2 CLONE PROOF: OK ==="
