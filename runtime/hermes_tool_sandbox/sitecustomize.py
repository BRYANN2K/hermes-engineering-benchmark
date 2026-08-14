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

    shared_auth_text = os.environ.get("HEB_SHARED_AUTH_FILE", "")
    try:
        shared_auth = Path(shared_auth_text).resolve(strict=True)
        if not shared_auth.is_file():
            raise RuntimeError("shared credential store is not a regular file")
    except Exception as exc:
        os.write(2, f"HEB credential isolation initialization failed: {exc}\n".encode())
        os._exit(126)

    # Authentication is the sole shared state. Override the auth module before
    # oneshot resolves a provider so OAuth refreshes remain coherent across
    # workers while config, sessions, memory, and skills stay in the disposable
    # per-run HERMES_HOME. Tool subprocesses never receive this path and are
    # independently Landlocked to the task workspace.
    from hermes_cli import auth as auth_mod

    auth_mod._auth_file_path = lambda: shared_auth
    auth_mod._auth_lock_path = lambda: shared_auth.with_suffix(".lock")
    auth_mod._global_auth_file_path = lambda: None

    # Hermes -z normally behaves like a normal chat turn and can load memory
    # and project context. Force cognitive isolation at the AIAgent constructor
    # boundary, then attest the applied values when the main agent is built.
    from run_agent import AIAgent

    original_agent_init = AIAgent.__init__

    def isolated_agent_init(self, *args, **kwargs):
        kwargs["skip_memory"] = True
        kwargs["skip_context_files"] = True
        kwargs["load_soul_identity"] = False
        kwargs["fallback_model"] = None
        with trace.open("a", encoding="utf-8") as stream:
            stream.write(
                json.dumps(
                    {
                        "sandbox": "hermes-cognitive-isolation",
                        "applied": True,
                        "skip_memory": True,
                        "skip_context_files": True,
                        "load_soul_identity": False,
                        "fallback_disabled": True,
                    },
                    separators=(",", ":"),
                )
                + "\n"
            )
        return original_agent_init(self, *args, **kwargs)

    AIAgent.__init__ = isolated_agent_init
    AIAgent._heb_cognitive_isolation_installed = True

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
        stream.write(
            json.dumps(
                {
                    "sandbox": "hermes-tool-hook",
                    "installed": True,
                    "cognitive_isolation_installed": True,
                    "ephemeral_home": True,
                    "shared_credentials_host_only": True,
                },
                separators=(",", ":"),
            )
            + "\n"
        )


_install()