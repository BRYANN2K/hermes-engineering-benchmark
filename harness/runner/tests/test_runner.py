#!/usr/bin/env python3
"""Behavior tests for the Hermes engineering benchmark runner."""

from __future__ import annotations

import importlib.util
import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "runner.py"
_SPEC = importlib.util.spec_from_file_location("benchmark_runner", RUNNER)
assert _SPEC is not None and _SPEC.loader is not None
RUNNER_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(RUNNER_MODULE)


class RunnerPlanTests(unittest.TestCase):
    def test_dotenv_parser_handles_export_and_quotes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / ".env"
            path.write_text("OTHER=nope\nexport OPENCODE_GO_API_KEY='probe-value'\n", encoding="utf-8")
            self.assertEqual(RUNNER_MODULE.read_dotenv_value(path, "OPENCODE_GO_API_KEY"), "probe-value")
            self.assertIsNone(RUNNER_MODULE.read_dotenv_value(path, "MISSING"))

    def test_trace_requires_applied_cognitive_isolation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            trace = Path(tmp) / "trace.jsonl"
            trace.write_text(
                json.dumps({
                    "sandbox": "hermes-tool-hook",
                    "installed": True,
                    "cognitive_isolation_installed": True,
                    "ephemeral_home": True,
                    "shared_credentials_host_only": True,
                }) + "\n",
                encoding="utf-8",
            )
            self.assertFalse(RUNNER_MODULE.verify_sandbox_trace(trace, enabled=True))

    def test_matrix_dry_run_uses_the_frozen_six_route_matrix(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            starter = tmp_path / "starter"
            starter.mkdir()
            prompt = tmp_path / "prompt.txt"
            prompt.write_text("Implement the task.\n", encoding="utf-8")

            completed = subprocess.run(
                [
                    sys.executable,
                    str(RUNNER),
                    "matrix",
                    "--starter",
                    str(starter),
                    "--prompt-file",
                    str(prompt),
                    "--task-id",
                    "task-001",
                    "--grader",
                    "/grader/not-run",
                    "--dry-run",
                ],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            plan = json.loads(completed.stdout)
            pairs = [(item["provider"], item["model"]) for item in plan["runs"]]
            self.assertEqual(
                pairs,
                [
                    ("openai-codex", "gpt-5.6-sol"),
                    ("openai-codex", "gpt-daybreak-blue-latest"),
                    ("openai-codex", "gpt-5.6-terra"),
                    ("openai-codex", "gpt-5.6-luna"),
                    ("opencode-go", "deepseek-v4-flash"),
                    ("opencode-go", "deepseek-v4-pro"),
                ],
            )
            self.assertTrue(all(item["reasoning"] == "high" for item in plan["runs"]))
            self.assertTrue(all(item["toolsets"] == "terminal,file" for item in plan["runs"]))
            self.assertTrue(all(item["timeout_seconds"] == 1800.0 for item in plan["runs"]))
            self.assertFalse((ROOT / "runs").exists())


class RunnerExecutionTests(unittest.TestCase):
    def _write_executable(self, path: Path, content: str) -> None:
        path.write_text(content, encoding="utf-8")
        path.chmod(path.stat().st_mode | stat.S_IXUSR)

    def _make_fixture(self, tmp_path: Path) -> tuple[Path, Path, Path, Path, Path]:
        starter = tmp_path / "starter"
        starter.mkdir()
        subprocess.run(["git", "init", "-q", str(starter)], check=True)
        subprocess.run(["git", "-C", str(starter), "config", "user.email", "bench@example.invalid"], check=True)
        subprocess.run(["git", "-C", str(starter), "config", "user.name", "Benchmark Test"], check=True)
        (starter / "answer.txt").write_text("before\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(starter), "add", "answer.txt"], check=True)
        subprocess.run(["git", "-C", str(starter), "commit", "-qm", "starter"], check=True)

        prompt = tmp_path / "prompt.txt"
        prompt.write_text("Change answer.txt.\n", encoding="utf-8")
        mock_hermes = tmp_path / "mock-hermes.py"
        self._write_executable(
            mock_hermes,
            """#!/usr/bin/env python3
import json, os, pathlib, sys
args = sys.argv[1:]
assert pathlib.Path(os.environ["HERMES_HOME"]).name == ".hermes-home"
assert args[args.index(\"--reasoning\") + 1] == \"high\"
assert args[args.index(\"--toolsets\") + 1] == \"terminal,file\"
provider = args[args.index(\"--provider\") + 1]
model = args[args.index(\"--model\") + 1]
usage = pathlib.Path(args[args.index(\"--usage-file\") + 1])
pathlib.Path(\"answer.txt\").write_text(f\"after:{provider}:{model}\\n\", encoding=\"utf-8\")
usage.write_text(json.dumps({\"provider\": provider, \"model\": model, \"input_tokens\": 12, \"output_tokens\": 3, \"total_tokens\": 15, \"api_calls\": 1, \"completed\": True, \"failed\": False}) + \"\\n\", encoding=\"utf-8\")
print(f\"mock final for {model}\")
""",
        )
        grader = tmp_path / "grader.py"
        self._write_executable(
            grader,
            """#!/usr/bin/env python3
import json, pathlib, sys
workspace = pathlib.Path(sys.argv[1])
assert sys.argv[2:] == [\"--hidden-mode\", \"strict\"]
passed = workspace.joinpath(\"answer.txt\").read_text(encoding=\"utf-8\").startswith(\"after:\")
print(json.dumps({\"passed\": passed, \"score\": 1.0 if passed else 0.0, \"details\": {\"hidden\": True}}))
""",
        )
        runs = tmp_path / "runs"
        return starter, prompt, mock_hermes, grader, runs

    def test_run_captures_complete_immutable_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            starter, prompt, mock_hermes, grader, runs = self._make_fixture(Path(tmp))
            completed = subprocess.run(
                [
                    sys.executable,
                    str(RUNNER),
                    "run",
                    "--starter", str(starter),
                    "--prompt-file", str(prompt),
                    "--task-id", "task-001",
                    "--grader", str(grader),
                    "--grader-arg=--hidden-mode",
                    "--grader-arg=strict",
                    "--provider", "openai-codex",
                    "--model", "gpt-5.6-sol",
                    "--runs-root", str(runs),
                    "--hermes", str(mock_hermes), "--no-tool-sandbox", "--no-grader-sandbox",
                ],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            summary = json.loads(completed.stdout)
            run_dir = Path(summary["run_dir"])
            self.assertEqual(run_dir.parent, runs)
            expected = {
                "manifest.json", "prompt.txt", "stdout.txt", "stderr.txt",
                "usage.json", "timing.json", "exit_status.json", "git.diff",
                "git.patch", "git-status.txt", "grader.stdout.txt",
                "grader.stderr.txt", "result.json", "checksums.sha256", "COMPLETE",
            }
            self.assertTrue(expected.issubset({p.name for p in run_dir.iterdir()}))
            self.assertTrue((run_dir / "schemas" / "manifest.schema.json").is_file())
            self.assertTrue((run_dir / "schemas" / "result.schema.json").is_file())
            manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
            schema = json.loads((run_dir / "schemas" / "manifest.schema.json").read_text(encoding="utf-8"))
            for key in ("benchmark_freeze", "task", "hermes", "limits", "environment", "grader", "pricing"):
                declared = set(schema["properties"][key]["properties"])
                self.assertEqual(set(manifest[key]), declared)
            self.assertEqual(manifest["hermes"]["provider"], "openai-codex")
            self.assertEqual(manifest["hermes"]["runtime_verification"], "not_applicable_mock")
            self.assertIsNone(manifest["hermes"]["runtime_manifest_sha256"])
            self.assertEqual(manifest["benchmark_freeze"]["status"], "not_applicable_mock")
            self.assertIsNone(manifest["benchmark_freeze"]["source_tree_sha256"])
            self.assertEqual(manifest["limits"]["max_turns"], 90)
            self.assertEqual(manifest["environment"]["HERMES_HOME"], "ephemeral-per-run")
            self.assertFalse((run_dir / ".hermes-home").exists())
            result = json.loads((run_dir / "result.json").read_text(encoding="utf-8"))
            self.assertTrue(result["grader"]["passed"])
            self.assertTrue(result["outcome"]["success"])
            self.assertIn("after:openai-codex:gpt-5.6-sol", (run_dir / "git.diff").read_text(encoding="utf-8"))
            self.assertFalse(os.access(run_dir / "manifest.json", os.W_OK))
            self.assertEqual(
                [path.relative_to(run_dir).as_posix() if path != run_dir else "." for path in [run_dir, *run_dir.rglob("*")] if path.stat().st_mode & 0o222],
                [],
            )
            # The verifier must reject files added outside the sealed inventory.
            run_dir.chmod(run_dir.stat().st_mode | stat.S_IWUSR)
            extra = run_dir / "undeclared.txt"
            extra.write_text("tamper\n", encoding="utf-8")
            module_spec = __import__("importlib.util").util.spec_from_file_location("runner_module", RUNNER)
            runner_module = __import__("importlib.util").util.module_from_spec(module_spec)
            module_spec.loader.exec_module(runner_module)
            verified, error = runner_module.verify_checksums(run_dir)
            self.assertFalse(verified)
            self.assertIn("inventory mismatch", error)

    def test_relative_grader_path_executes_from_run_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            starter, prompt, mock_hermes, grader, runs = self._make_fixture(tmp_path)
            relative_grader = grader.relative_to(tmp_path)
            completed = subprocess.run(
                [
                    sys.executable, str(RUNNER), "run",
                    "--starter", str(starter), "--prompt-file", str(prompt),
                    "--task-id", "task-relative-grader",
                    "--grader", str(relative_grader),
                    "--grader-arg=--hidden-mode", "--grader-arg=strict",
                    "--provider", "openai-codex", "--model", "gpt-5.6-sol",
                    "--runs-root", str(runs), "--hermes", str(mock_hermes), "--no-tool-sandbox", "--no-grader-sandbox",
                ],
                cwd=tmp_path,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            result = json.loads(completed.stdout)["result"]
            self.assertTrue(result["outcome"]["grader_completed"])
            self.assertTrue(result["outcome"]["passed"])

    def test_rejected_candidate_is_a_completed_grade(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            starter, prompt, mock_hermes, grader, runs = self._make_fixture(tmp_path)
            grader.write_text(
                "#!/usr/bin/env python3\n"
                "import json\n"
                "print(json.dumps({'passed': False, 'score': 0.0, 'max_score': 1.0}))\n"
                "raise SystemExit(1)\n",
                encoding="utf-8",
            )
            grader.chmod(grader.stat().st_mode | stat.S_IXUSR)
            completed = subprocess.run(
                [
                    sys.executable, str(RUNNER), "run",
                    "--starter", str(starter), "--prompt-file", str(prompt),
                    "--task-id", "task-rejected", "--grader", str(grader),
                    "--provider", "openai-codex", "--model", "gpt-5.6-sol",
                    "--runs-root", str(runs), "--hermes", str(mock_hermes),
                    "--no-tool-sandbox", "--no-grader-sandbox",
                ],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            result = json.loads(completed.stdout)["result"]
            self.assertTrue(result["outcome"]["grader_completed"])
            self.assertFalse(result["outcome"]["passed"])
            self.assertFalse(result["outcome"]["success"])

    def test_timeout_kills_the_process_group_and_still_runs_grader(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            starter, prompt, mock_hermes, grader, runs = self._make_fixture(Path(tmp))
            mock_hermes.write_text(
                "#!/usr/bin/env python3\nimport time\ntime.sleep(60)\n",
                encoding="utf-8",
            )
            mock_hermes.chmod(mock_hermes.stat().st_mode | stat.S_IXUSR)
            completed = subprocess.run(
                [
                    sys.executable, str(RUNNER), "run",
                    "--starter", str(starter), "--prompt-file", str(prompt),
                    "--task-id", "task-timeout", "--grader", str(grader),
                    "--grader-arg=--hidden-mode", "--grader-arg=strict",
                    "--provider", "openai-codex", "--model", "gpt-5.6-sol",
                    "--runs-root", str(runs), "--hermes", str(mock_hermes), "--no-tool-sandbox", "--no-grader-sandbox",
                    "--timeout", "0.1",
                ],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            run_dir = Path(json.loads(completed.stdout)["run_dir"])
            statuses = json.loads((run_dir / "exit_status.json").read_text(encoding="utf-8"))
            self.assertTrue(statuses["hermes"]["timed_out"])
            self.assertIn("grader", statuses)
            usage = json.loads((run_dir / "usage.json").read_text(encoding="utf-8"))
            self.assertIsNone(usage["input_tokens"])
            result = json.loads((run_dir / "result.json").read_text(encoding="utf-8"))
            self.assertFalse(result["outcome"]["success"])

    def test_matrix_mock_runs_all_models_in_parallel_with_unique_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            starter, prompt, mock_hermes, grader, runs = self._make_fixture(Path(tmp))
            completed = subprocess.run(
                [
                    sys.executable, str(RUNNER), "matrix",
                    "--starter", str(starter), "--prompt-file", str(prompt),
                    "--task-id", "task-matrix", "--grader", str(grader),
                    "--grader-arg=--hidden-mode", "--grader-arg=strict",
                    "--runs-root", str(runs), "--hermes", str(mock_hermes), "--no-tool-sandbox", "--no-grader-sandbox",
                    "--jobs", "6", "--batch-id", "mock-batch",
                ],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            summary = json.loads(completed.stdout)
            self.assertEqual(summary["errors"], [])
            self.assertEqual(len(summary["runs"]), 6)
            run_dirs = [Path(item["run_dir"]) for item in summary["runs"]]
            self.assertEqual(len({path.name for path in run_dirs}), 6)
            self.assertTrue(all(path.joinpath("COMPLETE").is_file() for path in run_dirs))
            requested = [
                json.loads(path.joinpath("manifest.json").read_text(encoding="utf-8"))["hermes"]["model"]
                for path in run_dirs
            ]
            self.assertEqual(
                requested,
                [
                    "gpt-5.6-sol",
                    "gpt-daybreak-blue-latest",
                    "gpt-5.6-terra",
                    "gpt-5.6-luna",
                    "deepseek-v4-flash",
                    "deepseek-v4-pro",
                ],
            )

    def test_fixed_run_key_refuses_overwrite_and_resume_reuses_complete_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            starter, prompt, mock_hermes, grader, runs = self._make_fixture(Path(tmp))
            base = [
                sys.executable, str(RUNNER), "run",
                "--starter", str(starter), "--prompt-file", str(prompt),
                "--task-id", "task-001", "--grader", str(grader),
                "--grader-arg=--hidden-mode", "--grader-arg=strict",
                "--provider", "openai-codex", "--model", "gpt-5.6-sol",
                "--runs-root", str(runs), "--hermes", str(mock_hermes), "--no-tool-sandbox", "--no-grader-sandbox",
                "--run-key", "fixed-key",
            ]
            first = subprocess.run(base, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.assertEqual(first.returncode, 0, first.stderr)
            second = subprocess.run(base, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.assertNotEqual(second.returncode, 0)
            self.assertIn("already exists", second.stderr)
            resumed = subprocess.run(base + ["--resume"], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.assertEqual(resumed.returncode, 0, resumed.stderr)
            self.assertEqual(json.loads(resumed.stdout)["status"], "already_complete")

    def test_resume_incomplete_run_rejects_changed_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            starter, prompt, mock_hermes, grader, runs = self._make_fixture(Path(tmp))
            run_dir = runs / "interrupted-key"
            run_dir.mkdir(parents=True)
            request = {
                "schema_version": "1.0",
                "task_id": "task-001",
                "attempt": 1,
                "provider": "openai-codex",
                "model": "gpt-5.6-sol",
                "reasoning": "high",
                "toolsets": "terminal,file",
                "timeout_seconds": 1800.0,
                "grader_timeout_seconds": 300.0,
                "max_turns": 90,
                "prompt_sha256": "0" * 64,
                "starter_sha256": "0" * 64,
                "grader_sha256": "0" * 64,
                "hermes_executable": str(mock_hermes.resolve()),
                "grader_executable": str(grader.resolve()),
                "grader_arguments": ["--hidden-mode", "strict"],
            }
            (run_dir / "request.json").write_text(json.dumps(request) + "\n", encoding="utf-8")
            completed = subprocess.run(
                [
                    sys.executable, str(RUNNER), "run",
                    "--starter", str(starter), "--prompt-file", str(prompt),
                    "--task-id", "task-001", "--grader", str(grader),
                    "--grader-arg=--hidden-mode", "--grader-arg=strict",
                    "--provider", "openai-codex", "--model", "gpt-5.6-sol",
                    "--runs-root", str(runs), "--hermes", str(mock_hermes), "--no-tool-sandbox", "--no-grader-sandbox",
                    "--run-key", "interrupted-key", "--resume",
                ],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("resume inputs differ", completed.stderr)


if __name__ == "__main__":
    unittest.main()
