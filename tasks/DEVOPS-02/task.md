# Make release publication atomic and retry-safe

Repair `publish_release(root, version, files, fail_after=None)` in `solution.py`. It simulates a local deployment release store.

- `version` is a non-empty string containing only ASCII letters, digits, `.`, `_`, or `-`, and may not be `.` or `..`.
- `files` is a non-empty dictionary mapping safe relative POSIX paths to string contents. Reject absolute paths, empty/dot components, `..`, backslashes, and path-prefix collisions (`a` and `a/b`).
- A successful call creates `root/releases/<version>/` with exactly those UTF-8 files and atomically writes `root/current` containing `version` plus a newline.
- Never follow an existing symlink anywhere below `root/releases`.
- Retrying an existing byte-identical version succeeds and activates it. Reusing a version with different content raises `ValueError` without changing it or `current`.
- `fail_after=N` is a deterministic test hook: after N files have been staged, raise `RuntimeError`. A failed call leaves no release, does not change `current`, and removes staging artifacts.
- Return the final release path. Raise `ValueError` for invalid input before mutating `root`.

Standard library only. Keep the API and CLI documented in the starter README.

Run the visible tests with `python3 -B -m unittest discover -s tests -p 'test_*.py' -v`.
