# Safely install an untrusted file bundle

Repair `install_bundle(root, entries)` in `solution.py`. This is a sandboxed archive-extraction simulation; it never reads a real archive.

`entries` is a non-empty list. Each entry is exactly one of:

- `{"path": P, "type": "file", "content": STRING}`
- `{"path": P, "type": "dir"}`

Paths are relative POSIX paths. Reject absolute paths, backslashes, empty/`.`/`..` components, duplicate normalized paths, and file/path-prefix collisions (a file `a` cannot coexist with `a/b`). Directory ancestors may be implicit. Reject malformed input with `ValueError` before mutating `root`.

Installation rules:

- Refuse to follow or replace a symlink at `root` or anywhere under it. Existing regular directories are allowed.
- Every target path must be absent; installation never overwrites existing files or directories (except an explicitly listed directory may match an existing regular directory).
- Install all entries or none. Stage in the parent of `root`, then atomically rename when `root` is absent. If `root` exists, preflight all conflicts and create entries; on any failure, remove only entries created by this call and preserve pre-existing state.
- Write file content as UTF-8. Return a lexicographically sorted list of installed POSIX paths, including explicit directory entries.
- `fail_after=N` is a deterministic test hook. After N entries have been created, raise `RuntimeError`; rollback must still hold. N must be a non-negative integer.

Security boundary: no path outside `root` may be read or written. Standard library only; retain the CLI.

Run the visible tests with `python3 -B -m unittest discover -s tests -p 'test_*.py' -v`.
