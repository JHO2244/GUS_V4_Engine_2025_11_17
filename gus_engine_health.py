from layer1_integrity_core.L1_integrity_core_stub import verify_integrity

def get_engine_health_summary() -> dict:
    l1_ok, l1_issues = verify_integrity()

    return {
        "overall_ok": l1_ok,
        "checked_at": "AUTO_FILL_AT_RUNTIME",  # you likely already have datetime logic
        "layers": {
            "L1_integrity_core": {
                "engine_ok": l1_ok,
                "reason": l1_issues[0].reason if l1_issues else "OK",
                "files_checked": 0 if not l1_ok and not l1_issues else len(l1_issues) or len(l1_issues),
                # you can refine this field as you like
            }
        },
    }

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
