from __future__ import annotations

import pathlib
import tempfile

from layer9_preservation.preservation_package_v0_1 import (
    build_preservation_package,
    verify_preservation_package,
)


def test_l9_1_build_and_verify_roundtrip(tmp_path: pathlib.Path) -> None:
    # Create a fake repo root with deterministic files
    repo = tmp_path / "repo"
    repo.mkdir()

    (repo / "layer9_preservation").mkdir()
    (repo / "tests").mkdir()

    (repo / "layer9_preservation" / "a.py").write_text("print('A')\n", encoding="utf-8", newline="\n")
    (repo / "tests" / "t.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8", newline="\n")
    (repo / "README.md").write_text("# Demo\n", encoding="utf-8", newline="\n")

    out_dir = tmp_path / "out"

    res = build_preservation_package(
        repo_root=str(repo),
        out_dir=str(out_dir),
        anchor="ANCHOR123",
        note="unit test",
        create_zip=True,
    )

    assert pathlib.Path(res.manifest_path).exists()
    assert pathlib.Path(res.seal_path).exists()
    assert res.zip_path is not None and pathlib.Path(res.zip_path).exists()

    assert verify_preservation_package(repo_root=str(repo), package_dir=str(out_dir)) is True


def test_l9_1_zip_is_deterministic(tmp_path: pathlib.Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "layer1_integrity_core").mkdir(parents=True)
    (repo / "layer1_integrity_core" / "x.py").write_text("x=1\n", encoding="utf-8", newline="\n")
    (repo / "README.md").write_text("R\n", encoding="utf-8", newline="\n")

    out1 = tmp_path / "out1"
    out2 = tmp_path / "out2"

    r1 = build_preservation_package(repo_root=str(repo), out_dir=str(out1), anchor="A", note="N", create_zip=True)
    r2 = build_preservation_package(repo_root=str(repo), out_dir=str(out2), anchor="A", note="N", create_zip=True)

    z1 = pathlib.Path(r1.zip_path)  # type: ignore[arg-type]
    z2 = pathlib.Path(r2.zip_path)  # type: ignore[arg-type]

    assert z1.read_bytes() == z2.read_bytes()
