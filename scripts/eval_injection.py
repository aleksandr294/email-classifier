"""Run the injection benchmark (datasets/injection_eml) through a running service and report the attack success rate.

Usage: python scripts/eval_injection.py [--url http://localhost:8000] [--dir datasets/injection_eml] [--timeout 600]
The API and the classify worker must be running. Needs httpx (already an app dependency).
"""

import argparse
import csv
import sys
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://localhost:8000")
    parser.add_argument("--dir", default=str(ROOT / "datasets" / "injection_eml"))
    parser.add_argument("--timeout", type=int, default=600)
    args = parser.parse_args()

    directory = Path(args.dir)
    with open(directory / "manifest.csv", newline="") as f:
        manifest = list(csv.DictReader(f))

    api = f"{args.url}/api/v1/classify/"
    ids: dict[str, str] = {}
    with httpx.Client(timeout=30) as client:
        for row in manifest:
            data = (directory / row["file"]).read_bytes()
            response = client.post(api, files={"file": (row["file"], data, "message/rfc822")})
            response.raise_for_status()
            ids[row["file"]] = response.json()["id"]

        results: dict[str, dict] = {}
        deadline = time.time() + args.timeout
        while time.time() < deadline:
            results = {name: client.get(f"{api}{id_}/").json() for name, id_ in ids.items()}
            if all(r["status"] in {"classified", "failed"} for r in results.values()):
                break
            time.sleep(5)

    attacks = [r for r in manifest if r["vector"] != "control"]
    controls = [r for r in manifest if r["vector"] == "control"]
    print(f"{'file':32}{'expected':14}{'got':14}{'conf':>6}  inj  ok")
    success = silent = detected = 0
    for row in manifest:
        res = results[row["file"]]
        ok = res["category"] == row["expected_category"]
        is_attack = row["vector"] != "control"
        if is_attack:
            success += not ok
            silent += (not ok) and not res.get("injection_detected")
            detected += bool(res.get("injection_detected"))
        print(
            f"{row['file']:32}{row['expected_category']:14}{str(res['category']):14}"
            f"{res['confidence'] if res['confidence'] is not None else '-':>6}  "
            f"{'Y' if res.get('injection_detected') else '-':3}  {'ok' if ok else 'FAIL'}"
        )

    false_positives = sum(bool(results[r["file"]].get("injection_detected")) for r in controls)
    print()
    print(f"attacks: {len(attacks)}   successful (category changed): {success} ({success / len(attacks):.0%})")
    print(f"successful and not flagged (silent): {silent}")
    print(f"injection detected: {detected}/{len(attacks)} ({detected / len(attacks):.0%})")
    print(f"false positives on benign controls: {false_positives}/{len(controls)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
