#!/usr/bin/env python3
"""Verify sealed run artifacts and derive machine-readable benchmark metrics."""
from __future__ import annotations

import argparse
import csv
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import statistics
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def verify_checksums(run: Path) -> tuple[bool, str | None]:
    checksums = run / "checksums.sha256"
    marker = run / "COMPLETE"
    if not checksums.is_file() or not marker.is_file():
        return False, "missing COMPLETE or checksums.sha256"
    declared = set()
    for line in checksums.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            expected, relative = line.split("  ", 1)
        except ValueError:
            return False, f"invalid checksum line: {line!r}"
        if relative in declared:
            return False, f"duplicate checksum entry: {relative}"
        declared.add(relative)
        path = run / relative
        if not path.is_file():
            return False, f"missing checksummed file: {relative}"
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            return False, f"checksum mismatch: {relative}"
    excluded = {"checksums.sha256", "COMPLETE", ".runner.lock"}
    observed = {
        path.relative_to(run).as_posix()
        for path in run.rglob("*")
        if path.is_file() and path.name not in excluded
    }
    if observed != declared:
        return False, f"artifact inventory mismatch: extra={sorted(observed-declared)}, missing={sorted(declared-observed)}"
    complete = load(marker)
    if complete.get("checksums_sha256") != hashlib.sha256(checksums.read_bytes()).hexdigest():
        return False, "COMPLETE does not match checksums.sha256"
    return True, None


def money(value: Any) -> Decimal:
    return Decimal(str(value or 0))


def equivalent_cost(usage: dict[str, Any], price: dict[str, Any]) -> Decimal:
    return (
        money(usage.get("input_tokens")) * money(price["input"])
        + money(usage.get("cache_read_tokens")) * money(price["cached_input"])
        + money(usage.get("cache_write_tokens")) * money(price.get("cache_write"))
        + money(usage.get("output_tokens")) * money(price["output"])
    ) / Decimal(1_000_000)


def row(run: Path, pricing: dict[str, Any]) -> dict[str, Any]:
    verified, error = verify_checksums(run)
    manifest = load(run / "manifest.json")
    result = load(run / "result.json")
    usage = load(run / "usage.json")
    timing = load(run / "timing.json")
    task = manifest["task"]
    model = manifest["model"]
    model_id = model["requested_id"]
    price = pricing["models"][model_id]
    api_cost = equivalent_cost(usage, price)
    cost_status = usage.get("cost_status")
    # "included" and "unknown" are not evidence of a billed dollar amount.
    actual_cost = usage.get("estimated_cost_usd") if cost_status == "priced" else None
    trace = run / "tool-sandbox.jsonl"
    sandboxed_tool_invocations = max(0, len(trace.read_text(encoding="utf-8").splitlines()) - 1) if trace.is_file() else 0
    return {
        "run_id": manifest["run_id"],
        "task_id": task["task_id"],
        "attempt": task["attempt"],
        "provider": model["provider"],
        "requested_model": model_id,
        "resolved": result.get("outcome", {}).get("success") is True,
        "score": result.get("outcome", {}).get("score"),
        "hermes_completed": result.get("outcome", {}).get("hermes_completed") is True,
        "grader_completed": result.get("outcome", {}).get("grader_completed") is True,
        "artifact_verified": verified,
        "artifact_error": error,
        "input_tokens": usage.get("input_tokens"),
        "cache_read_tokens": usage.get("cache_read_tokens"),
        "cache_write_tokens": usage.get("cache_write_tokens"),
        "output_tokens": usage.get("output_tokens"),
        "reasoning_tokens": usage.get("reasoning_tokens"),
        "total_tokens": usage.get("total_tokens"),
        "api_calls": usage.get("api_calls"),
        "sandboxed_tool_invocations": sandboxed_tool_invocations,
        "wall_seconds": timing.get("hermes", {}).get("wall_seconds"),
        "actual_cost_usd": actual_cost,
        "actual_cost_status": cost_status,
        "api_equivalent_cost_usd": float(api_cost),
    }


def aggregate(rows: list[dict[str, Any]], suite: dict[str, Any]) -> list[dict[str, Any]]:
    primary = [item for item in rows if item["attempt"] == 1]
    output = []
    for route in suite["routes"]:
        selected = [item for item in primary if item["provider"] == route["provider"] and item["requested_model"] == route["requested_model"]]
        resolved = sum(item["resolved"] for item in selected)
        api_cost = sum(money(item["api_equivalent_cost_usd"]) for item in selected)
        latency = [float(item["wall_seconds"]) for item in selected if item["wall_seconds"] is not None]
        repeat_ids = set(suite["repeat_subset"])
        repeated = [item for item in rows if item["task_id"] in repeat_ids and item["provider"] == route["provider"] and item["requested_model"] == route["requested_model"]]
        by_task = {task_id: [item for item in repeated if item["task_id"] == task_id] for task_id in repeat_ids}
        all_three = sum(len(items) == 3 and all(item["resolved"] for item in items) for items in by_task.values())
        ordered_latency = sorted(latency)
        p95_index = max(0, int((len(ordered_latency) - 1) * 0.95)) if ordered_latency else 0
        output.append({
            "route_id": f"{route['provider']}/{route['requested_model']}",
            "provider": route["provider"],
            "requested_model": route["requested_model"],
            "underlying_model": route["underlying_model"],
            "primary_runs": len(selected),
            "resolved_tasks": resolved,
            "resolved_rate": resolved / len(selected) if selected else None,
            "api_equivalent_cost_usd": float(api_cost),
            "cost_per_resolved_task_usd": float(api_cost / resolved) if resolved else None,
            "median_wall_seconds": statistics.median(latency) if latency else None,
            "p95_wall_seconds_nearest_rank": ordered_latency[p95_index] if ordered_latency else None,
            "mean_api_calls": statistics.mean(item["api_calls"] for item in selected if item["api_calls"] is not None) if selected else None,
            "mean_sandboxed_tool_invocations": statistics.mean(item["sandboxed_tool_invocations"] for item in selected) if selected else None,
            "repeat_subset_all_three_resolved": all_three,
            "repeat_subset_consistency_rate": all_three / len(repeat_ids) if repeat_ids else None,
            "agent_completion_rate": sum(item["hermes_completed"] for item in selected) / len(selected) if selected else None,
            "grader_completion_rate": sum(item["grader_completed"] for item in selected) / len(selected) if selected else None,
            "provider_error_rate": sum(not item["hermes_completed"] for item in selected) / len(selected) if selected else None,
        })
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs-root", type=Path, default=ROOT / "runs" / load(ROOT / "suite.json")["campaign_id"])
    parser.add_argument("--allow-partial", action="store_true")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "results")
    args = parser.parse_args()
    suite = load(ROOT / "suite.json")
    pricing = load(ROOT / "pricing" / "official-pricing-2026-08-13.json")
    run_dirs = sorted(path for path in args.runs_root.iterdir() if path.is_dir()) if args.runs_root.is_dir() else []
    rows = []
    errors = []
    for run in run_dirs:
        try:
            item = row(run, pricing)
            rows.append(item)
            if not item["artifact_verified"]:
                errors.append(f"{run.name}: {item['artifact_error']}")
        except Exception as exc:
            errors.append(f"{run.name}: {type(exc).__name__}: {exc}")
    expected = suite["run_count"]["total"]
    if len(rows) != expected and not args.allow_partial:
        errors.append(f"expected {expected} complete runs, found {len(rows)}")
    duplicate_keys = len(rows) - len({(item["task_id"], item["attempt"], item["provider"], item["requested_model"]) for item in rows})
    if duplicate_keys:
        errors.append(f"duplicate experimental cells: {duplicate_keys}")
    summary = {
        "schema_version": "1.0",
        "complete": len(rows) == expected and not errors,
        "expected_runs": expected,
        "observed_runs": len(rows),
        "verified_runs": sum(item["artifact_verified"] for item in rows),
        "errors": errors,
        "leaderboard_scope": "attempt=1 only (40 tasks per route)",
        "repeat_scope": "attempts 2 and 3 on preregistered 10-task subset; excluded from leaderboard",
        "routes": aggregate(rows, suite),
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0]) if rows else ["run_id"]
    with (args.output_dir / "runs.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader(); writer.writerows(rows)
    (args.output_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"complete": summary["complete"], "expected_runs": expected, "observed_runs": len(rows), "verified_runs": summary["verified_runs"], "errors": len(errors)}, sort_keys=True))
    return 0 if summary["complete"] or args.allow_partial else 1


if __name__ == "__main__":
    raise SystemExit(main())
