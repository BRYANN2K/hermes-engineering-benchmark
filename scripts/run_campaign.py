#!/usr/bin/env python3
"""Execute the frozen 360-run campaign in preregistered order."""
from __future__ import annotations

import argparse
import concurrent.futures
import json
from pathlib import Path
import random
import subprocess
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "harness" / "runner" / "runner.py"
FREEZE = ROOT / "scripts" / "freeze.py"


def load_suite() -> dict[str, Any]:
    return json.loads((ROOT / "suite.json").read_text(encoding="utf-8"))


def plan(suite: dict[str, Any]) -> list[dict[str, Any]]:
    repeat = set(suite["repeat_subset"])
    items = []
    for task in suite["tasks"]:
        attempts = [1, 2, 3] if task["id"] in repeat else [1]
        for attempt in attempts:
            for route in suite["routes"]:
                items.append({"task_id": task["id"], "attempt": attempt, **route})
    random.Random(suite["randomization"]["seed"]).shuffle(items)
    if len(items) != suite["run_count"]["total"] or len(items) != 360:
        raise RuntimeError(f"campaign plan must contain exactly 360 runs, got {len(items)}")
    return items


def command(item: dict[str, Any], runs_root: Path, *, resume: bool) -> list[str]:
    task_id = item["task_id"]
    grader = ROOT / "private_graders" / task_id
    campaign_id = load_suite()["campaign_id"]
    run_key = "__".join(
        [campaign_id, task_id, f"a{item['attempt']}", item["provider"], item["requested_model"]]
    )
    output = [
        sys.executable,
        str(RUNNER),
        "run",
        "--starter", str(ROOT / "tasks" / task_id / "starter"),
        "--prompt-file", str(ROOT / "tasks" / task_id / "task.md"),
        "--task-id", task_id,
        "--grader", str(grader / "grade.py"),
        "--grader-bundle-root", str(grader),
        "--provider", item["provider"],
        "--model", item["requested_model"],
        "--attempt", str(item["attempt"]),
        "--runs-root", str(runs_root),
        "--run-key", run_key,
        "--reasoning", "high",
        "--toolsets", "terminal,file",
        "--timeout", "1800",
        "--grader-timeout", "300",
        "--max-turns", "90",
    ]
    if resume:
        output.append("--resume")
    return output


def run_item(index: int, item: dict[str, Any], runs_root: Path, resume: bool) -> dict[str, Any]:
    cmd = command(item, runs_root, resume=resume)
    completed = subprocess.run(cmd, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    parsed = None
    try:
        parsed = json.loads(completed.stdout)
    except json.JSONDecodeError:
        pass
    return {
        "index": index,
        "task_id": item["task_id"],
        "attempt": item["attempt"],
        "provider": item["provider"],
        "requested_model": item["requested_model"],
        "returncode": completed.returncode,
        "summary": parsed,
        "stdout": completed.stdout if parsed is None else None,
        "stderr": completed.stderr,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs-root", type=Path, default=ROOT / "runs" / load_suite()["campaign_id"])
    parser.add_argument("--jobs", type=int, default=3)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--start-index", type=int, default=0)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--summary", type=Path, default=ROOT / "proof" / "campaign-driver-summary.json")
    args = parser.parse_args()
    if args.jobs < 1 or args.jobs > 6:
        raise SystemExit("--jobs must be between 1 and 6")
    freeze = subprocess.run(
        [sys.executable, str(FREEZE), "verify"],
        cwd=ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if freeze.returncode != 0:
        detail = (freeze.stdout + freeze.stderr).strip()
        raise SystemExit(f"source freeze verification failed; refusing campaign execution: {detail}")
    suite = load_suite()
    full_plan = plan(suite)
    selected = list(enumerate(full_plan))[args.start_index:]
    if args.limit is not None:
        selected = selected[:args.limit]
    if args.dry_run:
        value = {"schema_version": "1.0", "full_run_count": len(full_plan), "selected_run_count": len(selected), "runs": [{"index": i, **item, "command": command(item, args.runs_root, resume=args.resume)} for i, item in selected]}
        print(json.dumps(value, indent=2, sort_keys=True))
        return 0
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.jobs) as executor:
        futures = {executor.submit(run_item, i, item, args.runs_root, args.resume): i for i, item in selected}
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            results.append(result)
            print(json.dumps({key: result[key] for key in ("index", "task_id", "attempt", "provider", "requested_model", "returncode")}, sort_keys=True), flush=True)
    results.sort(key=lambda item: item["index"])
    report = {"schema_version": "1.0", "full_run_count": len(full_plan), "selected_run_count": len(selected), "completed": len(results), "failed_driver_commands": sum(item["returncode"] != 0 for item in results), "results": results}
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0 if report["failed_driver_commands"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
