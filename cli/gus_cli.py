from __future__ import annotations
from gus_purpose_charter_gate import require_charter_v4

import argparse
import json
import os
import sys
from typing import Any, Dict

from layer9_policy_verdict.src.governance_api import govern_action


def _loads_json(s: str) -> Dict[str, Any]:
    try:
        obj = json.loads(s)
        if not isinstance(obj, dict):
            raise ValueError("JSON must be an object/dict.")
        return obj
    except Exception as e:
        raise SystemExit(f"Invalid JSON: {e}")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="gus_cli", description="GUS v4 Operator CLI (v1)")
    sub = p.add_subparsers(dest="cmd", required=True)

    g = sub.add_parser("govern", help="Evaluate action+context under a policy and append verdict to L8 ledger")
    g.add_argument("--policy", required=True, help="Policy filename (e.g. L9_MERGE_MAIN.json)")
    g.add_argument("--epoch", required=True, help="Epoch reference (e.g. epoch_..._anchor_main)")
    g.add_argument("--head", required=True, help="Chain head hash (e.g. L8 chain head)")
    g.add_argument("--action", required=True, help='Action JSON object (e.g. \'{"type":"merge_pr","target":"main"}\')')
    g.add_argument("--context", required=True, help='Context JSON object (e.g. \'{"actor":"JHO","checks":"green"}\')')
    return p


def cmd_govern(args: argparse.Namespace) -> int:
    action = _loads_json(args.action)
    context = _loads_json(args.context)

    require_charter_v4()  # fail-closed if charter missing/invalid

    out = govern_action(
        action=action,
        context=context,
        policy_filename=args.policy,
        epoch_ref=args.epoch,
        chain_head=args.head,
    )

    # Print compact JSON (stable keys)
    payload = {
        "ok": out["ok"],
        "level": out["level"],
        "score": out["score"],
        "ledger_hash": out["ledger_hash"],
        "policy_id": out["verdict"].policy_id,
        "object_hash": out["verdict"].object_hash,
    }
    print(json.dumps(payload, ensure_ascii=False))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.cmd == "govern":
        return cmd_govern(args)

    raise SystemExit("Unknown command.")


if __name__ == "__main__":
    raise SystemExit(main())
