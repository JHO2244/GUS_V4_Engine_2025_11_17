from __future__ import annotations

from pathlib import Path

from utils.canonical_json import write_canonical_json_file, canonical_dumps


def test_canonical_writer_single_line_and_newline(tmp_path: Path) -> None:
    obj = {"b": 1, "a": {"z": 9, "y": 8}}
    out = tmp_path / "seal.json"

    write_canonical_json_file(out, obj)

    raw = out.read_bytes()
    text = raw.decode("utf-8")

    # must end with exactly one newline
    assert text.endswith("\n")
    assert not text.endswith("\n\n")

    # must be single line JSON + newline
    assert text.count("\n") == 1

    # must match canonical dumps + newline
    assert text == canonical_dumps(obj) + "\n"
