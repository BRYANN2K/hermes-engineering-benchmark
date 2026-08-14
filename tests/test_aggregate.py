#!/usr/bin/env python3
"""Unit/integration checks for the machine-readable result aggregator."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import stat
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("aggregate_module", ROOT / "scripts" / "aggregate.py")
AGG = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AGG)
INTEGRITY_SPEC = importlib.util.spec_from_file_location("integrity_module", ROOT / "scripts" / "verify_campaign_integrity.py")
assert INTEGRITY_SPEC is not None and INTEGRITY_SPEC.loader is not None
INTEGRITY = importlib.util.module_from_spec(INTEGRITY_SPEC)
INTEGRITY_SPEC.loader.exec_module(INTEGRITY)


class AggregateTests(unittest.TestCase):
    def _reseal(self, run: Path) -> None:
        run.chmod(run.stat().st_mode | stat.S_IWUSR)
        for path in run.rglob("*"):
            if path.is_dir():
                path.chmod(path.stat().st_mode | stat.S_IWUSR)
            if path.is_file():
                path.chmod(path.stat().st_mode | stat.S_IWUSR)
        (run / "checksums.sha256").unlink(missing_ok=True)
        (run / "COMPLETE").unlink(missing_ok=True)
        lines = []
        for path in sorted(p for p in run.rglob("*") if p.is_file()):
            lines.append(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.relative_to(run).as_posix()}")
        checksums = run / "checksums.sha256"
        checksums.write_text("\n".join(lines) + "\n", encoding="utf-8")
        (run / "COMPLETE").write_text(json.dumps({"checksums_sha256": hashlib.sha256(checksums.read_bytes()).hexdigest()}) + "\n", encoding="utf-8")
        for path in run.rglob("*"):
            if path.is_file():
                path.chmod(path.stat().st_mode & ~0o222)
            elif path.is_dir():
                path.chmod(path.stat().st_mode & ~0o222)
        run.chmod(run.stat().st_mode & ~0o222)

    def _sealed(self, root: Path, route: dict, task: str = "BUG-03", attempt: int = 1, run_id: str | None = None) -> Path:
        run = root / (run_id or f"{task}-{attempt}-{route['requested_model']}")
        run.mkdir()
        runtime_sha256 = AGG.runtime_manifest_sha256()
        source_freeze = json.loads(AGG.SOURCE_FREEZE_COMMITMENT.read_text())
        grader_sha256 = AGG.grader_commitment(task)
        assert grader_sha256 is not None
        landlock_sha256 = AGG.LANDLOCK_HELPER_HASH_FILE.read_text().strip()
        payloads = {
            "manifest.json": {
                "run_id": run.name,
                "benchmark_freeze": {"status": "verified", "source_tree_sha256": source_freeze["source_tree_sha256"], "file_count": source_freeze["file_count"]},
                "task": {"task_id": task, "attempt": attempt},
                "hermes": {"provider": route["provider"], "model": route["requested_model"], "runtime_verification": "verified", "runtime_manifest_sha256": runtime_sha256},
                "environment": {"HERMES_HOME": "ephemeral-per-run", "agent_tool_sandbox": {"enabled": True, "landlock_helper_sha256": landlock_sha256}, "grader_sandbox": {"enabled": True}},
                "grader": {"sha256": "1" * 64, "bundle_sha256": grader_sha256},
            },
            "request.json": {"task_id": task, "attempt": attempt, "provider": route["provider"], "model": route["requested_model"], "hermes_runtime_manifest_sha256": runtime_sha256, "benchmark_source_tree_sha256": source_freeze["source_tree_sha256"], "benchmark_source_file_count": source_freeze["file_count"], "landlock_helper_sha256": landlock_sha256, "grader_sha256": "1" * 64, "grader_bundle_sha256": grader_sha256},
            "result.json": {"run_id": run.name, "model": {"provider": route["provider"], "requested_id": route["requested_model"]}, "task": {"task_id": task, "attempt": attempt}, "outcome": {"success": True, "passed": True, "score": 1.0, "hermes_completed": True, "grader_completed": True, "tool_sandbox_verified": True}},
            "usage.json": {"input_tokens": 100, "cache_read_tokens": 50, "cache_write_tokens": 0, "output_tokens": 10, "reasoning_tokens": 5, "total_tokens": 160, "api_calls": 2, "cost_status": "included", "estimated_cost_usd": 0.0, "completed": True, "failed": False},
            "timing.json": {"hermes": {"wall_seconds": 2.0}, "grader": {"wall_seconds": 0.1}},
            "exit_status.json": {"hermes": {"return_code": 0, "timed_out": False}, "grader": {"return_code": 0, "timed_out": False}},
        }
        for name, value in payloads.items():
            (run / name).write_text(json.dumps(value) + "\n", encoding="utf-8")
        (run / "tool-sandbox.jsonl").write_text(
            '{"sandbox":"hermes-tool-hook","installed":true,"cognitive_isolation_installed":true,"ephemeral_home":true,"shared_credentials_host_only":true}\n'
            '{"sandbox":"hermes-cognitive-isolation","applied":true,"skip_memory":true,"skip_context_files":true,"load_soul_identity":false,"fallback_disabled":true}\n'
            '{"sandbox":"landlock-seccomp-netns","activated":true}\n',
            encoding="utf-8",
        )
        self._reseal(run)
        return run

    def test_all_routes_aggregate_and_cost_does_not_double_count_reasoning(self) -> None:
        suite = json.loads((ROOT / "suite.json").read_text())
        pricing = json.loads((ROOT / "pricing" / "official-pricing-2026-08-13.json").read_text())
        with tempfile.TemporaryDirectory() as tmp:
            rows = [AGG.row(self._sealed(Path(tmp), route), pricing) for route in suite["routes"]]
        summary = AGG.aggregate(rows, suite)
        self.assertEqual(len(summary), 6)
        self.assertTrue(all(item["primary_runs"] == 1 for item in summary))
        self.assertTrue(all(item["resolved_rate"] == 1.0 for item in summary))
        self.assertTrue(all(item["mean_sandboxed_tool_invocations"] == 1 for item in summary))
        sol = next(item for item in rows if item["requested_model"] == "gpt-5.6-sol")
        self.assertAlmostEqual(sol["api_equivalent_cost_usd"], (100*5 + 50*.5 + 10*30)/1_000_000)
        self.assertIsNone(sol["actual_cost_usd"])
        self.assertIsNone(sol["provider_reported_estimated_cost_usd"])

    def test_undeclared_file_breaks_seal(self) -> None:
        suite = json.loads((ROOT / "suite.json").read_text())
        with tempfile.TemporaryDirectory() as tmp:
            run = self._sealed(Path(tmp), suite["routes"][0])
            run.chmod(run.stat().st_mode | stat.S_IWUSR)
            (run / "injected.txt").write_text("tamper", encoding="utf-8")
            passed, error = AGG.verify_checksums(run)
        self.assertFalse(passed)
        self.assertIn("inventory mismatch", error)

    def test_cell_integrity_rejects_resealed_runtime_fingerprint_tamper(self) -> None:
        suite = json.loads((ROOT / "suite.json").read_text())
        with tempfile.TemporaryDirectory() as tmp:
            run = self._sealed(Path(tmp), suite["routes"][0])
            manifest = json.loads((run / "manifest.json").read_text())
            (run / "manifest.json").chmod(0o600)
            manifest["hermes"]["runtime_manifest_sha256"] = "0" * 64
            (run / "manifest.json").write_text(json.dumps(manifest) + "\n")
            self._reseal(run)
            passed, errors, _ = AGG.verify_cell(run)
        self.assertFalse(passed)
        self.assertIn("external Hermes runtime fingerprint mismatch", errors)

    def test_cell_integrity_rejects_resealed_source_freeze_tamper(self) -> None:
        suite = json.loads((ROOT / "suite.json").read_text())
        with tempfile.TemporaryDirectory() as tmp:
            run = self._sealed(Path(tmp), suite["routes"][0])
            manifest = json.loads((run / "manifest.json").read_text())
            (run / "manifest.json").chmod(0o600)
            manifest["benchmark_freeze"]["source_tree_sha256"] = "0" * 64
            (run / "manifest.json").write_text(json.dumps(manifest) + "\n")
            self._reseal(run)
            passed, errors, _ = AGG.verify_cell(run)
        self.assertFalse(passed)
        self.assertIn("benchmark source freeze mismatch", errors)

    def test_cell_integrity_rejects_resealed_duplicate_cognitive_marker(self) -> None:
        suite = json.loads((ROOT / "suite.json").read_text())
        with tempfile.TemporaryDirectory() as tmp:
            run = self._sealed(Path(tmp), suite["routes"][0])
            trace = run / "tool-sandbox.jsonl"
            trace.chmod(0o600)
            lines = trace.read_text().splitlines()
            trace.write_text("\n".join(lines + [lines[1]]) + "\n")
            self._reseal(run)
            passed, errors, evidence = AGG.verify_cell(run)
        self.assertFalse(passed)
        self.assertEqual(evidence["cognitive_attestations"], 2)
        self.assertTrue(any("exactly one cognitive-isolation" in error for error in errors))

    def test_cell_integrity_rejects_resealed_identity_tamper(self) -> None:
        suite = json.loads((ROOT / "suite.json").read_text())
        with tempfile.TemporaryDirectory() as tmp:
            run = self._sealed(Path(tmp), suite["routes"][0])
            request = json.loads((run / "request.json").read_text())
            (run / "request.json").chmod(0o600)
            request["attempt"] = 2
            (run / "request.json").write_text(json.dumps(request) + "\n")
            self._reseal(run)
            passed, errors, _ = AGG.verify_cell(run)
        self.assertFalse(passed)
        self.assertIn("request/manifest/result experimental identity mismatch", errors)

    def test_cell_integrity_rejects_resealed_grader_commitment_tamper(self) -> None:
        suite = json.loads((ROOT / "suite.json").read_text())
        with tempfile.TemporaryDirectory() as tmp:
            run = self._sealed(Path(tmp), suite["routes"][0])
            manifest = json.loads((run / "manifest.json").read_text())
            (run / "manifest.json").chmod(0o600)
            manifest["grader"]["bundle_sha256"] = "0" * 64
            (run / "manifest.json").write_text(json.dumps(manifest) + "\n")
            self._reseal(run)
            passed, errors, _ = AGG.verify_cell(run)
        self.assertFalse(passed)
        self.assertIn("grader bundle commitment mismatch", errors)

    def test_cell_integrity_rejects_resealed_landlock_helper_tamper(self) -> None:
        suite = json.loads((ROOT / "suite.json").read_text())
        with tempfile.TemporaryDirectory() as tmp:
            run = self._sealed(Path(tmp), suite["routes"][0])
            manifest = json.loads((run / "manifest.json").read_text())
            (run / "manifest.json").chmod(0o600)
            manifest["environment"]["agent_tool_sandbox"]["landlock_helper_sha256"] = "0" * 64
            (run / "manifest.json").write_text(json.dumps(manifest) + "\n")
            self._reseal(run)
            passed, errors, _ = AGG.verify_cell(run)
        self.assertFalse(passed)
        self.assertIn("agent sandbox or ephemeral-home policy mismatch", errors)

    def test_campaign_plan_and_six_route_canary_integrity(self) -> None:
        suite = json.loads((ROOT / "suite.json").read_text())
        full = INTEGRITY.expected_cells(suite, "full")
        canary = INTEGRITY.expected_cells(suite, "canary")
        self.assertEqual(len(full), 360)
        self.assertEqual(len(canary), 6)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for run_id, cell in canary.items():
                route = {"provider": cell["provider"], "requested_model": cell["requested_model"]}
                run = self._sealed(root, route, task=cell["task_id"], attempt=cell["attempt"], run_id=run_id)
                passed, errors, _ = AGG.verify_cell(run, expected=cell, require_successful_canary=True)
                self.assertTrue(passed, errors)
            observed = {path.name for path in root.iterdir() if path.is_dir()}
            self.assertEqual(observed, set(canary))

    def test_canary_extra_key_policy_allows_only_frozen_full_plan(self) -> None:
        suite = json.loads((ROOT / "suite.json").read_text())
        full = INTEGRITY.expected_cells(suite, "full")
        canary = INTEGRITY.expected_cells(suite, "canary")
        planned_extra = next(key for key in full if key not in canary)
        observed = set(canary) | {planned_extra, "unplanned-run"}
        extra = sorted(observed - set(canary))
        unexpected = sorted(set(extra) - set(full))
        self.assertEqual(unexpected, ["unplanned-run"])

    def test_campaign_integrity_cli_enforces_exact_canary_and_planned_extras(self) -> None:
        suite = json.loads((ROOT / "suite.json").read_text())
        full = INTEGRITY.expected_cells(suite, "full")
        canary = INTEGRITY.expected_cells(suite, "canary")
        command = [
            sys.executable,
            str(ROOT / "scripts" / "verify_campaign_integrity.py"),
            "{root}",
            "--expected", "6",
            "--scope", "canary",
        ]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for run_id, cell in canary.items():
                route = {"provider": cell["provider"], "requested_model": cell["requested_model"]}
                self._sealed(root, route, task=cell["task_id"], attempt=cell["attempt"], run_id=run_id)

            def invoke(*extra: str) -> subprocess.CompletedProcess[str]:
                return subprocess.run(
                    [part.format(root=str(root)) for part in command] + list(extra),
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=False,
                )

            self.assertEqual(invoke().returncode, 0)
            planned_extra = next(key for key in full if key not in canary)
            (root / planned_extra).mkdir()
            self.assertNotEqual(invoke().returncode, 0)
            self.assertEqual(invoke("--allow-planned-extras").returncode, 0)
            (root / planned_extra).rmdir()
            (root / "unplanned-run").mkdir()
            self.assertNotEqual(invoke("--allow-planned-extras").returncode, 0)


if __name__ == "__main__":
    unittest.main()
