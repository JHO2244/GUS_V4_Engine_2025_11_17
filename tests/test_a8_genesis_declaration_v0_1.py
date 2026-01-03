from pathlib import Path
import json

from layer8_genesis.genesis_declaration_v0_1 import (
    build_genesis_declaration_v0_1,
    write_genesis_declaration,
)


def test_a8_genesis_declaration_has_required_fields(tmp_path: Path) -> None:
    decl = build_genesis_declaration_v0_1(created_utc="2099-01-01T00:00:00Z")
    d = decl.to_dict()

    # Required keys
    for k in [
        "version",
        "system_name",
        "repo_root",
        "head_sha",
        "epoch_anchor_tag",
        "epoch_anchor_sha",
        "seal_policy",
        "signature_policy",
        "determinism_policy",
        "invariants",
        "created_utc",
    ]:
        assert k in d

    assert d["version"] == "v0.1"
    assert d["system_name"] == "GUS v4"
    assert isinstance(d["invariants"], list)
    assert d["created_utc"].endswith("Z")


def test_a8_genesis_declaration_is_canonical_json(tmp_path: Path) -> None:
    decl = build_genesis_declaration_v0_1(created_utc="2099-01-01T00:00:00Z")
    out = tmp_path / "genesis.json"
    write_genesis_declaration(out, decl)

    raw = out.read_text(encoding="utf-8")
    assert raw.endswith("\n"), "Must end with LF newline"
    # canonical JSON must parse
    parsed = json.loads(raw)
    assert parsed["version"] == "v0.1"
