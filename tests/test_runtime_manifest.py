#!/usr/bin/env python3
"""Tests for the external Hermes runtime fingerprint."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "verify_hermes_runtime.py"


class HermesRuntimeManifestTests(unittest.TestCase):
    def make_runtime(self, root: Path) -> None:
        (root / "bin").mkdir(parents=True)
        (root / ".venv" / "bin").mkdir(parents=True)
        for directory in ("agent", "hermes_cli", "tools"):
            (root / directory).mkdir()
        (root / "bin" / "hermes").write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        (root / ".venv" / "bin" / "hermes").write_text("#!/usr/bin/env python3\n", encoding="utf-8")
        (root / ".venv" / "bin" / "python").symlink_to(Path(sys.executable).resolve())
        (root / "pyproject.toml").write_text("[project]\nname='fixture'\nversion='1.0'\n", encoding="utf-8")
        (root / "uv.lock").write_text("version = 1\n", encoding="utf-8")
        (root / "run_agent.py").write_text("VALUE = 1\n", encoding="utf-8")
        (root / "agent" / "core.py").write_text("VALUE = 2\n", encoding="utf-8")
        (root / "hermes_cli" / "main.py").write_text("VALUE = 3\n", encoding="utf-8")
        (root / "tools" / "local.py").write_text("VALUE = 4\n", encoding="utf-8")

    def test_write_verify_and_detect_runtime_drift(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            runtime = base / "runtime"
            manifest = base / "manifest.json"
            self.make_runtime(runtime)
            write = subprocess.run(
                [sys.executable, str(SCRIPT), "write", "--hermes-root", str(runtime), "--manifest", str(manifest)],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            self.assertEqual(write.returncode, 0, write.stderr)
            payload = json.loads(manifest.read_text(encoding="utf-8"))
            self.assertEqual(payload["file_count"], 8)
            verified = subprocess.run(
                [sys.executable, str(SCRIPT), "verify", "--hermes-root", str(runtime), "--manifest", str(manifest)],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            self.assertEqual(verified.returncode, 0, verified.stderr)
            (runtime / "agent" / "core.py").write_text("VALUE = 99\n", encoding="utf-8")
            drift = subprocess.run(
                [sys.executable, str(SCRIPT), "verify", "--hermes-root", str(runtime), "--manifest", str(manifest)],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            self.assertNotEqual(drift.returncode, 0)
            self.assertFalse(json.loads(drift.stdout)["verified"])


if __name__ == "__main__":
    unittest.main()
