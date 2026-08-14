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
import subprocess
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RUNTIME_MANIFEST = ROOT / "runtime" / "hermes-runtime-manifest.json"
GRADER_COMMITMENTS = ROOT / "proof" / "grader-commitments.json"
LANDLOCK_HELPER_HASH_FILE = ROOT / "runtime" / "sandbox" / "landlock-run.sha256"
SOURCE_FREEZE_COMMITMENT = ROOT / "proof" / "freeze-summary.json"


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


def runtime_manifest_sha256() -> str:
    return hashlib.sha256(RUNTIME_MANIFEST.read_bytes()).hexdigest()


def grader_commitment(task_id: str) -> str | None:
    payload = load(GRADER_COMMITMENTS)
    matches = [row.get("sha256") for row in payload.get("commitments", []) if row.get("task_id") == task_id]
    return matches[0] if len(matches) == 1 else None


def verify_cognitive_trace(path: Path) -> tuple[bool, str | None, int]:
    try:
        records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    except (OSError, json.JSONDecodeError) as exc:
        return False, f"invalid tool-sandbox trace: {exc}", 0
    if not records:
        return False, "empty tool-sandbox trace", 0
    first = records[0]
    if not (
        first.get("sandbox") == "hermes-tool-hook"
        and first.get("installed") is True
        and first.get("cognitive_isolation_installed") is True
        and first.get("ephemeral_home") is True
        and first.get("shared_credentials_host_only") is True
    ):
        return False, "invalid Hermes tool-hook attestation", 0
    cognitive = [record for record in records if record.get("sandbox") == "hermes-cognitive-isolation"]
    if len(cognitive) != 1:
        return False, f"expected exactly one cognitive-isolation attestation, found {len(cognitive)}", len(cognitive)
    marker = cognitive[0]
    if not (
        marker.get("applied") is True
        and marker.get("skip_memory") is True
        and marker.get("skip_context_files") is True
        and marker.get("load_soul_identity") is False
        and marker.get("fallback_disabled") is True
    ):
        return False, "invalid cognitive-isolation flags", 1
    unexpected = [
        record
        for record in records[1:]
        if record.get("sandbox") != "hermes-cognitive-isolation"
        and record != {"sandbox": "landlock-seccomp-netns", "activated": True}
        and not (
            record.get("sandbox") == "hermes-tool-hook"
            and record.get("installed") is True
            and record.get("cognitive_isolation_installed") is True
        )
    ]
    if unexpected:
        return False, "unexpected tool-sandbox trace record", 1
    return True, None, 1


def verify_cell(
    run: Path,
    *,
    expected: dict[str, Any] | None = None,
    require_successful_canary: bool = False,
) -> tuple[bool, list[str], dict[str, Any]]:
    errors: list[str] = []
    sealed, seal_error = verify_checksums(run)
    if not sealed:
        errors.append(seal_error or "sealed artifact verification failed")
    writable = (["."] if run.stat().st_mode & 0o222 else []) + [
        path.relative_to(run).as_posix()
        for path in run.rglob("*")
        if path.stat().st_mode & 0o222
    ]
    if writable:
        errors.append(f"writable sealed files: {writable}")
    if (run / ".hermes-home").exists():
        errors.append("ephemeral Hermes home survived sealing")
    try:
        manifest = load(run / "manifest.json")
        request = load(run / "request.json")
        result = load(run / "result.json")
        usage = load(run / "usage.json")
        timing = load(run / "timing.json")
        exit_status = load(run / "exit_status.json")
    except (OSError, json.JSONDecodeError, TypeError) as exc:
        return False, errors + [f"invalid required JSON artifact: {exc}"], {}

    hermes = manifest.get("hermes", {})
    benchmark_freeze = manifest.get("benchmark_freeze", {})
    task = manifest.get("task", {})
    result_model = result.get("model", {})
    result_task = result.get("task", {})
    identity = {
        "run_id": run.name,
        "task_id": task.get("task_id"),
        "attempt": task.get("attempt"),
        "provider": hermes.get("provider"),
        "requested_model": hermes.get("model"),
    }
    if manifest.get("run_id") != run.name or result.get("run_id") != run.name:
        errors.append("run identity mismatch")
    if (
        request.get("task_id") != identity["task_id"]
        or request.get("attempt") != identity["attempt"]
        or request.get("provider") != identity["provider"]
        or request.get("model") != identity["requested_model"]
        or result_task.get("task_id") != identity["task_id"]
        or result_task.get("attempt") != identity["attempt"]
        or result_model.get("provider") != identity["provider"]
        or result_model.get("requested_id") != identity["requested_model"]
    ):
        errors.append("request/manifest/result experimental identity mismatch")
    if expected is not None and any(identity.get(key) != value for key, value in expected.items()):
        errors.append("run does not match frozen experimental cell")

    expected_runtime = runtime_manifest_sha256()
    if (
        hermes.get("runtime_verification") != "verified"
        or hermes.get("runtime_manifest_sha256") != expected_runtime
        or request.get("hermes_runtime_manifest_sha256") != expected_runtime
    ):
        errors.append("external Hermes runtime fingerprint mismatch")
    expected_source = load(SOURCE_FREEZE_COMMITMENT)
    if (
        benchmark_freeze.get("status") != "verified"
        or benchmark_freeze.get("source_tree_sha256") != expected_source.get("source_tree_sha256")
        or benchmark_freeze.get("file_count") != expected_source.get("file_count")
        or request.get("benchmark_source_tree_sha256") != expected_source.get("source_tree_sha256")
        or request.get("benchmark_source_file_count") != expected_source.get("file_count")
    ):
        errors.append("benchmark source freeze mismatch")
    grader = manifest.get("grader", {})
    expected_grader = grader_commitment(str(identity["task_id"])) if identity["task_id"] is not None else None
    if (
        expected_grader is None
        or grader.get("bundle_sha256") != expected_grader
        or request.get("grader_bundle_sha256") != expected_grader
        or grader.get("sha256") != request.get("grader_sha256")
    ):
        errors.append("grader bundle commitment mismatch")
    environment = manifest.get("environment", {})
    agent_sandbox = environment.get("agent_tool_sandbox", {})
    grader_sandbox = environment.get("grader_sandbox", {})
    expected_landlock = LANDLOCK_HELPER_HASH_FILE.read_text(encoding="ascii").strip()
    if (
        environment.get("HERMES_HOME") != "ephemeral-per-run"
        or agent_sandbox.get("enabled") is not True
        or agent_sandbox.get("landlock_helper_sha256") != expected_landlock
        or request.get("landlock_helper_sha256") != expected_landlock
    ):
        errors.append("agent sandbox or ephemeral-home policy mismatch")
    if grader_sandbox.get("enabled") is not True:
        errors.append("grader sandbox policy mismatch")
    trace_ok, trace_error, cognitive_count = verify_cognitive_trace(run / "tool-sandbox.jsonl")
    if not trace_ok:
        errors.append(trace_error or "cognitive trace verification failed")

    outcome = result.get("outcome", {})
    if outcome.get("tool_sandbox_verified") is not True:
        errors.append("runner did not verify tool sandbox")
    if not isinstance(usage, dict) or "failed" not in usage:
        errors.append("usage telemetry is incomplete")
    if not isinstance(timing.get("hermes"), dict) or not isinstance(exit_status.get("hermes"), dict):
        errors.append("Hermes timing or exit telemetry is incomplete")
    if not isinstance(timing.get("grader"), dict) or not isinstance(exit_status.get("grader"), dict):
        errors.append("grader timing or exit telemetry is incomplete")
    if require_successful_canary and not (
        outcome.get("hermes_completed") is True
        and outcome.get("grader_completed") is True
        and usage.get("completed") is True
        and usage.get("failed") is False
        and exit_status.get("hermes", {}).get("return_code") == 0
        and exit_status.get("hermes", {}).get("timed_out") is False
        and exit_status.get("grader", {}).get("return_code") in (0, 1)
        and exit_status.get("grader", {}).get("timed_out") is False
    ):
        errors.append("canary route, agent, grader, or telemetry did not complete successfully")
    evidence = {
        **identity,
        "sealed": sealed,
        "writable_files": writable,
        "runtime_verified": hermes.get("runtime_verification") == "verified",
        "cognitive_attestations": cognitive_count,
        "tool_sandbox_verified": outcome.get("tool_sandbox_verified"),
        "hermes_completed": outcome.get("hermes_completed"),
        "grader_completed": outcome.get("grader_completed"),
        "candidate_passed": outcome.get("passed"),
        "usage_completed": usage.get("completed"),
        "usage_failed": usage.get("failed"),
    }
    return not errors, errors, evidence


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
    verified, integrity_errors, _evidence = verify_cell(run)
    manifest = load(run / "manifest.json")
    result = load(run / "result.json")
    usage = load(run / "usage.json")
    timing = load(run / "timing.json")
    task = manifest["task"]
    model = manifest["hermes"]
    model_id = model["model"]
    price = pricing["models"][model_id]
    api_cost = equivalent_cost(usage, price)
    cost_status = usage.get("cost_status")
    # Included, unknown and locally priced estimates are not evidence of a billed amount.
    actual_cost = usage.get("actual_cost_usd") if cost_status == "billed" else None
    provider_estimate = usage.get("estimated_cost_usd") if cost_status == "priced" else None
    trace = run / "tool-sandbox.jsonl"
    sandboxed_tool_invocations = 0
    if trace.is_file():
        sandboxed_tool_invocations = sum(
            1
            for line in trace.read_text(encoding="utf-8").splitlines()
            if line and json.loads(line).get("sandbox") == "landlock-seccomp-netns"
        )
    return {
        "run_id": manifest["run_id"],
        "task_id": task["task_id"],
        "attempt": task["attempt"],
        "provider": model["provider"],
        "requested_model": model_id,
        "resolved": verified and result.get("outcome", {}).get("success") is True,
        "score": result.get("outcome", {}).get("score"),
        "hermes_completed": result.get("outcome", {}).get("hermes_completed") is True,
        "grader_completed": result.get("outcome", {}).get("grader_completed") is True,
        "artifact_verified": verified,
        "artifact_error": "; ".join(integrity_errors) if integrity_errors else None,
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
        "provider_reported_estimated_cost_usd": provider_estimate,
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
    if not args.allow_partial:
        integrity = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "verify_campaign_integrity.py"),
                str(args.runs_root),
                "--expected", str(suite["run_count"]["total"]),
                "--scope", "full",
            ],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if integrity.returncode != 0:
            detail = (integrity.stdout + integrity.stderr).strip()
            print(json.dumps({"complete": False, "error": f"campaign integrity failed: {detail}"}, sort_keys=True))
            return 1
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
