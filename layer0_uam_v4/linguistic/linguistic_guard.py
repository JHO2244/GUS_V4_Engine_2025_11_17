from __future__ import annotations

import argparse
import json

from utils.canonical_json import write_canonical_json_file
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple

REPO_ROOT = Path(__file__).resolve().parents[2]  # layer0_uam_v4/linguistic -> repo root
CANON_PATH = REPO_ROOT / "linguistic" / "canon" / "glc_v1_1.json"
LEDGER_DIR = REPO_ROOT / "linguistic" / "logs"


@dataclass(frozen=True)
class Finding:
    level: str  # PASS/WARN/FAIL
    kind: str   # SCE or SID
    term: str
    message: str
    file: str


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def load_canon() -> Dict:
    if not CANON_PATH.exists():
        raise FileNotFoundError(f"GLC canon not found: {CANON_PATH}")
    return json.loads(CANON_PATH.read_text(encoding="utf-8"))


def gather_text_files(root: Path) -> List[Path]:
    # Intentionally narrow: only docs + readme + markdown + txt
    exts = {".md", ".txt", ".rst"}
    files: List[Path] = []
    for p in root.rglob("*"):
        if p.is_file() and p.suffix.lower() in exts:
            # skip venv, .git, caches
            if any(part in (".git", ".venv", "venv", "__pycache__") for part in p.parts):
                continue
            files.append(p)
    return files


def extract_term_occurrences(text: str, term: str) -> List[Tuple[int, str]]:
    # simple line-based extraction; stable + fast; avoids NLP complexity
    pattern = re.compile(rf"\b{re.escape(term)}\b", re.IGNORECASE)
    out: List[Tuple[int, str]] = []
    for i, line in enumerate(text.splitlines(), start=1):
        if pattern.search(line):
            out.append((i, line.strip()))
    return out


def sce_check(term_entry: Dict, context_line: str) -> Tuple[str, str]:
    """
    Human-readable first: we detect likely misuse signals with lightweight heuristics.
    PASS/WARN/FAIL based on contamination markers.
    """
    forbidden = term_entry.get("forbidden_usage", [])
    # If any forbidden phrase appears in the line, warn/fail
    lowered = context_line.lower()

    hits = [f for f in forbidden if f.lower() in lowered]
    if hits:
        # If line asserts moral judgement or ideology, fail; else warn.
        hard_markers = ["virtue", "moral", "ideology", "politic", "good person", "bad person", "righteous"]
        if any(m in lowered for m in hard_markers):
            return "FAIL", f"Forbidden framing detected: {hits}"
        return "WARN", f"Potential forbidden framing detected: {hits}"

    # If line uses heavy certainty language without verification cues for TRUTH/VERIFICATION, warn
    if term_entry["term"].lower() in ("truth", "verification"):
        certainty = ["obviously", "clearly", "everyone knows", "no doubt"]
        if any(c in lowered for c in certainty) and not any(v in lowered for v in ("test", "verify", "audit", "evidence", "repeat")):
            return "WARN", "Certainty framing without verification cues."

    return "PASS", "Canonical usage appears clean."


def sid_check(line: str) -> Tuple[bool, str]:
    """
    Behavioral intrusion markers (one-page SID sheet) — lightweight heuristics.
    """
    lowered = line.lower()
    high = [
        "redefine", "new meaning", "what we really mean is", "obviously", "clearly",
        "everyone knows", "just for now", "temporarily", "for this context only"
    ]
    medium = ["urgent", "righteous", "moral", "virtue", "ideological", "political"]

    if any(h in lowered for h in high):
        return True, "SID high-confidence marker present."
    if sum(1 for m in medium if m in lowered) >= 2:
        return True, "SID medium-confidence cluster present."
    return False, ""


def write_ledger(findings: List[Finding], canon_version: str) -> Path:
    LEDGER_DIR.mkdir(parents=True, exist_ok=True)
    stamp = _utc_stamp()
    out_path = LEDGER_DIR / f"ssl_{canon_version}_{stamp}.json"
    payload = {
        "ts_utc": stamp,
        "canon_version": canon_version,
        "counts": {
            "PASS": sum(1 for f in findings if f.level == "PASS"),
            "WARN": sum(1 for f in findings if f.level == "WARN"),
            "FAIL": sum(1 for f in findings if f.level == "FAIL"),
            "SID": sum(1 for f in findings if f.kind == "SID")
        },
        "findings": [f.__dict__ for f in findings]
    }
    write_canonical_json_file(out_path, payload)
    return out_path


def main() -> int:
    ap = argparse.ArgumentParser(description="GUS v4 Linguistic Guard (GLC/SCE/SID/SSL) — non-blocking by default.")
    ap.add_argument("--strict", action="store_true", help="Exit non-zero on FAIL findings.")
    ap.add_argument("--path", default=str(REPO_ROOT), help="Root path to scan (default: repo root).")
    args = ap.parse_args()

    canon = load_canon()
    canon_version = canon.get("glc_version", "unknown")
    terms = canon.get("terms", [])

    root = Path(args.path).resolve()
    files = gather_text_files(root)

    findings: List[Finding] = []

    for fp in files:
        text = fp.read_text(encoding="utf-8", errors="ignore")
        for t in terms:
            term = t["term"]
            occ = extract_term_occurrences(text, term)
            for lineno, line in occ:
                # Canonical Defaulting (CD): if term used, canon meaning is assumed; we only flag misuse markers.
                level, msg = sce_check(t, line)
                findings.append(Finding(level=level, kind="SCE", term=term, message=f"{msg} (line {lineno})", file=str(fp)))

                sid_hit, sid_msg = sid_check(line)
                if sid_hit:
                    findings.append(Finding(level="WARN" if level != "FAIL" else "FAIL", kind="SID", term=term, message=f"{sid_msg} (line {lineno})", file=str(fp)))

    ledger_path = write_ledger(findings, canon_version)

    # Summary to stdout (fast + readable)
    counts = {
        "PASS": sum(1 for f in findings if f.level == "PASS" and f.kind == "SCE"),
        "WARN": sum(1 for f in findings if f.level == "WARN"),
        "FAIL": sum(1 for f in findings if f.level == "FAIL"),
        "SID": sum(1 for f in findings if f.kind == "SID")
    }

    print("🛡 Linguistic Guard Summary")
    print(f"• Canon: GLC v{canon_version}")
    print(f"• Files scanned: {len(files)}")
    print(f"• PASS (SCE): {counts['PASS']}")
    print(f"• WARN total: {counts['WARN']}")
    print(f"• FAIL total: {counts['FAIL']}")
    print(f"• SID flags: {counts['SID']}")
    print(f"• SSL ledger: {ledger_path}")

    if args.strict and counts["FAIL"] > 0:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
