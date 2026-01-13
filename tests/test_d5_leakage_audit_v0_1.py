from __future__ import annotations
import json
import re
import subprocess
from pathlib import Path

def _grep(pattern: str, paths: list[str]) -> list[str]:
    # Use git grep for tracked content determinism.
    cmd = ["git", "grep", "-nI", "-E", pattern, "--"] + paths
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    out = proc.stdout.strip()
    if proc.returncode == 1:  # no matches
        return []
    if proc.returncode != 0:
        raise AssertionError(f"git grep failed: rc={proc.returncode}\n{out}")
    return out.splitlines()

def test_d5_leakage_audit_shape_and_rules() -> None:
    p = Path("gdvs/d5_privacy/leakage_audit_v0_1.json")
    assert p.exists()
    data = json.loads(p.read_text(encoding="utf-8"))

    allowed_top = {"created_at_utc", "d5_version", "schema_version", "checks"}
    assert set(data.keys()) == allowed_top
    assert data["d5_version"] == "0.1"
    assert data["schema_version"] == "0.1"
    assert isinstance(data["created_at_utc"], str) and data["created_at_utc"].endswith("Z")

    checks = data["checks"]
    assert isinstance(checks, list) and len(checks) >= 4

    allowlisted_note_pat = re.compile(r"(offline_private_key|No secret material in repo|no secrets)")
    for c in checks:
        assert set(c.keys()) == {"id","name","scope","pattern","must_find"}
        assert isinstance(c["scope"], list) and c["scope"]
        assert isinstance(c["pattern"], str) and c["pattern"].strip()

        hits = _grep(c["pattern"], c["scope"])

        mf = c["must_find"]
        if mf == 0:
            # zero matches required
            assert hits == [], f"{c['id']} found hits:\n" + "\n".join(hits[:20])
        elif isinstance(mf, str) and mf.startswith(">="):
            n = int(mf.replace(">=","").strip())
            assert len(hits) >= n, f"{c['id']} expected >= {n} matches"
            # For allowlisted mention check, ensure matches are benign wording
            if c["id"] == "D5-C03":
                assert any(allowlisted_note_pat.search(h) for h in hits)
        else:
            raise AssertionError(f"Unsupported must_find: {mf}")
