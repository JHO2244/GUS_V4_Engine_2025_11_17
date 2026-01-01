from __future__ import annotations

import argparse
import json
from typing import Any, Dict, List, Optional


def _loads_json(s: str) -> Dict[str, Any]:
    try:
        obj = json.loads(s)
    except Exception as e:
        raise SystemExit(f"Invalid JSON: {e}")
    if not isinstance(obj, dict):
        raise SystemExit("JSON must be an object (dict).")
    return obj


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="gus", description="GUS Operator CLI")
    sub = p.add_subparsers(dest="cmd", required=True)

    g = sub.add_parser("govern", help="Policy → Verdict → Ledger (fail-closed)")
    g.add_argument("--policy", required=True, help="Policy filename in layer9_policy_verdict/policies/")
    g.add_argument("--epoch", required=True, help="Epoch reference string")
    g.add_argument("--head", required=True, help="Chain head hash/string")
    g.add_argument("--action", required=True, help='JSON object, e.g. \'{"type":"merge_pr","target":"main"}\'')
    g.add_argument("--context", required=True, help='JSON object, e.g. \'{"actor":"JHO","checks":"green"}\'')

    return p


def cmd_govern(args: argparse.Namespace) -> int:
    # Import here to keep CLI import-light and avoid circulars during test collection
    from layer9_policy_verdict.src.governance_api import govern_action

    action = _loads_json(args.action)
    context = _loads_json(args.context)

    out = govern_action(
        action=action,
        context=context,
        policy_filename=args.policy,
        epoch_ref=args.epoch,
        chain_head=args.head,
    )

    print(json.dumps(out, indent=2, ensure_ascii=False, sort_keys=True))
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.cmd == "govern":
        return cmd_govern(args)

    raise SystemExit("Unknown command.")


if __name__ == "__main__":
    raise SystemExit(main())
