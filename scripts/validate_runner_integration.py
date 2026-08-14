#!/usr/bin/env python3
"""Validate each hidden grader through the exact runner execution path."""
from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "harness" / "runner" / "runner.py"

MOCK = '''#!/usr/bin/env python3
import json, os, pathlib, shutil, sys
args=sys.argv[1:]
usage=pathlib.Path(args[args.index("--usage-file")+1])
source=pathlib.Path(os.environ["HEB_REFERENCE_SOURCE"])
workspace=pathlib.Path.cwd()
for path in source.rglob("*"):
    if path.is_file():
        target=workspace/path.relative_to(source)
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(path,target)
usage.write_text(json.dumps({"provider":args[args.index("--provider")+1],"model":args[args.index("--model")+1],"input_tokens":1,"output_tokens":1,"total_tokens":2,"api_calls":1,"completed":True,"failed":False})+"\\n")
print("reference overlay complete")
'''


def validate_one(task_id: str, base: Path) -> dict[str, Any]:
    grader = ROOT / "private_graders" / task_id
    reference = grader / "reference_solution"
    if not reference.is_dir():
        reference = grader / "reference"
    if not reference.is_dir():
        return {"task_id": task_id, "passed": False, "error": "missing reference directory"}
    task_root = ROOT / "tasks" / task_id
    local = base / task_id
    local.mkdir()
    mock = local / "mock-hermes.py"
    mock.write_text(MOCK, encoding="utf-8")
    mock.chmod(mock.stat().st_mode | stat.S_IXUSR)
    runs = local / "runs"
    command = [
        sys.executable, str(RUNNER), "run",
        "--starter", str(task_root / "starter"),
        "--prompt-file", str(task_root / "task.md"),
        "--task-id", task_id,
        "--grader", str(grader / "grade.py"),
        "--grader-bundle-root", str(grader),
        "--provider", "openai-codex",
        "--model", "gpt-5.6-sol",
        "--runs-root", str(runs),
        "--hermes", str(mock),
        "--run-key", f"integration__{task_id}",
        "--no-tool-sandbox",
    ]
    env = os.environ.copy()
    env["HEB_REFERENCE_SOURCE"] = str(reference.resolve())
    completed = subprocess.run(command, cwd=ROOT, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=180, check=False)
    parsed = None
    try:
        parsed = json.loads(completed.stdout)
    except json.JSONDecodeError:
        pass
    passed = completed.returncode == 0 and isinstance(parsed, dict) and parsed.get("result", {}).get("outcome", {}).get("success") is True
    return {"task_id": task_id, "passed": passed, "returncode": completed.returncode, "summary": parsed, "stdout": completed.stdout if parsed is None else None, "stderr": completed.stderr}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--jobs", type=int, default=4)
    parser.add_argument("--output", type=Path, default=ROOT / "proof" / "runner-grader-integration.json")
    args = parser.parse_args()
    suite = json.loads((ROOT / "suite.json").read_text(encoding="utf-8"))
    task_ids = [task["id"] for task in suite["tasks"]]
    with tempfile.TemporaryDirectory(prefix="heb-runner-integration-") as tmp:
        base = Path(tmp)
        with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, args.jobs)) as executor:
            results = list(executor.map(lambda task_id: validate_one(task_id, base), task_ids))
    passed = len(results) == 40 and all(item["passed"] for item in results)
    report = {"schema_version": "1.0", "passed": passed, "tasks_expected": 40, "tasks_passed": sum(item["passed"] for item in results), "results": results}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"passed": passed, "tasks_expected": 40, "tasks_passed": report["tasks_passed"]}, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
