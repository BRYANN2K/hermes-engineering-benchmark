#!/usr/bin/env python3
"""Create or verify SHA-256 commitments for private grader trees."""
import argparse
import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def digest_tree(root: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    count = 0
    for path in sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix()):
        encoded = path.relative_to(root).as_posix().encode("utf-8", "surrogateescape")
        if path.is_symlink():
            digest.update(b"L\0" + encoded + b"\0" + os.fsencode(os.readlink(path)) + b"\0")
        elif path.is_dir():
            digest.update(b"D\0" + encoded + b"\0")
        elif path.is_file():
            digest.update(b"F\0" + encoded + b"\0")
            digest.update(path.read_bytes())
            digest.update(b"\0")
            count += 1
    return digest.hexdigest(), count


def current() -> dict:
    suite = json.loads((ROOT / "suite.json").read_text(encoding="utf-8"))
    commitments = []
    for task in suite["tasks"]:
        task_id = task["id"]
        sha256, files = digest_tree(ROOT / "private_graders" / task_id)
        commitments.append({"task_id": task_id, "sha256": sha256, "files": files})
    return {
        "schema_version": "1.0",
        "algorithm": "runner tree_sha256: typed D/F/L entries with sorted relative paths and file bytes",
        "task_count": len(commitments),
        "commitments": commitments,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("create", "verify"))
    parser.add_argument("--output", type=Path, default=ROOT / "proof" / "grader-commitments.json")
    args = parser.parse_args()
    observed = current()
    if args.action == "create":
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(observed, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({"created": True, "task_count": observed["task_count"]}, sort_keys=True))
        return 0
    expected = json.loads(args.output.read_text(encoding="utf-8"))
    passed = expected == observed
    print(json.dumps({"passed": passed, "task_count": observed["task_count"]}, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
