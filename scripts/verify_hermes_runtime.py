#!/usr/bin/env python3
"""Create or verify the external Hermes runtime used by benchmark runs."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_HERMES_ROOT = Path("/opt/hermes")
DEFAULT_OUTPUT = ROOT / "runtime" / "hermes-runtime-manifest.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def scoped_files(hermes_root: Path) -> list[Path]:
    candidates = [
        hermes_root / "bin" / "hermes",
        hermes_root / ".venv" / "bin" / "hermes",
        hermes_root / "pyproject.toml",
        hermes_root / "uv.lock",
    ]
    candidates.extend(path for path in hermes_root.glob("*.py") if path.is_file())
    for directory in ("agent", "hermes_cli", "tools"):
        candidates.extend(
            path
            for path in (hermes_root / directory).rglob("*.py")
            if "__pycache__" not in path.parts
        )
    missing = [path for path in candidates if not path.is_file()]
    if missing:
        raise RuntimeError(f"Hermes runtime scope is incomplete: {missing[0]}")
    return sorted(set(candidates), key=lambda path: path.relative_to(hermes_root).as_posix())


def python_runtime(hermes_root: Path) -> dict:
    python = hermes_root / ".venv" / "bin" / "python"
    code = """
import importlib.metadata as metadata
import json
import platform
import hashlib
import sys
rows = []
for dist in metadata.distributions():
    file_rows = []
    for relative in sorted(dist.files or (), key=lambda item: str(item)):
        path = dist.locate_file(relative)
        if not path.is_file() or path.name.endswith(('.pyc', '.pyo')) or '__pycache__' in path.parts:
            continue
        digest = hashlib.sha256()
        try:
            with path.open('rb') as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                    digest.update(chunk)
        except OSError:
            continue
        file_rows.append([str(relative), digest.hexdigest(), path.stat().st_size])
    canonical = json.dumps(file_rows, sort_keys=True, separators=(',', ':')).encode()
    rows.append([
        str(dist.metadata.get('Name') or ''),
        str(dist.version),
        len(file_rows),
        hashlib.sha256(canonical).hexdigest(),
    ])
rows.sort()
print(json.dumps({
    'implementation': platform.python_implementation(),
    'version': platform.python_version(),
    'cache_tag': sys.implementation.cache_tag,
    'distributions': rows,
}, sort_keys=True, separators=(',', ':')))
"""
    completed = subprocess.run(
        [str(python), "-c", code],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        timeout=60,
    )
    if completed.returncode != 0:
        raise RuntimeError(f"Hermes Python inventory failed: {completed.stderr.strip()}")
    value = json.loads(completed.stdout)
    resolved = python.resolve(strict=True)
    value["executable_sha256"] = sha256(resolved)
    return value


def build(hermes_root: Path) -> dict:
    hermes_root = hermes_root.resolve(strict=True)
    entries = [
        {
            "path": path.relative_to(hermes_root).as_posix(),
            "sha256": sha256(path),
            "bytes": path.stat().st_size,
        }
        for path in scoped_files(hermes_root)
    ]
    python = python_runtime(hermes_root)
    canonical = json.dumps(
        {"files": entries, "python": python},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return {
        "schema_version": "1.0",
        "hash_algorithm": "sha256",
        "hermes_root": str(hermes_root),
        "scope": "launcher + root Python + agent/ + hermes_cli/ + tools/ + lockfiles + Python interpreter + installed distribution file hashes",
        "excluded_by_safe_mode": "skills, plugins, MCP, UI, gateway state, user config, memory, sessions and credentials",
        "file_count": len(entries),
        "runtime_sha256": hashlib.sha256(canonical).hexdigest(),
        "python": python,
        "files": entries,
    }


def verify(manifest: Path, hermes_root: Path) -> tuple[bool, dict]:
    expected = json.loads(manifest.read_text(encoding="utf-8"))
    observed = build(hermes_root)
    return expected == observed, observed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("write", "verify"))
    parser.add_argument("--hermes-root", type=Path, default=DEFAULT_HERMES_ROOT)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    observed = build(args.hermes_root)
    if args.action == "write":
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        args.manifest.write_text(json.dumps(observed, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({"written": str(args.manifest), "file_count": observed["file_count"], "runtime_sha256": observed["runtime_sha256"]}, sort_keys=True))
        return 0
    expected = json.loads(args.manifest.read_text(encoding="utf-8"))
    passed = expected == observed
    print(json.dumps({"verified": passed, "file_count": observed["file_count"], "runtime_sha256": observed["runtime_sha256"]}, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
