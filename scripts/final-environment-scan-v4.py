#!/usr/bin/env python3
"""Create or verify the final v4 inherited-environment limitation scan."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from pathlib import Path

CAMPAIGN_ID = "campaign-20260814-v4"
EXPECTED_RUNS = 360
EXPECTED_SOURCE_TREE_SHA256 = "ee3327ff74001ae79175c7b103ebcf88b61b2797d3d966aeacf4efac38d13d6f"
EXPECTED_RUNTIME_SHA256 = "a996ff33779fd30e727144c28d3b3fbb391031f293ed2ecfd11233d29faf2c45"
WARNING = "dashboard-auth-basic: dashboard.basic_auth.username is set but neither password_hash nor password is configured"
DASHBOARD_NAMES = (
    "HERMES_DASHBOARD_BASIC_AUTH_USERNAME",
    "HERMES_DASHBOARD_BASIC_AUTH_PASSWORD",
    "HERMES_DASHBOARD_BASIC_AUTH_SECRET",
)
ENUMERATION_PATTERN = re.compile(r"(?<![A-Za-z0-9_])(?:env|printenv)(?![A-Za-z0-9_])|/proc/(?:self|[0-9]+)/environ")
TEXT_EXTENSIONS = {".json", ".jsonl", ".txt"}
DEFAULT_INCIDENT = Path("/opt/data/benchmarks/hermes-engineering-bench/incidents/20260814T195436Z-inherited-dashboard-username-environment.json")
DEFAULT_OUTPUT = Path("/opt/data/benchmarks/hermes-engineering-bench/incidents/20260814-final-environment-scan.json")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def safe_regular(path: Path, parent: Path) -> bool:
    try:
        return not path.is_symlink() and path.is_file() and path.resolve(strict=True).is_relative_to(parent)
    except (OSError, RuntimeError):
        return False


def validate_incident(path: Path) -> dict:
    if path.is_symlink() or not path.is_file():
        raise ValueError("environment incident must be a regular non-symlink file")
    report = json.loads(path.read_text(encoding="utf-8"))
    finding = report.get("finding")
    trajectory = report.get("trajectory_scan")
    impact = report.get("impact_assessment")
    if (
        report.get("schema_version") != "1.0"
        or report.get("campaign_id") != CAMPAIGN_ID
        or report.get("incident_type") != "inherited_nonsecret_dashboard_username_environment"
        or report.get("frozen_source_tree_sha256") != EXPECTED_SOURCE_TREE_SHA256
        or report.get("hermes_runtime_sha256") != EXPECTED_RUNTIME_SHA256
        or not isinstance(finding, dict)
        or finding.get("dashboard_username_name_reaches_hermes_process") is not True
        or finding.get("dashboard_password_name_reaches_hermes_process") is not False
        or finding.get("dashboard_secret_name_reaches_hermes_process") is not False
        or finding.get("dashboard_username_value_read_for_audit") is not False
        or not isinstance(trajectory, dict)
        or trajectory.get("exact_dashboard_auth_variable_reference_files") != 0
        or trajectory.get("generic_env_printenv_or_proc_environ_command_files") != 0
        or not isinstance(impact, dict)
        or impact.get("credential_exposure") is not False
        or impact.get("nonsecret_operator_identity_exposure_possible") is not True
        or impact.get("campaign_validity") != "retain with explicit limitation, final 360-run rescan, and post-campaign fix"
    ):
        raise ValueError("environment incident contract differs")
    return report


def scan(runs_root: Path, incident: Path) -> dict:
    validate_incident(incident)
    if runs_root.is_symlink() or not runs_root.is_dir():
        raise ValueError("campaign runs root must be a regular non-symlink directory")
    root = runs_root.resolve(strict=True)
    run_dirs = sorted(path for path in root.iterdir() if path.is_dir() and not path.is_symlink())
    if len(run_dirs) != EXPECTED_RUNS or any(not path.name.startswith(f"{CAMPAIGN_ID}__") for path in run_dirs):
        raise ValueError(f"expected exactly {EXPECTED_RUNS} v4 run directories")
    inventory = []
    warning_runs = []
    variable_reference_files = []
    enumeration_files = []
    for run_dir in run_dirs:
        resolved_run = run_dir.resolve(strict=True)
        if resolved_run.parent != root:
            raise ValueError("run directory escapes campaign root")
        complete = run_dir / "COMPLETE"
        if not safe_regular(complete, resolved_run):
            raise ValueError(f"run is not sealed safely: {run_dir.name}")
        stderr = run_dir / "stderr.txt"
        if not safe_regular(stderr, resolved_run):
            raise ValueError(f"run stderr is missing or unsafe: {run_dir.name}")
        stderr_text = stderr.read_text(encoding="utf-8", errors="strict")
        if WARNING in stderr_text:
            warning_runs.append(run_dir.name)
        for artifact in sorted(run_dir.rglob("*")):
            if artifact.is_symlink():
                raise ValueError(f"symlink in sealed run: {artifact}")
            if not artifact.is_file() or artifact.suffix not in TEXT_EXTENSIONS:
                continue
            resolved = artifact.resolve(strict=True)
            if not resolved.is_relative_to(resolved_run):
                raise ValueError("artifact escapes run directory")
            text = artifact.read_text(encoding="utf-8", errors="strict")
            relative = f"{run_dir.name}/{artifact.relative_to(run_dir).as_posix()}"
            if any(name in text for name in DASHBOARD_NAMES):
                variable_reference_files.append(relative)
            if artifact.suffix == ".jsonl" and ENUMERATION_PATTERN.search(text):
                enumeration_files.append(relative)
        inventory.append({"run_id": run_dir.name, "complete_sha256": sha256(complete)})
    if len(warning_runs) != EXPECTED_RUNS:
        raise ValueError(f"expected the documented warning in exactly {EXPECTED_RUNS} sealed runs, got {len(warning_runs)}")
    if variable_reference_files:
        raise ValueError("dashboard auth variable names appear in sealed text artifacts")
    if enumeration_files:
        raise ValueError("environment enumeration command appears in sealed trajectories")
    return {
        "schema_version": "1.0",
        "campaign_id": CAMPAIGN_ID,
        "passed": True,
        "sealed_run_count": EXPECTED_RUNS,
        "warning_run_count": EXPECTED_RUNS,
        "dashboard_auth_variable_reference_file_count": 0,
        "environment_enumeration_trajectory_file_count": 0,
        "jsonl_trace_coverage": "sandbox_and_isolation_events_only_not_a_complete_candidate_command_ledger",
        "sealed_inventory_sha256": hashlib.sha256(canonical(inventory)).hexdigest(),
        "incident_sha256": sha256(incident),
        "scanner_sha256": sha256(Path(__file__).resolve(strict=True)),
        "frozen_source_tree_sha256": EXPECTED_SOURCE_TREE_SHA256,
        "hermes_runtime_sha256": EXPECTED_RUNTIME_SHA256,
        "limitation": "A nonsecret dashboard username was process-accessible during counted runs. No sealed text artifact referenced the dashboard-auth variable names and no recorded JSONL isolation trace contained an environment-enumeration marker, but those JSONL traces are not a complete candidate command ledger.",
    }


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    try:
        temporary.write_text(content, encoding="utf-8")
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs-root", type=Path, required=True)
    parser.add_argument("--incident", type=Path, default=DEFAULT_INCIDENT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    observed = scan(args.runs_root, args.incident)
    if args.verify:
        if args.output.is_symlink() or not args.output.is_file():
            raise ValueError("final environment scan report is missing or unsafe")
        recorded = json.loads(args.output.read_text(encoding="utf-8"))
        if recorded != observed:
            raise ValueError("final environment scan report differs from live rescan")
    else:
        if args.output.exists() or args.output.is_symlink():
            raise ValueError("refusing to overwrite an existing final environment scan report")
        atomic_write(args.output, json.dumps(observed, indent=2, sort_keys=True) + "\n")
    print(json.dumps(observed, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
