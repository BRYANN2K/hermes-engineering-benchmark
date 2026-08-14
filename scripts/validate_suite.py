#!/usr/bin/env python3
"""Validate every task's starter/reference/known-bad contract."""
from __future__ import annotations

import argparse
import concurrent.futures
import datetime as dt
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def load_suite() -> dict[str, Any]:
    value = json.loads((ROOT / "suite.json").read_text(encoding="utf-8"))
    ids = [task["id"] for task in value["tasks"]]
    if len(ids) != 40 or len(set(ids)) != 40:
        raise RuntimeError("suite.json must contain exactly 40 unique task IDs")
    if value["run_count"] != {"primary": 240, "repeat_additional": 120, "total": 360}:
        raise RuntimeError("suite run count is not the preregistered 360")
    return value


def validate_one(task_id: str, timeout: int) -> dict[str, Any]:
    task = ROOT / "tasks" / task_id
    grader = ROOT / "private_graders" / task_id
    required = [task / "task.md", task / "starter", grader / "grade.py", grader / "validate.py"]
    missing = [str(path.relative_to(ROOT)) for path in required if not path.exists()]
    if missing:
        return {"task_id": task_id, "passed": False, "error": "missing_paths", "missing": missing}
    command = [sys.executable, str(grader / "validate.py")]
    env = os.environ.copy()
    env.update({"PYTHONDONTWRITEBYTECODE": "1", "TZ": "UTC", "LC_ALL": "C.UTF-8"})
    for key in list(env):
        if any(marker in key.upper() for marker in ("TOKEN", "SECRET", "PASSWORD", "CREDENTIAL")):
            env.pop(key, None)
    try:
        result = subprocess.run(
            command,
            cwd=ROOT,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {"task_id": task_id, "passed": False, "error": "timeout"}
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    parsed = None
    parse_error = None
    if len(lines) == 1:
        try:
            parsed = json.loads(lines[0])
        except json.JSONDecodeError as exc:
            parse_error = str(exc)
    else:
        parse_error = f"expected one stdout line, got {len(lines)}"
    return {
        "task_id": task_id,
        "passed": result.returncode == 0 and isinstance(parsed, dict) and parsed.get("passed", True) is not False,
        "returncode": result.returncode,
        "command": command,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "result": parsed,
        "parse_error": parse_error,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--jobs", type=int, default=4)
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--output", type=Path, default=ROOT / "proof" / "suite-validation.json")
    args = parser.parse_args()
    suite = load_suite()
    task_ids = [task["id"] for task in suite["tasks"]]
    results: list[dict[str, Any]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, args.jobs)) as executor:
        future_map = {executor.submit(validate_one, task_id, args.timeout): task_id for task_id in task_ids}
        for future in concurrent.futures.as_completed(future_map):
            try:
                results.append(future.result())
            except Exception as exc:
                results.append({"task_id": future_map[future], "passed": False, "error": f"{type(exc).__name__}: {exc}"})
    results.sort(key=lambda item: task_ids.index(item["task_id"]))
    passed = all(item.get("passed") is True for item in results) and len(results) == 40
    report = {
        "schema_version": "1.0",
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z"),
        "passed": passed,
        "tasks_expected": 40,
        "tasks_validated": len(results),
        "tasks_passed": sum(item.get("passed") is True for item in results),
        "results": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("passed", "tasks_expected", "tasks_validated", "tasks_passed")}, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
