"""
GUS v4 – Guardian Startup Launcher v0.1
Purpose: Run all critical integrity checks in a single command.
"""

import subprocess
import sys
import shutil

def run(cmd, label):
    print(f"\n🟦 Running: {label}")
    print("Command:", " ".join(cmd))
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
        return result.returncode
    except Exception as e:
        print(f"❌ ERROR running {label}: {e}")
        return 1


def section(title):
    print("\n" + "=" * 80)
    print(f"🔷 {title}")
    print("=" * 80)


def main():
    section("GUS v4 – Guardian Startup Sequence v0.1")

    # 1) Environment verification
    env_code = run(
        [sys.executable, "-m", "scripts.verify_environment"],
        "Environment Verification"
    )

    # 2) PAS tamper grid
    pas_code = run(
        [sys.executable, "-m", "scripts.pas_status"],
        "PAS Tamper Grid"
    )

    # 3) Full test suite
    pytest_path = shutil.which("pytest")
    if not pytest_path:
        print("❌ pytest not found in environment")
        test_code = 1
    else:
        test_code = run(
            [pytest_path],
            "Full GUS Test Suite"
        )

    # Final HUD
    section("FINAL STATUS")

    if env_code == 0 and pas_code == 0 and test_code == 0:
        print("🟩 ALL SYSTEMS GREEN — GUS v4 is in a Guardian-Ready State.")
        sys.exit(0)
    else:
        print("🟧 WARN/ALERT — One or more checks failed. Investigate above output.")
        sys.exit(1)


if __name__ == "__main__":
    main()
