# Repair the restart-safe migration runner

Implement `run_migrations(db_path, migrations_dir, fail_after=None)` in `solution.py` for a local JSON state store.

Migration files are regular, non-symlink files named exactly `NNN-name.json` where NNN is a positive zero-padded 3-digit version. Each JSON object has exactly `version` (matching the filename integer), `set` (object of string keys to JSON values), and `delete` (list of unique string keys). A key cannot appear in both. Versions must be unique and contiguous starting at 1. Reject malformed sets before mutating state.

State lives at `db_path` as `{"data": {...}, "applied": [{"version": N, "sha256": HEX}, ...]}`. Missing state means empty. Existing state must validate; applied versions must be a contiguous prefix and each digest must match the current canonical migration bytes (`sha256` of the file's raw bytes). Never reapply an applied migration.

After each migration, atomically replace the state file. `fail_after=N` raises `RuntimeError` after N newly committed migrations, leaving those commits durable; a retry resumes. Return the newly applied version list. Reject symlinks. Standard library only.

Run the visible tests with `python3 -B -m unittest discover -s tests -p 'test_*.py' -v`.
