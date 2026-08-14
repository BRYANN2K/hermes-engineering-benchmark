# Harden the local health-check runner

Repair `run_check(workspace, spec)` in `solution.py`. It executes trusted check scripts while treating the job specification as untrusted. This task is fully local and sandboxed.

`workspace` must be an existing regular directory, not a symlink. `spec` has exactly:

- `script`: a safe relative POSIX path strictly below `checks/`, ending `.py`;
- `args`: a list of at most 16 strings, each at most 256 characters (metacharacters are valid literal arguments);
- `env`: an object with at most 16 string-to-string entries. Keys must match `CHECK_[A-Z0-9_]+`; values are at most 512 characters and contain no NUL;
- `timeout_ms`: integer 50..5000 (booleans invalid).

The script and every existing ancestor below workspace must be regular/non-symlink. The script must resolve inside `workspace/checks`. Invalid input raises `ValueError` before executing anything.

Execute as `[sys.executable, "-I", script_path, *args]` with `shell=False`, working directory `workspace`, stdin disconnected, and a clean environment containing only `PATH` from the runner process (if present), `LANG=C`, `LC_ALL=C`, plus declared `CHECK_*` variables. Do not leak any other parent variable. Capture text as UTF-8 with replacement for invalid bytes. On timeout, kill the process and collect output.

Return exactly `{"returncode": INT_OR_NULL, "stdout": TEXT, "stderr": TEXT, "timed_out": BOOL}`. Limit each output field to 4096 characters; append `...[truncated]` after the first 4082 characters when needed. A timeout has `returncode: null` and `timed_out: true`. Never interpret argument or environment text as shell syntax. Standard library only; keep the fixture CLI.

Run the visible tests with `python3 -B -m unittest discover -s tests -p 'test_*.py' -v`.
