#!/usr/bin/env python3
"""Run reproducible Hermes engineering benchmarks and freeze their artifacts."""

from __future__ import annotations

import argparse
import concurrent.futures
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import signal
import stat
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Any, Iterable


SCHEMA_VERSION = "1.0"
MODELS = (
    ("openai-codex", "gpt-5.6-sol"),
    ("openai-codex", "gpt-daybreak-blue-latest"),
    ("openai-codex", "gpt-5.6-terra"),
    ("openai-codex", "gpt-5.6-luna"),
    ("opencode-go", "deepseek-v4-flash"),
    ("opencode-go", "deepseek-v4-pro"),
)
DEFAULT_HERMES = Path("/opt/hermes/bin/hermes")
REQUIRED_HERMES_HOME = Path("/opt/data")
REQUIRED_SHARED_AUTH_FILE = REQUIRED_HERMES_HOME / "auth.json"
REQUIRED_SHARED_ENV_FILE = REQUIRED_HERMES_HOME / ".env"
CANDIDATE_ROOT = Path(__file__).resolve().parent
REPOSITORY_ROOT = CANDIDATE_ROOT.parents[1]
HERMES_RUNTIME_MANIFEST = REPOSITORY_ROOT / "runtime" / "hermes-runtime-manifest.json"
HERMES_RUNTIME_VERIFIER = REPOSITORY_ROOT / "scripts" / "verify_hermes_runtime.py"
SOURCE_FREEZE_MANIFEST = REPOSITORY_ROOT / "freeze-manifest.json"
SOURCE_FREEZE_VERIFIER = REPOSITORY_ROOT / "scripts" / "freeze.py"
LANDLOCK_HELPER_HASH_FILE = REPOSITORY_ROOT / "runtime" / "sandbox" / "landlock-run.sha256"
SCHEMA_SOURCE = CANDIDATE_ROOT / "schemas"
DEFAULT_RUNS_ROOT = CANDIDATE_ROOT / "runs"
DEFAULT_TOOL_SANDBOX_HOOK = REPOSITORY_ROOT / "runtime" / "hermes_tool_sandbox"
DEFAULT_SANDBOX_RUN = REPOSITORY_ROOT / "runtime" / "sandbox" / "sandbox-run"
CHECKSUM_EXCLUDES = {"checksums.sha256", "COMPLETE", ".runner.lock"}


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def compact_utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def path_sha256(path: Path) -> str:
    if path.is_symlink():
        payload = b"symlink\0" + os.fsencode(os.readlink(path))
        return hashlib.sha256(payload).hexdigest()
    return file_sha256(path)


def tree_sha256(root: Path, *, exclude_git: bool = True) -> str:
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix()):
        relative = path.relative_to(root)
        if exclude_git and (relative == Path(".git") or ".git" in relative.parts):
            continue
        encoded = relative.as_posix().encode("utf-8", "surrogateescape")
        if path.is_symlink():
            digest.update(b"L\0" + encoded + b"\0" + os.fsencode(os.readlink(path)) + b"\0")
        elif path.is_dir():
            digest.update(b"D\0" + encoded + b"\0")
        elif path.is_file():
            digest.update(b"F\0" + encoded + b"\0")
            with path.open("rb") as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                    digest.update(chunk)
            digest.update(b"\0")
    return digest.hexdigest()


def safe_component(value: str) -> str:
    result = re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("-.")
    if not result or result in {".", ".."}:
        raise ValueError(f"unsafe empty path component derived from {value!r}")
    return result[:100]


def write_text_atomic(path: Path, content: str) -> None:
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    temporary.write_text(content, encoding="utf-8")
    os.replace(temporary, path)


def write_json_atomic(path: Path, value: Any) -> None:
    write_text_atomic(path, json.dumps(value, indent=2, sort_keys=True) + "\n")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def run_capture(command: list[str], *, cwd: Path, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        command,
        cwd=cwd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def git_value(workspace: Path, arguments: list[str]) -> str | None:
    completed = run_capture(["git", *arguments], cwd=workspace)
    if completed.returncode != 0:
        return None
    return completed.stdout.decode("utf-8", "replace").strip() or None


def starter_git_metadata(starter: Path) -> dict[str, Any]:
    return {
        "head": git_value(starter, ["rev-parse", "HEAD"]),
        "tree": git_value(starter, ["rev-parse", "HEAD^{tree}"]),
        "is_dirty": bool(git_value(starter, ["status", "--porcelain=v1", "--untracked-files=all"])),
    }


def hermes_command(args: argparse.Namespace, provider: str, model: str, usage_file: Path) -> list[str]:
    prompt = args.prompt_file.read_text(encoding="utf-8")
    return [
        str(args.hermes),
        "--provider",
        provider,
        "--model",
        model,
        "--reasoning",
        args.reasoning,
        "--toolsets",
        args.toolsets,
        "--usage-file",
        str(usage_file),
        "--safe-mode",
        "-z",
        prompt,
    ]


def benchmark_environment(
    args: argparse.Namespace,
    *,
    enable_tool_sandbox: bool,
    sandbox_trace: Path | None = None,
    provider: str | None = None,
) -> dict[str, str]:
    environment = os.environ.copy()
    # The one-shot agent authenticates through HERMES_HOME. Unrelated gateway,
    # social, MCP, and operator credentials must not reach the benchmark
    # process (or terminal subprocesses it creates).
    for key in list(environment):
        upper = key.upper()
        if any(marker in upper for marker in ("KEY", "TOKEN", "SECRET", "PASSWORD", "CREDENTIAL")):
            environment.pop(key, None)
    environment.update(
        {
            "HERMES_HOME": str(args.ephemeral_hermes_home),
            "HERMES_MAX_ITERATIONS": str(args.max_turns),
            "HERMES_WRITE_SAFE_ROOT": str(args.active_workspace),
            "TERMINAL_CWD": str(args.active_workspace),
            "TERMINAL_ENV": "local",
            "TERMINAL_LOCAL_PERSISTENT": "false",
            "TZ": "UTC",
            "LC_ALL": "C.UTF-8",
            "LANG": "C.UTF-8",
        }
    )
    # Do not inherit arbitrary Python module injection into benchmark or grader
    # processes. The only allowed injection is our frozen tool-sandbox hook,
    # and it is enabled exclusively for the Hermes process (never the grader).
    environment.pop("PYTHONPATH", None)
    environment.pop("PYTHONHOME", None)
    for key in ("HEB_TOOL_SANDBOX", "HEB_SANDBOX_RUN", "HEB_SANDBOX_TRACE", "HEB_SHARED_AUTH_FILE"):
        environment.pop(key, None)
    if enable_tool_sandbox:
        if sandbox_trace is None:
            raise ValueError("sandbox trace path is required when tool sandboxing is enabled")
        environment.update(
            {
                "PYTHONPATH": str(args.tool_sandbox_hook.resolve()),
                "HEB_TOOL_SANDBOX": "1",
                "HEB_SANDBOX_RUN": str(args.sandbox_run.resolve()),
                "HEB_SANDBOX_TRACE": str(sandbox_trace.resolve()),
                "HEB_SHARED_AUTH_FILE": str(REQUIRED_SHARED_AUTH_FILE.resolve()),
            }
        )
        if provider == "opencode-go":
            key = read_dotenv_value(REQUIRED_SHARED_ENV_FILE, "OPENCODE_GO_API_KEY")
            if not key:
                raise ValueError("OpenCode Go credential is unavailable")
            # Host process only. sandbox-run reconstructs a minimal env and
            # HEB_SHARED_* vars are explicitly unset before every tool command.
            environment["OPENCODE_GO_API_KEY"] = key
    return environment


def read_dotenv_value(path: Path, key: str) -> str | None:
    if not path.is_file():
        return None
    prefix = key + "="
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line.startswith("export "):
            line = line[7:].lstrip()
        if not line.startswith(prefix):
            continue
        value = line[len(prefix):].strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        return value or None
    return None


def execute_timed(
    command: list[str],
    *,
    cwd: Path,
    env: dict[str, str],
    stdout_path: Path,
    stderr_path: Path,
    timeout_seconds: float,
) -> tuple[dict[str, Any], dict[str, Any]]:
    started_at = utc_now()
    started_monotonic = time.monotonic()
    timed_out = False
    return_code: int | None = None
    launch_error: str | None = None

    with stdout_path.open("wb") as stdout_stream, stderr_path.open("wb") as stderr_stream:
        process: subprocess.Popen[bytes] | None = None
        try:
            process = subprocess.Popen(
                command,
                cwd=cwd,
                env=env,
                stdin=subprocess.DEVNULL,
                stdout=stdout_stream,
                stderr=stderr_stream,
                start_new_session=True,
            )
            try:
                return_code = process.wait(timeout=timeout_seconds)
            except subprocess.TimeoutExpired:
                timed_out = True
                try:
                    os.killpg(process.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
                try:
                    return_code = process.wait(timeout=3.0)
                except subprocess.TimeoutExpired:
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    return_code = process.wait()
        except OSError as exc:
            launch_error = f"{type(exc).__name__}: {exc}"
            stderr_stream.write((launch_error + "\n").encode("utf-8", "replace"))
            return_code = 127
        finally:
            if process is not None and process.poll() is None:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                process.wait()

    ended_at = utc_now()
    wall_seconds = time.monotonic() - started_monotonic
    status = {
        "return_code": return_code,
        "timed_out": timed_out,
        "launch_error": launch_error,
    }
    timing = {
        "started_at": started_at,
        "ended_at": ended_at,
        "wall_seconds": wall_seconds,
        "timeout_seconds": timeout_seconds,
    }
    return status, timing


def capture_git_evidence(workspace: Path, run_dir: Path) -> dict[str, Any]:
    if git_value(workspace, ["rev-parse", "--is-inside-work-tree"]) != "true":
        message = "starter workspace is not a Git working tree\n"
        write_text_atomic(run_dir / "git-status.txt", message)
        write_text_atomic(run_dir / "git.diff", "")
        write_text_atomic(run_dir / "git.patch", "")
        return {"available": False, "error": message.strip()}

    status = run_capture(
        ["git", "status", "--porcelain=v2", "--branch", "--untracked-files=all"],
        cwd=workspace,
    )
    write_text_atomic(run_dir / "git-status.txt", status.stdout.decode("utf-8", "replace"))

    alternate_index = run_dir / f".git-index-{uuid.uuid4().hex}"
    environment = os.environ.copy()
    environment["GIT_INDEX_FILE"] = str(alternate_index)
    try:
        read_tree = run_capture(["git", "read-tree", "HEAD"], cwd=workspace, env=environment)
        if read_tree.returncode != 0:
            raise RuntimeError(read_tree.stderr.decode("utf-8", "replace").strip())
        add_intent = run_capture(["git", "add", "-N", "-f", "--all", "--"], cwd=workspace, env=environment)
        if add_intent.returncode != 0:
            raise RuntimeError(add_intent.stderr.decode("utf-8", "replace").strip())
        human = run_capture(
            ["git", "diff", "--no-ext-diff", "--no-color", "HEAD", "--"],
            cwd=workspace,
            env=environment,
        )
        binary = run_capture(
            ["git", "diff", "--no-ext-diff", "--no-color", "--binary", "--full-index", "HEAD", "--"],
            cwd=workspace,
            env=environment,
        )
        if human.returncode != 0 or binary.returncode != 0:
            details = (human.stderr + binary.stderr).decode("utf-8", "replace").strip()
            raise RuntimeError(details or "git diff failed")
        (run_dir / "git.diff").write_bytes(human.stdout)
        (run_dir / "git.patch").write_bytes(binary.stdout)
        return {
            "available": True,
            "status_return_code": status.returncode,
            "diff_sha256": file_sha256(run_dir / "git.diff"),
            "patch_sha256": file_sha256(run_dir / "git.patch"),
        }
    except (OSError, RuntimeError) as exc:
        message = f"git evidence capture failed: {exc}\n"
        write_text_atomic(run_dir / "git.diff", message)
        write_text_atomic(run_dir / "git.patch", message)
        return {"available": False, "error": str(exc)}
    finally:
        alternate_index.unlink(missing_ok=True)
        alternate_lock = alternate_index.with_name(alternate_index.name + ".lock")
        alternate_lock.unlink(missing_ok=True)


def grader_command(args: argparse.Namespace, grader_workspace: Path) -> list[str]:
    # The grader runs with cwd set to the run artifact directory, not the
    # runner's invocation directory. Freeze the executable as an absolute path
    # so relative CLI arguments cannot fail only after a paid model run.
    grader = [str(args.grader.resolve()), str(grader_workspace), *args.grader_arg]
    if not args.grader_sandbox:
        return grader
    return [str(args.sandbox_run.resolve()), str(grader_workspace), *grader]


def grader_environment(args: argparse.Namespace) -> dict[str, str]:
    args.ephemeral_hermes_home = args.active_workspace
    environment = benchmark_environment(args, enable_tool_sandbox=False)
    bundle = args.grader_bundle_root.resolve() if args.grader_bundle_root else args.grader.resolve().parent
    # Graders may invoke system runtimes such as Node and may bind a loopback
    # HTTP server. They still run in a fresh network namespace: loopback is the
    # only interface and the host/external network remains unreachable.
    environment["SANDBOX_RO_PATHS"] = f"{bundle}:/usr:/usr/local/bin:/etc/ssl"
    environment["SANDBOX_ALLOW_LOOPBACK"] = "1"
    environment["SANDBOX_PATH"] = "/usr/local/bin:/usr/bin:/bin"
    return environment


def parse_grader_output(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return None, f"{type(exc).__name__}: {exc}"
    if not isinstance(value, dict):
        return None, "grader stdout must be one JSON object"
    return value, None


def prepare_starter_workspace(starter: Path, destination: Path) -> None:
    """Copy content only, then create a private Git baseline for safe diffs.

    The source's ``.git`` metadata is deliberately not copied. A copied Git
    worktree can contain a ``.git`` pointer back to the source and would make
    parallel agents share the source index. A synthetic baseline makes every
    workspace independent and makes the patch contain only benchmark changes.
    """
    shutil.copytree(
        starter,
        destination,
        symlinks=True,
        copy_function=shutil.copy2,
        ignore=shutil.ignore_patterns(".git"),
    )
    environment = os.environ.copy()
    environment.update(
        {
            "GIT_AUTHOR_NAME": "Hermes Benchmark",
            "GIT_AUTHOR_EMAIL": "benchmark@example.invalid",
            "GIT_COMMITTER_NAME": "Hermes Benchmark",
            "GIT_COMMITTER_EMAIL": "benchmark@example.invalid",
            "TZ": "UTC",
        }
    )
    commands = (
        ["git", "init", "-q"],
        ["git", "add", "-f", "--all", "--"],
        ["git", "commit", "-qm", "benchmark starter baseline", "--allow-empty"],
    )
    for command in commands:
        completed = run_capture(command, cwd=destination, env=environment)
        if completed.returncode != 0:
            error = completed.stderr.decode("utf-8", "replace").strip()
            raise RuntimeError(f"failed to prepare private Git baseline: {error}")


def copy_grader_workspace(workspace: Path, destination: Path) -> None:
    shutil.copytree(workspace, destination, symlinks=True, copy_function=shutil.copy2)


def ensure_usage_file(path: Path, status: dict[str, Any]) -> None:
    if path.is_file():
        return
    write_json_atomic(
        path,
        {
            "api_calls": None,
            "cache_read_tokens": None,
            "cache_write_tokens": None,
            "completed": False,
            "cost_source": None,
            "cost_status": "unknown",
            "estimated_cost_usd": None,
            "failed": True,
            "failure": "Hermes did not create the requested usage file",
            "input_tokens": None,
            "model": None,
            "output_tokens": None,
            "provider": None,
            "reasoning_tokens": None,
            "service_tier": None,
            "session_id": None,
            "total_tokens": None,
            "wrapper_exit_status": status,
        },
    )


def make_run_id(args: argparse.Namespace, provider: str, model: str) -> str:
    if args.run_key:
        normalized = safe_component(args.run_key)
        if normalized != args.run_key:
            raise ValueError("--run-key must contain only letters, digits, dot, underscore, or hyphen")
        return normalized
    return "__".join(
        [
            compact_utc_now(),
            safe_component(args.task_id),
            f"a{args.attempt}",
            safe_component(provider),
            safe_component(model),
            uuid.uuid4().hex[:12],
        ]
    )


def source_freeze_identity(args: argparse.Namespace) -> dict[str, Any]:
    if args.hermes.resolve() != DEFAULT_HERMES.resolve():
        return {"status": "not_applicable_mock", "source_tree_sha256": None, "file_count": None}
    payload = read_json(SOURCE_FREEZE_MANIFEST)
    return {
        "status": "verified",
        "source_tree_sha256": payload["source_tree_sha256"],
        "file_count": payload["file_count"],
    }


def request_record(args: argparse.Namespace, provider: str, model: str) -> dict[str, Any]:
    """Build the immutable input identity used to validate resume requests."""
    return {
        "schema_version": SCHEMA_VERSION,
        "task_id": args.task_id,
        "attempt": args.attempt,
        "provider": provider,
        "model": model,
        "reasoning": args.reasoning,
        "toolsets": args.toolsets,
        "timeout_seconds": args.timeout,
        "grader_timeout_seconds": args.grader_timeout,
        "max_turns": args.max_turns,
        "tool_sandbox": args.tool_sandbox,
        "tool_sandbox_hook_sha256": (
            file_sha256(args.tool_sandbox_hook / "sitecustomize.py") if args.tool_sandbox else None
        ),
        "sandbox_run_sha256": file_sha256(args.sandbox_run) if args.tool_sandbox else None,
        "landlock_helper_sha256": (
            file_sha256(args.sandbox_run.parent / "landlock-run") if args.tool_sandbox else None
        ),
        "grader_sandbox": args.grader_sandbox,
        "prompt_sha256": file_sha256(args.prompt_file.resolve()),
        "starter_sha256": tree_sha256(args.starter.resolve()),
        "grader_sha256": file_sha256(args.grader.resolve()),
        "grader_bundle_sha256": (
            tree_sha256(args.grader_bundle_root.resolve())
            if args.grader_bundle_root is not None
            else file_sha256(args.grader.resolve())
        ),
        "hermes_executable": str(args.hermes.resolve()),
        "hermes_runtime_manifest_sha256": (
            file_sha256(HERMES_RUNTIME_MANIFEST) if args.hermes.resolve() == DEFAULT_HERMES.resolve() else None
        ),
        "benchmark_source_tree_sha256": source_freeze_identity(args)["source_tree_sha256"],
        "benchmark_source_file_count": source_freeze_identity(args)["file_count"],
        "grader_executable": str(args.grader.resolve()),
        "grader_arguments": args.grader_arg,
    }


def assert_matching_request(run_dir: Path, current: dict[str, Any]) -> None:
    request_path = run_dir / "request.json"
    if not request_path.is_file():
        raise RuntimeError(f"cannot safely resume: missing request.json in {run_dir}")
    previous = read_json(request_path)
    if previous != current:
        differing = sorted(
            key
            for key in set(previous if isinstance(previous, dict) else {}) | set(current)
            if not isinstance(previous, dict) or previous.get(key) != current.get(key)
        )
        raise RuntimeError(f"resume inputs differ from frozen request: {', '.join(differing)}")


def process_is_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def acquire_lock(run_dir: Path, *, resume: bool) -> Path:
    lock_path = run_dir / ".runner.lock"
    try:
        descriptor = os.open(lock_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        if not resume:
            raise RuntimeError(f"run is locked: {run_dir}")
        try:
            lock_record = read_json(lock_path)
            pid = int(lock_record.get("pid", -1))
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            pid = -1
        if pid > 0 and process_is_alive(pid):
            raise RuntimeError(f"run is still active under pid {pid}: {run_dir}")
        lock_path.unlink(missing_ok=True)
        descriptor = os.open(lock_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
        json.dump({"pid": os.getpid(), "created_at": utc_now()}, stream)
        stream.write("\n")
    return lock_path


def iter_checksum_paths(run_dir: Path) -> Iterable[Path]:
    for path in sorted(run_dir.rglob("*"), key=lambda item: item.relative_to(run_dir).as_posix()):
        if path.name in CHECKSUM_EXCLUDES or path.is_dir():
            continue
        yield path


def write_checksums(run_dir: Path) -> Path:
    lines = []
    for path in iter_checksum_paths(run_dir):
        relative = path.relative_to(run_dir).as_posix()
        lines.append(f"{path_sha256(path)}  {relative}")
    checksum_path = run_dir / "checksums.sha256"
    write_text_atomic(checksum_path, "\n".join(lines) + ("\n" if lines else ""))
    return checksum_path


def verify_checksums(run_dir: Path) -> tuple[bool, str | None]:
    checksum_path = run_dir / "checksums.sha256"
    try:
        declared: set[str] = set()
        for line in checksum_path.read_text(encoding="utf-8").splitlines():
            expected, relative = line.split("  ", 1)
            if relative in declared:
                return False, f"duplicate checksum entry: {relative}"
            declared.add(relative)
            path = run_dir / relative
            if not path.exists() and not path.is_symlink():
                return False, f"missing artifact: {relative}"
            actual = path_sha256(path)
            if actual != expected:
                return False, f"checksum mismatch: {relative}"
        observed = {
            path.relative_to(run_dir).as_posix()
            for path in iter_checksum_paths(run_dir)
        }
        if observed != declared:
            extra = sorted(observed - declared)
            missing = sorted(declared - observed)
            return False, f"artifact inventory mismatch: extra={extra}, missing={missing}"
    except (OSError, ValueError) as exc:
        return False, f"invalid checksum file: {exc}"
    return True, None


def make_read_only(root: Path) -> None:
    paths = sorted(root.rglob("*"), key=lambda item: len(item.parts), reverse=True)
    for path in paths:
        if path.is_symlink():
            continue
        mode = stat.S_IMODE(path.stat().st_mode)
        path.chmod(mode & ~0o222)
    root_mode = stat.S_IMODE(root.stat().st_mode)
    root.chmod(root_mode & ~0o222)


def verify_sandbox_trace(path: Path, *, enabled: bool) -> bool:
    if not enabled:
        return True
    try:
        records = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    except (OSError, json.JSONDecodeError):
        return False
    if not records:
        return False
    first = records[0]
    if (
        first.get("sandbox") != "hermes-tool-hook"
        or first.get("installed") is not True
        or first.get("cognitive_isolation_installed") is not True
        or first.get("ephemeral_home") is not True
        or first.get("shared_credentials_host_only") is not True
    ):
        return False
    cognitive = [record for record in records[1:] if record.get("sandbox") == "hermes-cognitive-isolation"]
    if len(cognitive) != 1:
        return False
    applied = cognitive[0]
    if (
        applied.get("applied") is not True
        or applied.get("skip_memory") is not True
        or applied.get("skip_context_files") is not True
        or applied.get("load_soul_identity") is not False
        or applied.get("fallback_disabled") is not True
    ):
        return False
    return all(
        record == {"sandbox": "landlock-seccomp-netns", "activated": True}
        or (
            record.get("sandbox") == "hermes-tool-hook"
            and record.get("installed") is True
            and record.get("cognitive_isolation_installed") is True
        )
        for record in records[1:]
        if record.get("sandbox") != "hermes-cognitive-isolation"
    )


def completed_summary(run_dir: Path, *, status: str) -> dict[str, Any]:
    result_path = run_dir / "result.json"
    result = read_json(result_path) if result_path.is_file() else None
    return {
        "run_id": run_dir.name,
        "run_dir": str(run_dir.resolve()),
        "status": status,
        "result": result,
    }


def validate_common(args: argparse.Namespace, *, executing: bool) -> None:
    if not args.starter.is_dir():
        raise ValueError(f"starter is not a directory: {args.starter}")
    if not args.prompt_file.is_file():
        raise ValueError(f"prompt file does not exist: {args.prompt_file}")
    if args.timeout <= 0 or args.grader_timeout <= 0:
        raise ValueError("timeouts must be positive")
    if args.max_turns != 90:
        raise ValueError(
            "Hermes v0.20.0 one-shot constructs AIAgent with a 90-turn limit; "
            "only --max-turns 90 can be asserted by this runner"
        )
    if args.attempt < 1:
        raise ValueError("attempt must be >= 1")
    if getattr(args, "jobs", 1) < 1:
        raise ValueError("--jobs must be >= 1")
    safe_component(args.task_id)
    if args.resume and not args.run_key and args.action == "run":
        raise ValueError("--resume requires --run-key for a single run")
    if executing:
        if not args.hermes.is_file() or not os.access(args.hermes, os.X_OK):
            raise ValueError(f"Hermes executable is not executable: {args.hermes}")
        if args.hermes.resolve() == DEFAULT_HERMES.resolve():
            source = subprocess.run(
                [sys.executable, str(SOURCE_FREEZE_VERIFIER), "verify", "--manifest", str(SOURCE_FREEZE_MANIFEST)],
                cwd=REPOSITORY_ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
                timeout=120,
            )
            if source.returncode != 0:
                detail = (source.stdout + source.stderr).strip()
                raise ValueError(f"benchmark source freeze verification failed: {detail}")
            completed = subprocess.run(
                [sys.executable, str(HERMES_RUNTIME_VERIFIER), "verify", "--manifest", str(HERMES_RUNTIME_MANIFEST)],
                cwd=REPOSITORY_ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
                timeout=120,
            )
            if completed.returncode != 0:
                detail = (completed.stdout + completed.stderr).strip()
                raise ValueError(f"Hermes runtime verification failed: {detail}")
        if not args.grader.is_file() or not os.access(args.grader, os.X_OK):
            raise ValueError(f"grader is not executable: {args.grader}")
        if args.grader_bundle_root is not None and not args.grader_bundle_root.is_dir():
            raise ValueError(f"grader bundle root is not a directory: {args.grader_bundle_root}")
        if args.tool_sandbox:
            if not args.tool_sandbox_hook.joinpath("sitecustomize.py").is_file():
                raise ValueError(f"tool sandbox hook is missing: {args.tool_sandbox_hook}")
            if not args.sandbox_run.is_file() or not os.access(args.sandbox_run, os.X_OK):
                raise ValueError(f"sandbox runner is not executable: {args.sandbox_run}")
            helper = args.sandbox_run.parent / "landlock-run"
            if not helper.is_file() or not os.access(helper, os.X_OK):
                raise ValueError(f"compiled sandbox helper is missing: {helper}; run scripts/build-sandbox")
            if not LANDLOCK_HELPER_HASH_FILE.is_file():
                raise ValueError("compiled sandbox helper hash is missing; run scripts/build-sandbox")
            expected_helper_sha256 = LANDLOCK_HELPER_HASH_FILE.read_text(encoding="ascii").strip()
            if not re.fullmatch(r"[0-9a-f]{64}", expected_helper_sha256):
                raise ValueError("compiled sandbox helper hash is invalid")
            if file_sha256(helper) != expected_helper_sha256:
                raise ValueError("compiled sandbox helper does not match its frozen hash")
            if not REQUIRED_SHARED_AUTH_FILE.is_file():
                raise ValueError("shared Hermes credential store is unavailable")
        if args.grader_sandbox:
            if not args.sandbox_run.is_file() or not os.access(args.sandbox_run, os.X_OK):
                raise ValueError(f"grader sandbox runner is not executable: {args.sandbox_run}")
            helper = args.sandbox_run.parent / "landlock-run"
            if not helper.is_file() or not os.access(helper, os.X_OK):
                raise ValueError(f"compiled grader sandbox helper is missing: {helper}")


def build_manifest(
    args: argparse.Namespace,
    *,
    run_id: str,
    provider: str,
    model: str,
    starter_digest: str,
    starter_git: dict[str, Any],
    grader_digest: str,
    grader_bundle_digest: str,
    command: list[str],
    git_evidence: dict[str, Any],
    created_at: str,
) -> dict[str, Any]:
    return {
        "$schema": "https://example.invalid/hermes-engineering-bench/manifest.schema.json",
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "created_at": created_at,
        "benchmark_freeze": source_freeze_identity(args),
        "task": {
            "task_id": args.task_id,
            "attempt": args.attempt,
            "prompt_sha256": file_sha256(args.prompt_file),
            "starter_sha256": starter_digest,
            "starter_git": starter_git,
        },
        "hermes": {
            "executable": str(args.hermes.resolve()),
            "runtime_manifest_sha256": (
                file_sha256(HERMES_RUNTIME_MANIFEST) if args.hermes.resolve() == DEFAULT_HERMES.resolve() else None
            ),
            "runtime_verification": (
                "verified" if args.hermes.resolve() == DEFAULT_HERMES.resolve() else "not_applicable_mock"
            ),
            "provider": provider,
            "model": model,
            "reasoning": args.reasoning,
            "toolsets": args.toolsets,
            "safe_mode": True,
            "command": command,
        },
        "limits": {
            "wall_seconds": args.timeout,
            "grader_wall_seconds": args.grader_timeout,
            "max_turns": args.max_turns,
        },
        "environment": {
            "HERMES_HOME": "ephemeral-per-run",
            "HERMES_MAX_ITERATIONS": str(args.max_turns),
            "TZ": "UTC",
            "LC_ALL": "C.UTF-8",
            "agent_tool_sandbox": {
                "enabled": args.tool_sandbox,
                "hook_sha256": file_sha256(args.tool_sandbox_hook / "sitecustomize.py") if args.tool_sandbox else None,
                "sandbox_run_sha256": file_sha256(args.sandbox_run) if args.tool_sandbox else None,
                "landlock_helper_sha256": file_sha256(args.sandbox_run.parent / "landlock-run") if args.tool_sandbox else None,
                "network_policy": "agent tools have no sockets; Hermes host process retains model API egress",
                "cognitive_isolation": "skip_memory + skip_context_files + no soul identity + no fallback",
                "credential_policy": "shared host-only auth store; path withheld from tools and artifacts",
            },
            "grader_sandbox": {
                "enabled": args.grader_sandbox,
                "network_policy": "external egress disabled; isolated loopback enabled for local HTTP tests",
                "workspace_policy": "disposable writable copy; hidden grader bundle read-only",
            },
        },
        "grader": {
            "executable": str(args.grader.resolve()),
            "sha256": grader_digest,
            "bundle_sha256": grader_bundle_digest,
            "arguments": args.grader_arg,
            "interface": "grader WORKSPACE [ARG ...] -> one JSON object on stdout",
        },
        "git_evidence": git_evidence,
        "pricing": {
            "normalized_api_cost_usd": None,
            "price_snapshot_id": None,
            "status": "not_configured",
        },
    }


def run_one(args: argparse.Namespace, provider: str, model: str) -> dict[str, Any]:
    if (provider, model) not in MODELS:
        raise ValueError(f"unlisted provider/model pair: {provider}/{model}")

    run_id = make_run_id(args, provider, model)
    run_dir = args.runs_root.resolve() / run_id
    complete_path = run_dir / "COMPLETE"
    current_request = request_record(args, provider, model)

    if run_dir.exists():
        if not args.resume:
            raise RuntimeError(f"run directory already exists; refusing overwrite: {run_dir}")
        assert_matching_request(run_dir, current_request)
        if complete_path.is_file():
            valid, error = verify_checksums(run_dir)
            if not valid:
                raise RuntimeError(f"completed run failed checksum verification: {error}")
            return completed_summary(run_dir, status="already_complete")
    else:
        if args.resume:
            raise RuntimeError(f"cannot resume missing run directory: {run_dir}")
        args.runs_root.mkdir(parents=True, exist_ok=True)
        run_dir.mkdir(mode=0o700)
        write_json_atomic(run_dir / "request.json", current_request)

    lock_path = acquire_lock(run_dir, resume=args.resume)
    finalized = False
    try:
        created_at = utc_now()
        workspace = run_dir / "workspace"
        args.active_workspace = workspace.resolve()
        ephemeral_home = run_dir / ".hermes-home"
        args.ephemeral_hermes_home = ephemeral_home.resolve()
        state_path = run_dir / "state.json"
        if not workspace.exists():
            prepare_starter_workspace(args.starter.resolve(), workspace)
            write_json_atomic(state_path, {"schema_version": SCHEMA_VERSION, "stage": "prepared", "updated_at": utc_now()})

        starter_digest = tree_sha256(args.starter.resolve())
        starter_git = starter_git_metadata(args.starter.resolve())
        grader_digest = file_sha256(args.grader.resolve())
        grader_bundle_digest = (
            tree_sha256(args.grader_bundle_root.resolve())
            if args.grader_bundle_root is not None
            else grader_digest
        )
        usage_path = run_dir / "usage.json"
        sandbox_trace_path = run_dir / "tool-sandbox.jsonl"
        stdout_path = run_dir / "stdout.txt"
        stderr_path = run_dir / "stderr.txt"
        exit_status_path = run_dir / "exit_status.json"
        timing_path = run_dir / "timing.json"
        command = hermes_command(args, provider, model, usage_path)

        exit_status = read_json(exit_status_path) if exit_status_path.is_file() else {}
        timings = read_json(timing_path) if timing_path.is_file() else {}
        if "hermes" not in exit_status:
            ephemeral_home.mkdir(mode=0o700)
            try:
                hermes_status, hermes_timing = execute_timed(
                    command,
                    cwd=workspace,
                    env=benchmark_environment(
                        args,
                        enable_tool_sandbox=args.tool_sandbox,
                        sandbox_trace=sandbox_trace_path,
                        provider=provider,
                    ),
                    stdout_path=stdout_path,
                    stderr_path=stderr_path,
                    timeout_seconds=args.timeout,
                )
            finally:
                shutil.rmtree(ephemeral_home, ignore_errors=True)
            if ephemeral_home.exists():
                raise RuntimeError("ephemeral Hermes home survived agent execution")
            exit_status["hermes"] = hermes_status
            timings["hermes"] = hermes_timing
            ensure_usage_file(usage_path, hermes_status)
            write_json_atomic(exit_status_path, exit_status)
            write_json_atomic(timing_path, timings)
        else:
            ensure_usage_file(usage_path, exit_status["hermes"])
        write_json_atomic(state_path, {"schema_version": SCHEMA_VERSION, "stage": "hermes_complete", "updated_at": utc_now()})

        shutil.copy2(args.prompt_file, run_dir / "prompt.txt")
        git_evidence = capture_git_evidence(workspace, run_dir)
        write_json_atomic(state_path, {"schema_version": SCHEMA_VERSION, "stage": "evidence_complete", "updated_at": utc_now()})

        grader_stdout = run_dir / "grader.stdout.txt"
        grader_stderr = run_dir / "grader.stderr.txt"
        if "grader" not in exit_status:
            grader_workspace = run_dir / ".grader-workspace"
            if grader_workspace.exists():
                shutil.rmtree(grader_workspace)
            copy_grader_workspace(workspace, grader_workspace)
            try:
                grader_status, grader_timing = execute_timed(
                    grader_command(args, grader_workspace),
                    cwd=run_dir,
                    env=grader_environment(args),
                    stdout_path=grader_stdout,
                    stderr_path=grader_stderr,
                    timeout_seconds=args.grader_timeout,
                )
            finally:
                shutil.rmtree(grader_workspace, ignore_errors=True)
            exit_status["grader"] = grader_status
            timings["grader"] = grader_timing
            write_json_atomic(exit_status_path, exit_status)
            write_json_atomic(timing_path, timings)

        grader_result, grader_parse_error = parse_grader_output(grader_stdout)
        manifest = build_manifest(
            args,
            run_id=run_id,
            provider=provider,
            model=model,
            starter_digest=starter_digest,
            starter_git=starter_git,
            grader_digest=grader_digest,
            grader_bundle_digest=grader_bundle_digest,
            command=command,
            git_evidence=git_evidence,
            created_at=created_at,
        )
        write_json_atomic(run_dir / "manifest.json", manifest)

        sandbox_trace_verified = verify_sandbox_trace(sandbox_trace_path, enabled=args.tool_sandbox)
        hermes_ok = (
            exit_status["hermes"].get("return_code") == 0
            and not exit_status["hermes"].get("timed_out")
            and sandbox_trace_verified
        )
        grader_return_code = exit_status["grader"].get("return_code")
        # Exit 1 is the normal deterministic-grader signal for a rejected
        # candidate. It is a completed grade, not an infrastructure failure.
        grader_ok = (
            grader_return_code in (0, 1)
            and not exit_status["grader"].get("timed_out")
            and isinstance(grader_result, dict)
            and grader_parse_error is None
            and isinstance(grader_result.get("passed"), bool)
        )
        passed = grader_result.get("passed") if isinstance(grader_result, dict) else None
        result = {
            "$schema": "https://example.invalid/hermes-engineering-bench/result.schema.json",
            "schema_version": SCHEMA_VERSION,
            "run_id": run_id,
            "model": {"provider": provider, "requested_id": model},
            "task": {"task_id": args.task_id, "attempt": args.attempt},
            "outcome": {
                "success": bool(hermes_ok and grader_ok and passed is True),
                "passed": passed if isinstance(passed, bool) else None,
                "score": grader_result.get("score") if isinstance(grader_result, dict) else None,
                "hermes_completed": hermes_ok,
                "grader_completed": grader_ok,
                "tool_sandbox_verified": sandbox_trace_verified,
            },
            "grader": grader_result,
            "grader_parse_error": grader_parse_error,
            "usage_file": "usage.json",
            "exit_status_file": "exit_status.json",
            "timing_file": "timing.json",
        }
        write_json_atomic(run_dir / "result.json", result)
        run_schemas = run_dir / "schemas"
        if run_schemas.exists():
            shutil.rmtree(run_schemas)
        shutil.copytree(SCHEMA_SOURCE, run_schemas, copy_function=shutil.copy2)
        write_json_atomic(state_path, {"schema_version": SCHEMA_VERSION, "stage": "artifacts_complete", "updated_at": utc_now()})

        lock_path.unlink(missing_ok=True)
        checksum_path = write_checksums(run_dir)
        write_json_atomic(
            complete_path,
            {
                "schema_version": SCHEMA_VERSION,
                "completed_at": utc_now(),
                "checksums_file": checksum_path.name,
                "checksums_sha256": file_sha256(checksum_path),
                "permission_lock": "all write bits removed recursively",
            },
        )
        make_read_only(run_dir)
        finalized = True
        return completed_summary(run_dir, status="completed")
    finally:
        if not finalized:
            try:
                lock_path.unlink(missing_ok=True)
            except OSError:
                pass


def planned_run(args: argparse.Namespace, provider: str, model: str, run_key: str | None = None) -> dict[str, Any]:
    placeholder = args.runs_root / (run_key or "<unique-run-id>") / "usage.json"
    return {
        "provider": provider,
        "model": model,
        "reasoning": args.reasoning,
        "toolsets": args.toolsets,
        "timeout_seconds": args.timeout,
        "grader_timeout_seconds": args.grader_timeout,
        "max_turns": args.max_turns,
        "HERMES_HOME": "ephemeral-per-run",
        "prompt_sha256": file_sha256(args.prompt_file),
        "command": hermes_command(args, provider, model, placeholder),
        "run_key": run_key,
    }


def add_common_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--starter", type=Path, required=True, help="starter repository/tree")
    parser.add_argument("--prompt-file", type=Path, required=True, help="identical task prompt for every model")
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--grader", type=Path, required=True, help="hidden external grader executable")
    parser.add_argument(
        "--grader-bundle-root",
        type=Path,
        help="optional immutable grader directory whose full tree digest is frozen",
    )
    parser.add_argument("--grader-arg", action="append", default=[], help="repeat; use --grader-arg=VALUE for dash-prefixed values")
    parser.add_argument("--reasoning", default="high")
    parser.add_argument("--toolsets", default="terminal,file")
    parser.add_argument("--timeout", type=float, default=1800.0)
    parser.add_argument("--grader-timeout", type=float, default=300.0)
    parser.add_argument("--max-turns", type=int, default=90)
    parser.add_argument("--attempt", type=int, default=1)
    parser.add_argument("--runs-root", type=Path, default=DEFAULT_RUNS_ROOT)
    parser.add_argument("--hermes", type=Path, default=DEFAULT_HERMES)
    parser.add_argument("--tool-sandbox-hook", type=Path, default=DEFAULT_TOOL_SANDBOX_HOOK)
    parser.add_argument("--sandbox-run", type=Path, default=DEFAULT_SANDBOX_RUN)
    parser.add_argument(
        "--no-tool-sandbox",
        dest="tool_sandbox",
        action="store_false",
        help="disable agent tool confinement (test fixtures only; never valid for campaign runs)",
    )
    parser.set_defaults(tool_sandbox=True)
    parser.add_argument(
        "--no-grader-sandbox",
        dest="grader_sandbox",
        action="store_false",
        help="disable grader confinement (test fixtures only; never valid for campaign runs)",
    )
    parser.set_defaults(grader_sandbox=True)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--run-key", help="stable, exclusive directory key; required to resume a single run")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="action", required=True)

    run = subparsers.add_parser("run", help="run one allowed provider/model pair")
    add_common_arguments(run)
    run.add_argument("--provider", required=True)
    run.add_argument("--model", required=True)

    matrix = subparsers.add_parser("matrix", help="run or plan the frozen six-route matrix")
    add_common_arguments(matrix)
    matrix.add_argument("--jobs", type=int, default=1, help="parallel workers")
    matrix.add_argument("--dry-run", action="store_true", help="print plan; do not create run directories or execute anything")
    matrix.add_argument("--batch-id", help="stable prefix for resumable matrix runs")

    return parser


def matrix_run_key(batch_id: str, args: argparse.Namespace, provider: str, model: str) -> str:
    return "__".join(
        [
            safe_component(batch_id),
            safe_component(args.task_id),
            f"a{args.attempt}",
            safe_component(provider),
            safe_component(model),
        ]
    )


def run_matrix(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    batch_id = args.batch_id or f"batch-{compact_utc_now()}-{uuid.uuid4().hex[:8]}"
    if args.resume and not args.batch_id:
        raise ValueError("--resume requires --batch-id for matrix runs")
    keys = [matrix_run_key(batch_id, args, provider, model) for provider, model in MODELS]
    if args.dry_run:
        return (
            {
                "schema_version": SCHEMA_VERSION,
                "batch_id": batch_id,
                "task_id": args.task_id,
                "attempt": args.attempt,
                "runs": [
                    planned_run(args, provider, model, key)
                    for (provider, model), key in zip(MODELS, keys, strict=True)
                ],
            },
            0,
        )

    results: list[dict[str, Any] | None] = [None] * len(MODELS)
    errors: list[dict[str, Any]] = []

    def worker(index: int) -> tuple[int, dict[str, Any]]:
        provider, model = MODELS[index]
        child = argparse.Namespace(**vars(args))
        child.run_key = keys[index]
        return index, run_one(child, provider, model)

    with concurrent.futures.ThreadPoolExecutor(max_workers=min(args.jobs, len(MODELS))) as executor:
        futures = {executor.submit(worker, index): index for index in range(len(MODELS))}
        for future in concurrent.futures.as_completed(futures):
            index = futures[future]
            provider, model = MODELS[index]
            try:
                result_index, result = future.result()
                results[result_index] = result
            except Exception as exc:  # one model failure must not erase sibling artifacts
                errors.append({"provider": provider, "model": model, "error": f"{type(exc).__name__}: {exc}"})

    summary = {
        "schema_version": SCHEMA_VERSION,
        "batch_id": batch_id,
        "task_id": args.task_id,
        "attempt": args.attempt,
        "runs": results,
        "errors": errors,
    }
    return summary, 2 if errors else 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        validate_common(args, executing=not getattr(args, "dry_run", False))
        if args.action == "run":
            summary = run_one(args, args.provider, args.model)
            exit_code = 0
        else:
            summary, exit_code = run_matrix(args)
        json.dump(summary, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
        return exit_code
    except (OSError, RuntimeError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
