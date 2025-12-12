from __future__ import annotations

import sys
from pathlib import Path


def _ensure_repo_root_on_syspath() -> None:
    # tests/ is at repo_root/tests
    repo_root = Path(__file__).resolve().parents[1]
    repo_root_str = str(repo_root)

    # Put repo root first so local packages win over site-packages shadows
    if sys.path and sys.path[0] == repo_root_str:
        return
    if repo_root_str not in sys.path:
        sys.path.insert(0, repo_root_str)


_ensure_repo_root_on_syspath()
