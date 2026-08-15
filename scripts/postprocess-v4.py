#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import random
import statistics
import subprocess
import tempfile
from collections import Counter
from pathlib import Path

ALIASES = {
    "openai-codex/gpt-5.6-sol": "Sol",
    "openai-codex/gpt-daybreak-blue-latest": "Daybreak Blue",
    "openai-codex/gpt-5.6-terra": "Terra",
    "openai-codex/gpt-5.6-luna": "Luna",
    "opencode-go/deepseek-v4-flash": "DeepSeek V4 Flash",
    "opencode-go/deepseek-v4-pro": "DeepSeek V4 Pro",
}
REPO = Path("/opt/data/benchmarks/hermes-engineering-bench/repo")
EXPECTED_SOURCE_TREE_SHA256 = "ee3327ff74001ae79175c7b103ebcf88b61b2797d3d966aeacf4efac38d13d6f"
COLORS = ["#a78bfa", "#60a5fa", "#34d399", "#f59e0b", "#f472b6", "#22d3ee"]
DEFAULT_SUITE = REPO / "suite.json"
DEFAULT_INCIDENT = Path("/opt/data/benchmarks/hermes-engineering-bench/incidents/20260814T184812Z-frozen-proof-plan-stale.json")
DEFAULT_DERIVED_PLAN = Path("/opt/data/benchmarks/hermes-engineering-bench/derived/campaign-plan-v4-from-frozen-suite.json")
DEFAULT_RUNS_ROOT = REPO / "runs" / "campaign-20260814-v4"
ENVIRONMENT_INCIDENT = Path("/opt/data/benchmarks/hermes-engineering-bench/incidents/20260814T195436Z-inherited-dashboard-username-environment.json")
ENVIRONMENT_FINAL_SCAN = Path("/opt/data/benchmarks/hermes-engineering-bench/incidents/20260814-final-environment-scan.json")
ENVIRONMENT_SCANNER = Path("/opt/data/benchmarks/v4-final-environment-scan.py")
INTERRUPTION_INCIDENTS = (
    Path("/opt/data/benchmarks/hermes-engineering-bench/abandoned-runs/20260814T133927Z-campaign-20260814-v4-driver-interrupted/interruption.json"),
    Path("/opt/data/benchmarks/hermes-engineering-bench/abandoned-runs/20260814T185347Z-campaign-20260814-v4-driver-interrupted-2/interruption.json"),
)
PROVIDER_INCIDENTS = (
    Path("/opt/data/benchmarks/hermes-engineering-bench/abandoned-runs/20260814T194642Z-campaign-20260814-v4-daybreak-route-rejected/incident.json"),
)
EXPECTED_COLUMNS = {
    "run_id", "task_id", "attempt", "provider", "requested_model", "resolved", "score",
    "hermes_completed", "grader_completed", "artifact_verified", "artifact_error", "input_tokens",
    "cache_read_tokens", "cache_write_tokens", "output_tokens", "reasoning_tokens", "total_tokens",
    "api_calls", "sandboxed_tool_invocations", "wall_seconds", "actual_cost_usd", "actual_cost_status",
    "provider_reported_estimated_cost_usd", "api_equivalent_cost_usd",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def num(value: str | None, *, nonnegative: bool = False) -> float | None:
    if value in (None, "", "None"):
        return None
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"non-finite numeric value: {value}")
    if nonnegative and result < 0:
        raise ValueError(f"negative numeric value: {value}")
    return result


def boolean(value: str) -> bool:
    if value == "True":
        return True
    if value == "False":
        return False
    raise ValueError(f"invalid boolean: {value!r}")


def load_suite(path: Path) -> dict:
    if path.is_symlink() or not path.is_file():
        raise ValueError("suite.json must be a regular file")
    suite = json.loads(path.read_text(encoding="utf-8"))
    if suite.get("campaign_id") != "campaign-20260814-v4":
        raise ValueError("unexpected campaign ID in suite")
    tasks = [row.get("id") for row in suite.get("tasks", [])]
    repeats = suite.get("repeat_subset")
    routes = suite.get("routes")
    if (
        len(tasks) != 40 or len(set(tasks)) != 40
        or not isinstance(repeats, list) or len(repeats) != 10 or len(set(repeats)) != 10
        or not set(repeats) <= set(tasks)
        or not isinstance(routes, list) or len(routes) != 6
        or len({(row.get("provider"), row.get("requested_model")) for row in routes}) != 6
        or suite.get("run_count", {}).get("total") != 360
    ):
        raise ValueError("suite inventory differs from the frozen 40-task / 10-repeat / six-route contract")
    return suite


def expected_ordered_identities(suite: dict) -> list[tuple[str, int, str, str]]:
    repeated = set(suite["repeat_subset"])
    rows = [
        (task["id"], attempt, route["provider"], route["requested_model"])
        for task in suite["tasks"]
        for attempt in ([1, 2, 3] if task["id"] in repeated else [1])
        for route in suite["routes"]
    ]
    random.Random(suite["randomization"]["seed"]).shuffle(rows)
    return rows


def expected_identities(suite: dict) -> set[tuple[str, int, str, str]]:
    return set(expected_ordered_identities(suite))


def load_inputs(results: Path, suite: dict) -> tuple[dict, list[dict]]:
    summary_path = results / "summary.json"
    runs_path = results / "runs.csv"
    if summary_path.is_symlink() or runs_path.is_symlink() or not summary_path.is_file() or not runs_path.is_file():
        raise ValueError("summary.json and runs.csv must be regular files")
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    with runs_path.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames is None or set(reader.fieldnames) != EXPECTED_COLUMNS or len(reader.fieldnames) != len(EXPECTED_COLUMNS):
            raise ValueError("runs.csv columns differ from the frozen aggregate contract")
        rows = list(reader)
    if summary.get("complete") is not True or summary.get("expected_runs") != 360 or summary.get("observed_runs") != 360 or summary.get("verified_runs") != 360 or summary.get("errors") != []:
        raise ValueError("refusing to publish an incomplete or invalid campaign summary")
    if len(rows) != 360 or len(summary.get("routes", [])) != 6:
        raise ValueError("campaign inventory differs from 360 runs / six routes")
    if any(not boolean(row["artifact_verified"]) or row.get("artifact_error") not in ("", None) for row in rows):
        raise ValueError("runs.csv contains an unverified artifact")
    identities = []
    numeric_columns = (
        "input_tokens", "cache_read_tokens", "cache_write_tokens", "output_tokens", "reasoning_tokens",
        "total_tokens", "api_calls", "sandboxed_tool_invocations", "wall_seconds", "actual_cost_usd",
        "provider_reported_estimated_cost_usd", "api_equivalent_cost_usd",
    )
    integer_columns = (
        "input_tokens", "cache_read_tokens", "cache_write_tokens", "output_tokens", "reasoning_tokens",
        "total_tokens", "api_calls", "sandboxed_tool_invocations",
    )
    for row in rows:
        try:
            attempt = int(row["attempt"])
        except (TypeError, ValueError) as exc:
            raise ValueError("runs.csv contains an invalid attempt") from exc
        if str(attempt) != row["attempt"] or attempt not in (1, 2, 3):
            raise ValueError("runs.csv contains a non-canonical attempt")
        identity = (row["task_id"], attempt, row["provider"], row["requested_model"])
        expected_run_id = "__".join((suite["campaign_id"], row["task_id"], f"a{attempt}", row["provider"], row["requested_model"]))
        if row["run_id"] != expected_run_id:
            raise ValueError("runs.csv contains a run ID inconsistent with its experimental identity")
        for column in numeric_columns:
            num(row[column], nonnegative=True)
        for column in integer_columns:
            if row[column] not in ("", "None") and (not row[column].isdigit() or int(row[column]) < 0):
                raise ValueError(f"runs.csv contains a non-canonical nonnegative integer in {column}")
        for column in ("resolved", "hermes_completed", "grader_completed", "artifact_verified"):
            boolean(row[column])
        status = row["actual_cost_status"]
        if status == "":
            unavailable_columns = (
                "input_tokens", "cache_read_tokens", "cache_write_tokens", "output_tokens",
                "reasoning_tokens", "total_tokens", "actual_cost_usd",
                "provider_reported_estimated_cost_usd",
            )
            if any(row[column] not in ("", "None") for column in unavailable_columns):
                raise ValueError("usage-unavailable run contains partial token or provider-cost telemetry")
            if num(row["api_equivalent_cost_usd"], nonnegative=True) != 0 or (num(row["api_calls"], nonnegative=True) or 0) < 1:
                raise ValueError("usage-unavailable run must retain calls and the frozen zero placeholder")
            row["actual_cost_status"] = "usage_unavailable"
            status = "usage_unavailable"
        if status not in {"billed", "included", "unknown", "priced"}:
            if status != "usage_unavailable":
                raise ValueError("runs.csv contains an invalid actual-cost status")
        if (status == "billed") != (row["actual_cost_usd"] not in ("", "None")):
            raise ValueError("actual billed cost presence disagrees with actual-cost status")
        if (status == "priced") != (row["provider_reported_estimated_cost_usd"] not in ("", "None")):
            raise ValueError("provider estimate presence disagrees with actual-cost status")
        if row["api_equivalent_cost_usd"] in ("", "None"):
            raise ValueError("API-equivalent cost is required for every run")
        identities.append(identity)
    if len(set(identities)) != 360 or set(identities) != expected_identities(suite):
        raise ValueError("runs.csv identities differ from the exact frozen suite plan")
    return summary, rows


def audit_summary(summary: dict, rows: list[dict], suite: dict) -> None:
    primary = [row for row in rows if int(row["attempt"]) == 1]
    if len(primary) != 240:
        raise ValueError("primary inventory differs from 240")
    expected_route_ids = {
        f"{route['provider']}/{route['requested_model']}" for route in suite["routes"]
    }
    if {route.get("route_id") for route in summary["routes"]} != expected_route_ids:
        raise ValueError("summary route identities differ from the frozen suite")
    repeat_ids = set(suite["repeat_subset"])
    for route in summary["routes"]:
        provider, model = route["route_id"].split("/", 1)
        if route.get("provider") != provider or route.get("requested_model") != model:
            raise ValueError(f"summary route metadata differs: {route['route_id']}")
        selected = [row for row in primary if row["provider"] == provider and row["requested_model"] == model]
        if len(selected) != 40:
            raise ValueError(f"route primary inventory differs: {route['route_id']}")
        resolved = sum(boolean(row["resolved"]) for row in selected)
        cost = sum(num(row["api_equivalent_cost_usd"], nonnegative=True) or 0 for row in selected)
        latency = [num(row["wall_seconds"], nonnegative=True) for row in selected if num(row["wall_seconds"], nonnegative=True) is not None]
        ordered_latency = sorted(latency)
        p95_index = max(0, int((len(ordered_latency) - 1) * 0.95))
        repeated = [
            row for row in rows
            if row["task_id"] in repeat_ids and row["provider"] == provider and row["requested_model"] == model
        ]
        by_task = {task_id: [row for row in repeated if row["task_id"] == task_id] for task_id in repeat_ids}
        all_three = sum(len(items) == 3 and all(boolean(item["resolved"]) for item in items) for items in by_task.values())
        api_calls = [num(row["api_calls"], nonnegative=True) for row in selected if num(row["api_calls"], nonnegative=True) is not None]
        tool_calls = [num(row["sandboxed_tool_invocations"], nonnegative=True) for row in selected]
        if not latency or not api_calls or any(value is None for value in tool_calls):
            raise ValueError(f"summary source telemetry is incomplete: {route['route_id']}")
        checks = {
            "primary_runs": 40,
            "resolved_tasks": resolved,
            "resolved_rate": resolved / 40,
            "api_equivalent_cost_usd": cost,
            "cost_per_resolved_task_usd": cost / resolved if resolved else None,
            "median_wall_seconds": statistics.median(latency),
            "p95_wall_seconds_nearest_rank": ordered_latency[p95_index],
            "mean_api_calls": statistics.mean(value for value in api_calls if value is not None),
            "mean_sandboxed_tool_invocations": statistics.mean(value for value in tool_calls if value is not None),
            "repeat_subset_all_three_resolved": all_three,
            "repeat_subset_consistency_rate": all_three / 10,
            "agent_completion_rate": sum(boolean(row["hermes_completed"]) for row in selected) / 40,
            "grader_completion_rate": sum(boolean(row["grader_completed"]) for row in selected) / 40,
            "provider_error_rate": sum(not boolean(row["hermes_completed"]) for row in selected) / 40,
        }
        for key, expected in checks.items():
            observed = route.get(key)
            if expected is None:
                if observed is not None:
                    raise ValueError(f"summary audit differs at {route['route_id']}/{key}")
            elif isinstance(expected, float):
                if observed is None or not math.isfinite(float(observed)) or not math.isclose(float(observed), expected, rel_tol=1e-9, abs_tol=1e-9):
                    raise ValueError(f"summary audit differs at {route['route_id']}/{key}")
            elif observed != expected:
                raise ValueError(f"summary audit differs at {route['route_id']}/{key}")


def annotate_cost_coverage(summary: dict, rows: list[dict]) -> None:
    primary = [row for row in rows if int(row["attempt"]) == 1]
    for route in summary["routes"]:
        provider, model = route["route_id"].split("/", 1)
        selected = [row for row in primary if row["provider"] == provider and row["requested_model"] == model]
        available = [row for row in selected if row["actual_cost_status"] != "usage_unavailable"]
        if not available:
            raise ValueError(f"no API-equivalent cost coverage for {route['route_id']}")
        observed_total = sum(num(row["api_equivalent_cost_usd"], nonnegative=True) or 0 for row in available)
        if not math.isclose(observed_total, float(route["api_equivalent_cost_usd"]), rel_tol=1e-9, abs_tol=1e-9):
            raise ValueError(f"cost placeholder mismatch for {route['route_id']}")
        route["api_equivalent_cost_primary_coverage"] = len(available)
        route["api_equivalent_cost_observed_total_usd"] = observed_total
        route["api_equivalent_cost_mean_observed_usd"] = observed_total / len(available)
        if len(available) != len(selected):
            route["cost_per_resolved_task_usd"] = None


def esc(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def bar_chart(title: str, routes: list[dict], key: str, formatter, higher_better: bool) -> str:
    width, height = 1100, 560
    left, top, plot_w, plot_h = 270, 100, 760, 360
    values = [float(route[key] or 0) for route in routes]
    maximum = max(values) or 1
    rows = []
    rows.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">')
    rows.append('<rect width="100%" height="100%" fill="#09090b"/><style>text{font-family:Inter,Geist,Arial,sans-serif}.label{fill:#e4e4e7;font-size:18px}.value{fill:#fafafa;font-size:17px;font-weight:700}.meta{fill:#a1a1aa;font-size:14px}.title{fill:#fafafa;font-size:28px;font-weight:750}</style>')
    rows.append(f'<text x="40" y="50" class="title">{esc(title)}</text>')
    rows.append(f'<text x="40" y="76" class="meta">LLM Engineering Benchmark · campaign-20260814-v4 · {"higher" if higher_better else "lower"} is better</text>')
    bar_h, gap = 42, 18
    for index, (route, value) in enumerate(zip(routes, values)):
        y = top + index * (bar_h + gap)
        name = ALIASES.get(route["route_id"], route["route_id"])
        bar_w = max(2, plot_w * value / maximum)
        rows.append(f'<text x="40" y="{y + 28}" class="label">{esc(name)}</text>')
        rows.append(f'<rect x="{left}" y="{y}" width="{plot_w}" height="{bar_h}" rx="10" fill="#18181b"/>')
        rows.append(f'<rect x="{left}" y="{y}" width="{bar_w:.2f}" height="{bar_h}" rx="10" fill="{COLORS[index]}"/>')
        rows.append(f'<text x="{left + min(bar_w + 12, plot_w - 90):.2f}" y="{y + 28}" class="value">{esc(formatter(value))}</text>')
    rows.append('<text x="40" y="525" class="meta">Sol and Daybreak Blue are separate route/safeguard conditions; they are not claimed to use distinct underlying weights.</text>')
    rows.append('</svg>')
    return "".join(rows)


def scatter_chart(routes: list[dict]) -> str:
    width, height = 1100, 650
    left, top, plot_w, plot_h = 100, 100, 900, 430
    costs = [float(route["api_equivalent_cost_mean_observed_usd"]) for route in routes]
    rates = [float(route["resolved_rate"]) for route in routes]
    max_cost = max(costs) or 1
    rows = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">', '<rect width="100%" height="100%" fill="#09090b"/><style>text{font-family:Inter,Geist,Arial,sans-serif}.title{fill:#fafafa;font-size:28px;font-weight:750}.label{fill:#e4e4e7;font-size:15px}.meta{fill:#a1a1aa;font-size:14px}.grid{stroke:#27272a;stroke-width:1}</style>', '<text x="40" y="50" class="title">Resolved rate vs observed mean API-equivalent cost</text>', '<text x="40" y="76" class="meta">Upper-left is preferable; usage-unavailable runs are excluded from the cost mean.</text>']
    for tick in range(6):
        x = left + plot_w * tick / 5
        y = top + plot_h * tick / 5
        rows.append(f'<line x1="{x}" y1="{top}" x2="{x}" y2="{top + plot_h}" class="grid"/>')
        rows.append(f'<line x1="{left}" y1="{y}" x2="{left + plot_w}" y2="{y}" class="grid"/>')
        rows.append(f'<text x="{x - 20}" y="{top + plot_h + 28}" class="meta">${max_cost * tick / 5:.2f}</text>')
        rows.append(f'<text x="45" y="{top + plot_h - plot_h * tick / 5 + 5}" class="meta">{tick * 20}%</text>')
    for index, (route, cost, rate) in enumerate(zip(routes, costs, rates)):
        x = left + plot_w * cost / max_cost
        y = top + plot_h * (1 - rate)
        name = ALIASES.get(route["route_id"], route["route_id"])
        rows.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="12" fill="{COLORS[index]}" stroke="#fafafa" stroke-width="2"/>')
        rows.append(f'<text x="{x + 16:.2f}" y="{y + 5:.2f}" class="label">{esc(name)}</text>')
    rows.append('<text x="360" y="600" class="meta">Mean API-equivalent cost per usage-observed primary run (USD)</text><text transform="translate(22,430) rotate(-90)" class="meta">Resolved rate</text></svg>')
    return "".join(rows)


def markdown_report(summary: dict, rows: list[dict]) -> str:
    statuses = Counter(row["actual_cost_status"] for row in rows)
    billed = [num(row["actual_cost_usd"]) for row in rows if row.get("actual_cost_usd") not in ("", None)]
    lines = [
        "# LLM Engineering Benchmark — campaign-20260814-v4",
        "",
        "## Integrity",
        "",
        "- 360/360 expected runs observed and verified.",
        "- Primary leaderboard: attempt 1 only, 40 tasks per route.",
        "- Attempts 2–3: preregistered 10-task repeat subset only.",
        "- Six route conditions, five underlying model snapshots; Sol and Daybreak Blue remain distinct route/safeguard conditions.",
        "",
        "## Route results",
        "",
        "| Route | Resolved | Rate | Mean API-eq. cost | Cost coverage | Cost / resolved | Median | P95 | 3/3 repeat |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for route in summary["routes"]:
        alias = ALIASES.get(route["route_id"], route["route_id"])
        cpr = "—" if route["cost_per_resolved_task_usd"] is None else f"${route['cost_per_resolved_task_usd']:.4f}"
        lines.append(f"| {alias} | {route['resolved_tasks']}/40 | {route['resolved_rate']:.1%} | ${route['api_equivalent_cost_mean_observed_usd']:.4f} | {route['api_equivalent_cost_primary_coverage']}/40 | {cpr} | {route['median_wall_seconds']:.1f}s | {route['p95_wall_seconds_nearest_rank']:.1f}s | {route['repeat_subset_all_three_resolved']}/10 |")
    lines.extend([
        "",
        "## Cost semantics",
        "",
        f"- Actual billed total: {'$' + format(sum(value for value in billed if value is not None), '.6f') if billed else 'not asserted'}.",
        f"- Run cost-status inventory: `{dict(sorted(statuses.items()))}`.",
        "- `api_equivalent_cost_usd` uses the frozen public token-price table.",
        "- Runs with unavailable provider usage are classified as `usage_unavailable`, never as zero-cost observations. Cost charts use the mean over usage-observed primary runs and show coverage explicitly.",
        "- Provider estimates, included usage, unknown billing, and actual billed evidence remain separate.",
        "",
        "## Charts",
        "",
        "- [Resolved rate](resolved-rate.svg)",
        "- [API-equivalent cost](api-equivalent-cost.svg)",
        "- [Median latency](median-latency.svg)",
        "- [Repeat reliability](repeat-reliability.svg)",
        "- [Resolved rate vs cost](resolved-vs-cost.svg)",
        "",
        "## Limitations",
        "",
        "- Requested route IDs and provider-reported metadata do not independently prove immutable provider-side weights.",
        "- Shared-service wall latency is observational, not pure model compute time.",
        "- Hidden graders are disclosed only after campaign sealing to avoid contamination.",
        "- The frozen `proof/campaign-plan.json` retained unused v3 command strings and a stale order. The executed and integrity-checked v4 plan was deterministically derived from the frozen `suite.json`; the 360-cell identity sets are equal. The stale proof is retained and disclosed rather than rewritten.",
        "- The campaign driver was externally interrupted twice. Six unsealed partial cells with dead lock PIDs were archived and excluded, then rerun under their originally planned attempt labels. Only checksum-valid sealed artifacts are counted.",
        "- One Daybreak request was rejected before any counted response with the provider error that the requested model was unsupported for the account. The unsealed partial was archived and excluded; the same exact route later succeeded and the planned cell was rerun without fallback.",
        "- The frozen runner inherited a nonsecret dashboard username setting into Hermes/tool process environments, producing the same configuration warning across all 360 sealed runs. The final artifact rescan found no dashboard-auth variable-name reference, and no recorded JSONL isolation trace contained an `env`, `printenv`, or `/proc/*/environ` marker. Those JSONL traces cover sandbox/isolation events rather than a complete candidate command ledger, so this is evidence of no observed use—not proof that the inherited value was inaccessible. The strict environment-allowlist fix is post-campaign.",
        "- No combined scalar ranking is produced; capability, reliability, latency, and normalized cost remain separate axes.",
        "",
    ])
    return "\n".join(lines)


def atomic_write(path: Path, content: str) -> None:
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-dir", type=Path, required=True)
    parser.add_argument("--suite", type=Path, default=DEFAULT_SUITE)
    parser.add_argument("--incident", type=Path, default=DEFAULT_INCIDENT)
    parser.add_argument("--derived-plan", type=Path, default=DEFAULT_DERIVED_PLAN)
    parser.add_argument("--runs-root", type=Path, default=DEFAULT_RUNS_ROOT)
    parser.add_argument("--environment-incident", type=Path, default=ENVIRONMENT_INCIDENT)
    parser.add_argument("--environment-final-scan", type=Path, default=ENVIRONMENT_FINAL_SCAN)
    args = parser.parse_args()
    results = args.results_dir.resolve(strict=True)
    freeze = subprocess.run(
        ["python3", str(REPO / "scripts" / "freeze.py"), "verify"],
        cwd=REPO,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=120,
    )
    if freeze.returncode != 0:
        raise ValueError("live v4 source freeze verification failed: " + (freeze.stdout + freeze.stderr).strip())
    freeze_report = json.loads(freeze.stdout)
    if freeze_report != {"file_count": 471, "source_tree_sha256": EXPECTED_SOURCE_TREE_SHA256, "verified": True}:
        raise ValueError("live v4 source freeze attestation differs from the sealed campaign")
    if any(path.is_symlink() for path in (args.suite, args.incident, args.derived_plan, args.runs_root, args.environment_incident, args.environment_final_scan, ENVIRONMENT_SCANNER)):
        raise ValueError("postprocessor inputs must not be symlinks")
    suite_path = args.suite.resolve(strict=True)
    incident_path = args.incident.resolve(strict=True)
    derived_plan_path = args.derived_plan.resolve(strict=True)
    runs_root = args.runs_root.resolve(strict=True)
    environment_incident_path = args.environment_incident.resolve(strict=True)
    environment_scan_path = args.environment_final_scan.resolve(strict=True)
    environment_scanner_path = ENVIRONMENT_SCANNER.resolve(strict=True)
    environment_verification = subprocess.run(
        [
            "python3", str(environment_scanner_path), "--runs-root", str(runs_root),
            "--incident", str(environment_incident_path), "--output", str(environment_scan_path), "--verify",
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=300,
    )
    if environment_verification.returncode != 0:
        raise ValueError("final environment limitation scan failed live verification: " + (environment_verification.stdout + environment_verification.stderr).strip())
    environment_scan = json.loads(environment_scan_path.read_text(encoding="utf-8"))
    if environment_scan.get("passed") is not True or environment_scan.get("sealed_run_count") != 360 or environment_scan.get("warning_run_count") != 360:
        raise ValueError("final environment limitation scan summary differs")
    if not incident_path.is_file():
        raise ValueError("campaign incident record must be a regular file")
    incident = json.loads(incident_path.read_text(encoding="utf-8"))
    if incident.get("campaign_id") != "campaign-20260814-v4" or incident.get("finding", {}).get("identity_set_equal") is not True or incident.get("execution_path", {}).get("proof_plan_consumed_by_code") is not False:
        raise ValueError("campaign incident record does not attest the known stale proof-plan scope")
    interruption_reports = []
    for path in INTERRUPTION_INCIDENTS:
        if path.is_symlink() or not path.is_file():
            raise ValueError("campaign interruption record must be a regular file")
        report = json.loads(path.read_text(encoding="utf-8"))
        archived = report.get("runs") if isinstance(report.get("runs"), list) else report.get("archived_partials")
        if report.get("campaign_id") != "campaign-20260814-v4" or not isinstance(archived, list) or len(archived) != 3:
            raise ValueError("campaign interruption record does not attest exactly three archived partials")
        for row in archived:
            if not str(row.get("run_key", "")).startswith("campaign-20260814-v4__"):
                raise ValueError("campaign interruption record contains an unexpected run key")
            if row.get("complete_marker_present") not in (None, False) or row.get("proc_pid_exists_before_archive") not in (None, False):
                raise ValueError("campaign interruption record does not prove an unsealed orphan")
        interruption_reports.append((path, report))
    provider_incident_reports = []
    expected_provider_error = "HTTP 400: {\"detail\":\"The 'gpt-daybreak-blue-latest' model is not supported when using Codex with a ChatGPT account.\"}"
    for path in PROVIDER_INCIDENTS:
        if path.is_symlink() or not path.is_file():
            raise ValueError("campaign provider incident record must be a regular file")
        report = json.loads(path.read_text(encoding="utf-8"))
        run_key = report.get("run_key")
        usage = report.get("usage")
        ownership = report.get("ownership_proof")
        artifact_hashes = report.get("artifact_sha256")
        if (
            report.get("campaign_id") != "campaign-20260814-v4"
            or report.get("incident_type") != "provider_route_rejected_before_counted_response"
            or report.get("plan_index") != 267
            or report.get("task_id") != "DATA-04"
            or report.get("attempt") != 3
            or report.get("provider") != "openai-codex"
            or report.get("requested_model") != "gpt-daybreak-blue-latest"
            or report.get("runner_returncode") != 2
            or report.get("provider_error") != expected_provider_error
            or report.get("disposition") != "excluded_unsealed_provider_failure"
            or run_key != "campaign-20260814-v4__DATA-04__a3__openai-codex__gpt-daybreak-blue-latest"
        ):
            raise ValueError("campaign provider incident identity or error differs from the observed failure")
        if not isinstance(usage, dict) or type(usage.get("api_calls")) is not int or usage.get("api_calls") != 4 or usage.get("completed") is not False or usage.get("failed") is not True:
            raise ValueError("campaign provider incident usage does not attest the failed uncounted call")
        if any(usage.get(key) is not None for key in ("provider", "model", "input_tokens", "output_tokens", "total_tokens")):
            raise ValueError("campaign provider incident unexpectedly attributes a resolved route or token usage")
        if not isinstance(ownership, dict) or ownership.get("runner_lock_present_before_archive") is not False or ownership.get("matching_process_present_before_archive") is not False:
            raise ValueError("campaign provider incident does not prove the partial was unowned before archive")
        expected_artifacts = {"request.json", "state.json", "stdout.txt", "stderr.txt", "usage.json"}
        if not isinstance(artifact_hashes, dict) or set(artifact_hashes) != expected_artifacts:
            raise ValueError("campaign provider incident artifact inventory differs")
        partial = path.parent / "partial" / run_key
        if partial.is_symlink() or not partial.is_dir():
            raise ValueError("campaign provider incident archived partial is missing or unsafe")
        for name in expected_artifacts:
            artifact = partial / name
            if artifact.is_symlink() or not artifact.is_file() or sha256(artifact) != artifact_hashes[name]:
                raise ValueError("campaign provider incident artifact commitment differs")
        provider_incident_reports.append((path, report))
    suite = load_suite(suite_path)
    derived_plan = json.loads(derived_plan_path.read_text(encoding="utf-8"))
    derived_rows = derived_plan.get("runs")
    if not isinstance(derived_rows, list) or derived_plan.get("full_run_count") != 360 or len(derived_rows) != 360:
        raise ValueError("derived v4 plan does not contain exactly 360 runs")
    derived_identities = [
        (row.get("task_id"), row.get("attempt"), row.get("provider"), row.get("requested_model"))
        for row in derived_rows
    ]
    if derived_identities != expected_ordered_identities(suite):
        raise ValueError("derived v4 plan order differs from the frozen suite seed")
    for row in derived_rows:
        command = row.get("command")
        if not isinstance(command, list) or any(not isinstance(item, str) for item in command):
            raise ValueError("derived v4 plan contains an invalid command")
        expected_run_id = "__".join((suite["campaign_id"], row["task_id"], f"a{row['attempt']}", row["provider"], row["requested_model"]))
        if "--run-key" not in command or command[command.index("--run-key") + 1] != expected_run_id or any("campaign-20260813-v3" in item for item in command):
            raise ValueError("derived v4 plan command is stale or inconsistent")
    summary, rows = load_inputs(results, suite)
    audit_summary(summary, rows, suite)
    annotate_cost_coverage(summary, rows)
    routes = summary["routes"]
    outputs = {
        "report.md": markdown_report(summary, rows),
        "resolved-rate.svg": bar_chart("Primary resolved rate", routes, "resolved_rate", lambda value: f"{value:.1%}", True),
        "api-equivalent-cost.svg": bar_chart("Mean API-equivalent cost (usage observed)", summary["routes"], "api_equivalent_cost_mean_observed_usd", lambda value: f"${value:.3f}", False),
        "median-latency.svg": bar_chart("Median wall latency", routes, "median_wall_seconds", lambda value: f"{value:.1f}s", False),
        "repeat-reliability.svg": bar_chart("Repeat subset: all three attempts resolved", routes, "repeat_subset_consistency_rate", lambda value: f"{value:.1%}", True),
        "resolved-vs-cost.svg": scatter_chart(routes),
    }
    for name, content in outputs.items():
        atomic_write(results / name, content)
    manifest = {
        "schema_version": "1.0",
        "campaign_id": "campaign-20260814-v4",
        "suite_sha256": sha256(suite_path),
        "benchmark_source_file_count": 471,
        "benchmark_source_tree_sha256": EXPECTED_SOURCE_TREE_SHA256,
        "freeze_manifest_sha256": sha256(REPO / "freeze-manifest.json"),
        "postprocessor_sha256": sha256(Path(__file__).resolve(strict=True)),
        "known_incident_sha256": sha256(incident_path),
        "interruption_incident_sha256": {
            path.parent.name: sha256(path) for path, _report in interruption_reports
        },
        "provider_incident_sha256": {
            path.parent.name: sha256(path) for path, _report in provider_incident_reports
        },
        "environment_incident_sha256": sha256(environment_incident_path),
        "environment_final_scan_sha256": sha256(environment_scan_path),
        "environment_scanner_sha256": sha256(environment_scanner_path),
        "derived_v4_plan_sha256": sha256(derived_plan_path),
        "source_summary_sha256": sha256(results / "summary.json"),
        "source_runs_csv_sha256": sha256(results / "runs.csv"),
        "outputs": {name: sha256(results / name) for name in sorted(outputs)},
        "raw_model_outputs_included": False,
    }
    atomic_write(results / "report-manifest.json", json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"verified_runs": 360, "outputs": sorted(outputs), "manifest": str(results / "report-manifest.json")}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
