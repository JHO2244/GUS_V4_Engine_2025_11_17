from __future__ import annotations

from pathlib import Path
import shutil

import pytest


CHARTER = Path("GUS_PURPOSE_CHARTER_v4.json")


def test_cli_requires_charter(monkeypatch, tmp_path):
    backup = None
    if CHARTER.exists():
        backup = tmp_path / "GUS_PURPOSE_CHARTER_v4.json.bak"
        shutil.copy2(CHARTER, backup)
        CHARTER.unlink()

    try:
        from cli.gus_cli import main
        with pytest.raises(SystemExit):
            main(["govern", "--policy", "L9_BASE_STRICT", "--action", "{}", "--context", "{}"])
    finally:
        if backup and backup.exists():
            shutil.copy2(backup, CHARTER)
