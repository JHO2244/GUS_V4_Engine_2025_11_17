import json
import subprocess
from pathlib import Path

import pytest

from scripts.verify_seal import verify_seal


def _git(repo: Path, *args: str) -> str:
    out = subprocess.check_output(["git", "-C", str(repo), *args], text=True)
    return out.strip()


@pytest.fixture()
def mini_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test User")

    (repo / "requirements.lock").write_text("pkgA==1.0.0\n", encoding="utf-8")
    (repo / "hello.txt").write_text("hello\n", encoding="utf-8")

    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "init")

    return repo


def test_verify_pass_at_commit(mini_repo: Path, tmp_path: Path):
    commit = _git(mini_repo, "rev-parse", "HEAD")
    tree = _git(mini_repo, "rev-parse", "HEAD^{tree}")
    lock_hash = __import__("hashlib").sha256((mini_repo / "requirements.lock").read_bytes()).hexdigest()

    seal = {
        "git_commit": commit,
        "git_tree_hash": tree,
        "lockfile_hashes": {"requirements.lock": lock_hash},
    }
    seal_path = tmp_path / "seal.json"
    seal_path.write_text(json.dumps(seal, indent=2), encoding="utf-8")

    res = verify_seal(repo_root=str(mini_repo), seal_path=str(seal_path), rev=commit, allow_dirty=False)
    assert res.ok is True


def test_verify_fail_on_lockfile_change_working(mini_repo: Path, tmp_path: Path):
    commit = _git(mini_repo, "rev-parse", "HEAD")
    tree = _git(mini_repo, "rev-parse", "HEAD^{tree}")
    lock_hash = __import__("hashlib").sha256((mini_repo / "requirements.lock").read_bytes()).hexdigest()

    seal = {
        "git_commit": commit,
        "git_tree_hash": tree,
        "lockfile_hashes": {"requirements.lock": lock_hash},
    }
    seal_path = tmp_path / "seal.json"
    seal_path.write_text(json.dumps(seal, indent=2), encoding="utf-8")

    (mini_repo / "requirements.lock").write_text("pkgA==9.9.9\n", encoding="utf-8")

    res = verify_seal(repo_root=str(mini_repo), seal_path=str(seal_path), rev="WORKING", allow_dirty=True)
    assert res.ok is False
    diff = (res.details.get("diff") or "").lower()
    assert ("lockfile" in diff) or ("mismatch" in res.message.lower())
