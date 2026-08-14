"""Confine Hermes local terminal and file tools for benchmark runs.

Loaded only when the campaign runner prepends this directory to PYTHONPATH.
The Hermes process itself keeps network access for model API calls; every
LocalEnvironment child command is wrapped in the benchmark's fail-closed
Landlock/seccomp/network-namespace sandbox.
"""

from __future__ import annotations

import os
import json
from pathlib import Path
import subprocess


def _install() -> None:
    if os.environ.get("HEB_TOOL_SANDBOX") != "1":
        return

    workspace_text = os.environ.get("HERMES_WRITE_SAFE_ROOT", "")
    sandbox_text = os.environ.get("HEB_SANDBOX_RUN", "")
    try:
        if not workspace_text or os.pathsep in workspace_text:
            raise RuntimeError("benchmark tool sandbox requires exactly one write-safe root")
        workspace = Path(workspace_text).resolve(strict=True)
        sandbox = Path(sandbox_text).resolve(strict=True)
        trace = Path(os.environ["HEB_SANDBOX_TRACE"]).resolve(strict=False)
        if not workspace.is_dir() or not sandbox.is_file() or not os.access(sandbox, os.X_OK):
            raise RuntimeError("invalid benchmark workspace or sandbox executable")
        if trace.parent != workspace.parent:
            raise RuntimeError("sandbox trace must be a sibling artifact of the workspace")
    except Exception as exc:
        os.write(2, f"HEB tool sandbox initialization failed: {exc}\n".encode())
        os._exit(126)

    from tools.environments.local import LocalEnvironment

    if getattr(LocalEnvironment, "_heb_sandbox_installed", False):
        return

    original = LocalEnvironment._run_bash
    original_temp_dir = LocalEnvironment.get_temp_dir

    def sandboxed_run_bash(
        self,
        cmd_string: str,
        *,
        login: bool = False,
        timeout: int = 120,
        stdin_data: str | None = None,
    ) -> subprocess.Popen:
        bash = "/usr/bin/bash"
        bash_args = [bash, "-l", "-c", cmd_string] if login else [bash, "-c", cmd_string]
        args = [str(sandbox), str(workspace), *bash_args]
        run_env = os.environ.copy()
        run_env["SANDBOX_CPU_SECONDS"] = str(max(30, timeout + 5))
        proc = subprocess.Popen(
            args,
            text=True,
            env=run_env,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=subprocess.PIPE if stdin_data is not None else subprocess.DEVNULL,
            start_new_session=True,
            cwd=str(workspace),
        )
        if stdin_data is not None:
            from tools.environments.base import _pipe_stdin

            _pipe_stdin(proc, stdin_data)
        try:
            proc._hermes_pgid = os.getpgid(proc.pid)
        except ProcessLookupError:
            pass
        return proc

    LocalEnvironment._run_bash = sandboxed_run_bash
    LocalEnvironment.get_temp_dir = lambda self: str(workspace)
    LocalEnvironment._heb_sandbox_installed = True
    LocalEnvironment._heb_original_run_bash = original
    LocalEnvironment._heb_original_get_temp_dir = original_temp_dir
    with trace.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps({"sandbox": "hermes-tool-hook", "installed": True}, separators=(",", ":")) + "\n")


_install()