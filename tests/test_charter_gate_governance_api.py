from __future__ import annotations

from pathlib import Path
import shutil

import pytest


CHARTER = Path("GUS_PURPOSE_CHARTER_v4.json")


def test_governance_api_requires_charter(monkeypatch, tmp_path):
    # Temporarily hide charter if present
    backup = None
    if CHARTER.exists():
        backup = tmp_path / "GUS_PURPOSE_CHARTER_v4.json.bak"
        shutil.copy2(CHARTER, backup)
        CHARTER.unlink()

    try:
        from layer9_policy_verdict.src.governance_api import govern_action
        # minimal inputs (your govern_action may differ; adjust only argument names if needed)
        with pytest.raises(Exception):
            govern_action(
                action={"type": "test"},
                context={"x": 1},
                policy_id="L9_BASE_STRICT",
                epoch_ref="epoch_test",
                chain_head="head_test",
            )
    finally:
        if backup and backup.exists():
            shutil.copy2(backup, CHARTER)
