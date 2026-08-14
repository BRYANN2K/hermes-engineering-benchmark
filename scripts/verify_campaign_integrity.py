#!/usr/bin/env python3
"""Verify campaign run integrity without revealing or interpreting scores."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import stat
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import aggregate  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("runs_root", type=Path)
    parser.add_argument("--expected", type=int, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    rows = []
    for run in sorted(p for p in args.runs_root.iterdir() if p.is_dir()):
        sealed, error = aggregate.verify_checksums(run)
        writable = [p.relative_to(run).as_posix() for p in run.rglob("*") if p.is_file() and p.stat().st_mode & 0o222]
        manifest = json.loads((run / "manifest.json").read_text()) if (run / "manifest.json").is_file() else {}
        result = json.loads((run / "result.json").read_text()) if (run / "result.json").is_file() else {}
        usage = json.loads((run / "usage.json").read_text()) if (run / "usage.json").is_file() else {}
        trace = run / "tool-sandbox.jsonl"
        trace_lines = trace.read_text().splitlines() if trace.is_file() else []
        hook = False
        if trace_lines:
            try:
                first = json.loads(trace_lines[0]); hook = first.get("sandbox") == "hermes-tool-hook" and first.get("installed") is True
            except json.JSONDecodeError:
                pass
        row = {
            "run": run.name,
            "sealed": sealed,
            "seal_error": error,
            "writable_files": writable,
            "tool_hook_installed": hook,
            "hermes_completed": result.get("outcome", {}).get("hermes_completed"),
            "grader_completed": result.get("outcome", {}).get("grader_completed"),
            "candidate_passed": result.get("outcome", {}).get("passed"),
            "usage_completed": usage.get("completed"),
            "usage_failed": usage.get("failed"),
            "provider": manifest.get("model", {}).get("provider"),
            "requested_model": manifest.get("model", {}).get("requested_id"),
        }
        row["passed"] = bool(sealed and not writable and hook and row["grader_completed"] and usage)
        rows.append(row)
    report = {"passed": len(rows) == args.expected and all(x["passed"] for x in rows), "expected": args.expected, "found": len(rows), "runs": rows}
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text)
    print(json.dumps({"passed": report["passed"], "expected": args.expected, "found": len(rows)}, sort_keys=True))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
