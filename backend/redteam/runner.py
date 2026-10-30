import argparse
import json
import urllib.request


def main() -> int:
    parser = argparse.ArgumentParser(description="Replay the AgentSentinel demo scenarios.")
    parser.add_argument("--base-url", default="http://localhost:8000")
    base = parser.parse_args().base_url.rstrip("/")
    with urllib.request.urlopen(f"{base}/api/scenarios", timeout=10) as response:
        scenarios = json.loads(response.read().decode())
    matches = 0
    for scenario in scenarios:
        request = urllib.request.Request(
            f"{base}/api/demo/run/{scenario['id']}", data=b"{}",
            headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                result = json.loads(response.read().decode())
            actual = result["verdict"]
            passed = actual == scenario["expected"]
            matches += int(passed)
            print(f"{'PASS' if passed else 'CHECK'} {scenario['id']}: "
                  f"expected={scenario['expected']} actual={actual} executed={result['executed']}")
        except Exception as exc:
            print(f"ERROR {scenario['id']}: {type(exc).__name__}: {exc}")
    print(f"\nObserved scenario matches: {matches}/{len(scenarios)}")
    print("This is a scenario replay summary, not a security benchmark or general detection rate.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
