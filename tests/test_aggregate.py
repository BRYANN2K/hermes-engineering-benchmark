#!/usr/bin/env python3
"""Unit/integration checks for the machine-readable result aggregator."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("aggregate_module", ROOT / "scripts" / "aggregate.py")
AGG = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AGG)


class AggregateTests(unittest.TestCase):
    def _sealed(self, root: Path, route: dict, task: str = "BUG-03", attempt: int = 1) -> Path:
        run = root / f"{task}-{attempt}-{route['requested_model']}"
        run.mkdir()
        payloads = {
            "manifest.json": {"run_id": run.name, "task": {"task_id": task, "attempt": attempt}, "model": {"provider": route["provider"], "requested_id": route["requested_model"]}},
            "result.json": {"outcome": {"success": True, "score": 1.0, "hermes_completed": True, "grader_completed": True}},
            "usage.json": {"input_tokens": 100, "cache_read_tokens": 50, "cache_write_tokens": 0, "output_tokens": 10, "reasoning_tokens": 5, "total_tokens": 160, "api_calls": 2, "cost_status": "included", "estimated_cost_usd": 0.0},
            "timing.json": {"hermes": {"wall_seconds": 2.0}},
        }
        for name, value in payloads.items():
            (run / name).write_text(json.dumps(value) + "\n", encoding="utf-8")
        (run / "tool-sandbox.jsonl").write_text('{"sandbox":"hermes-tool-hook","installed":true}\n{"sandbox":"landlock-seccomp-netns","activated":true}\n', encoding="utf-8")
        lines = []
        for path in sorted(p for p in run.rglob("*") if p.is_file()):
            lines.append(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.relative_to(run).as_posix()}")
        checksums = run / "checksums.sha256"
        checksums.write_text("\n".join(lines) + "\n", encoding="utf-8")
        (run / "COMPLETE").write_text(json.dumps({"checksums_sha256": hashlib.sha256(checksums.read_bytes()).hexdigest()}) + "\n", encoding="utf-8")
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

    def test_undeclared_file_breaks_seal(self) -> None:
        suite = json.loads((ROOT / "suite.json").read_text())
        with tempfile.TemporaryDirectory() as tmp:
            run = self._sealed(Path(tmp), suite["routes"][0])
            (run / "injected.txt").write_text("tamper", encoding="utf-8")
            passed, error = AGG.verify_checksums(run)
        self.assertFalse(passed)
        self.assertIn("inventory mismatch", error)


if __name__ == "__main__":
    unittest.main()
