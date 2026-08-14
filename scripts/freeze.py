#!/usr/bin/env python3
"""Freeze or verify the preregistered benchmark source tree."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INCLUDED = (
    "suite.json",
    "campaign-policy.json",
    "proof/grader-commitments.json",
    "tasks",
    "private_graders",
    "harness",
    "runtime",
    "scripts",
    "pricing",
    "model-roster.json",
)
EXCLUDED_NAMES = {"__pycache__", ".pytest_cache", ".DS_Store", "landlock-run"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo"}


def files() -> list[Path]:
    output: list[Path] = []
    for relative in INCLUDED:
        path = ROOT / relative
        if not path.exists():
            continue
        candidates = [path] if path.is_file() else path.rglob("*")
        for candidate in candidates:
            rel = candidate.relative_to(ROOT)
            if any(part in EXCLUDED_NAMES for part in rel.parts):
                continue
            if candidate.is_file() and candidate.suffix not in EXCLUDED_SUFFIXES:
                output.append(candidate)
    return sorted(set(output), key=lambda path: path.relative_to(ROOT).as_posix())


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build() -> dict:
    entries = [{"path": path.relative_to(ROOT).as_posix(), "sha256": sha256(path), "bytes": path.stat().st_size} for path in files()]
    canonical = json.dumps(entries, separators=(",", ":"), sort_keys=True).encode()
    return {
        "schema_version": "1.0",
        "hash_algorithm": "sha256",
        "file_count": len(entries),
        "source_tree_sha256": hashlib.sha256(canonical).hexdigest(),
        "files": entries,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("write", "verify"))
    parser.add_argument("--manifest", type=Path, default=ROOT / "freeze-manifest.json")
    args = parser.parse_args()
    current = build()
    if args.action == "write":
        args.manifest.write_text(json.dumps(current, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({"written": str(args.manifest), "file_count": current["file_count"], "source_tree_sha256": current["source_tree_sha256"]}, sort_keys=True))
        return 0
    expected = json.loads(args.manifest.read_text(encoding="utf-8"))
    ok = expected == current
    print(json.dumps({"verified": ok, "file_count": current["file_count"], "source_tree_sha256": current["source_tree_sha256"]}, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
