#!/usr/bin/env python3
"""Verify campaign run integrity without revealing or interpreting scores."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import random
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import aggregate  # noqa: E402


def campaign_plan(suite: dict[str, Any]) -> list[dict[str, Any]]:
    repeated = set(suite["repeat_subset"])
    rows = []
    for task in suite["tasks"]:
        for attempt in ([1, 2, 3] if task["id"] in repeated else [1]):
            for route in suite["routes"]:
                rows.append(
                    {
                        "task_id": task["id"],
                        "attempt": attempt,
                        "provider": route["provider"],
                        "requested_model": route["requested_model"],
                    }
                )
    random.Random(suite["randomization"]["seed"]).shuffle(rows)
    if len(rows) != suite["run_count"]["total"]:
        raise RuntimeError("frozen campaign plan length mismatch")
    return rows


def expected_cells(suite: dict[str, Any], scope: str) -> dict[str, dict[str, Any]]:
    rows = campaign_plan(suite)
    if scope == "canary":
        rows = [
            row
            for row in rows
            if row["task_id"] == suite["canary_task"] and row["attempt"] == 1
        ]
        if len(rows) != 6:
            raise RuntimeError("frozen canary must contain exactly six routes")
    campaign_id = suite["campaign_id"]
    output = {}
    for row in rows:
        run_id = "__".join(
            [
                campaign_id,
                row["task_id"],
                f"a{row['attempt']}",
                row["provider"],
                row["requested_model"],
            ]
        )
        output[run_id] = {"run_id": run_id, **row}
    if len(output) != len(rows):
        raise RuntimeError("duplicate frozen campaign run key")
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("runs_root", type=Path)
    parser.add_argument("--expected", type=int, required=True)
    parser.add_argument("--scope", choices=("canary", "full"))
    parser.add_argument("--allow-planned-extras", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    scope = args.scope or ({6: "canary", 360: "full"}.get(args.expected))
    if scope is None:
        raise SystemExit("--scope is required when --expected is not 6 or 360")
    suite = json.loads((ROOT / "suite.json").read_text(encoding="utf-8"))
    expected = expected_cells(suite, scope)
    if args.expected != len(expected):
        raise SystemExit(f"--expected {args.expected} disagrees with frozen {scope} count {len(expected)}")
    observed = {path.name: path for path in args.runs_root.iterdir() if path.is_dir()} if args.runs_root.is_dir() else {}
    rows = []
    for run_id in sorted(set(expected) & set(observed)):
        passed, errors, evidence = aggregate.verify_cell(
            observed[run_id],
            expected=expected[run_id],
            require_successful_canary=scope == "canary",
        )
        rows.append({"run": run_id, "passed": passed, "errors": errors, **evidence})
    missing = sorted(set(expected) - set(observed))
    extra = sorted(set(observed) - set(expected))
    unexpected_extra = extra
    if args.allow_planned_extras and scope == "canary":
        full_keys = set(expected_cells(suite, "full"))
        unexpected_extra = sorted(set(extra) - full_keys)
    report = {
        "passed": not missing and not unexpected_extra and len(rows) == args.expected and all(row["passed"] for row in rows),
        "scope": scope,
        "expected": args.expected,
        "found": len(observed),
        "missing_run_keys": missing,
        "extra_run_keys": extra,
        "unexpected_extra_run_keys": unexpected_extra,
        "runs": rows,
    }
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text)
    print(json.dumps({"passed": report["passed"], "scope": scope, "expected": args.expected, "found": len(observed), "missing": len(missing), "extra": len(extra), "unexpected_extra": len(unexpected_extra)}, sort_keys=True))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
