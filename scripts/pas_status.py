# scripts/pas_status.py

from pas import run_all_scenarios, TamperScenarioResult

def main() -> None:
    results = run_all_scenarios()

    print("🛡  GUS v4 – PAS Tamper Grid Status\n")
    for r in results:
        ok = not r.detected  # flip: True = healthy
        status = "OK" if ok else "ALERT"
        print(f"{r.scenario_id:<8} {status:<6} {r.severity.name:<8} {r.name}")

    # Optional: overall health
    all_ok = all(not r.detected for r in results)
    print("\nOverall PAS status:", "OK ✅" if all_ok else "ALERT ⚠")

if __name__ == "__main__":
    main()
