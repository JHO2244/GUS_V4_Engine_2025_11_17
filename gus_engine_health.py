from datetime import datetime, timezone
from layer1_integrity_core.L1_integrity_core_stub import (
    load_integrity_status,
    verify_integrity,
)


def get_engine_health_summary() -> dict:
    """
    Aggregate a lightweight health summary for the engine, currently focused on L1.

    Returns a JSON-serializable dict, e.g.:

    {
        "overall_ok": true,
        "checked_at": "...Z",
        "layers": {
            "L1_integrity_core": {
                "engine_ok": true,
                "reason": "integrity verified",
                "checked_at": "...Z",
                "files_checked": 0
            }
        }
    }
    """
    # 1) Load the raw status object from L1
    status = load_integrity_status()  # IntegrityStatus

    # 2) Run the simple integrity gate (boolean)
    try:
        engine_ok = bool(verify_integrity())
    except Exception as exc:
        engine_ok = False
        reason = f"verify_integrity raised: {exc!r}"
    else:
        # Prefer an explicit reason if present on status, otherwise generic
        reason = getattr(status, "reason", None) or (
            "integrity verified" if engine_ok else "integrity verification failed"
        )

    # 3) Extract optional metadata safely
    checked_at = getattr(status, "checked_at", None)
    if checked_at is None:
        checked_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    files_checked = 0
    files = getattr(status, "files", None)
    if isinstance(files, (list, tuple)):
        files_checked = len(files)

    # 4) Build normalized health summary
    layer_summary = {
        "engine_ok": engine_ok,
        "reason": reason,
        "checked_at": checked_at,
        "files_checked": files_checked,
    }

    return {
        "overall_ok": bool(engine_ok),
        "checked_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "layers": {
            "L1_integrity_core": layer_summary,
        },
    }


import json


def main() -> None:
    summary = get_engine_health_summary()
    print(json.dumps(summary, indent=2, sort_keys=False))


if __name__ == "__main__":
    main()
