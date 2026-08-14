# Select the minimal safe CI job set

Repair `select_jobs(config, changed_paths)` in `solution.py`.

`config` has exactly a `jobs` list. Each job has exactly: unique non-empty `name`; non-empty `paths` list of POSIX glob strings; `needs` list of job names; and boolean `always`. Changed paths must be safe repository-relative POSIX paths (no absolute paths, backslashes, empty/`.`/`..` components).

A job is initially selected if `always` is true or any changed path matches any of its globs using `pathlib.PurePath.match` semantics. Then include every transitive prerequisite in `needs`. Return a deterministic topological order: prerequisites first and lexicographically smallest ready job first. Reject malformed config, unknown prerequisites, duplicate dependencies, self-dependencies, cycles, invalid paths, and non-string changed paths with `ValueError`. An empty changed-path list is valid. Do not mutate inputs.

The CLI accepts config JSON then a changed-path JSON list and prints one compact JSON array. Standard library only.

Run the visible tests with `python3 -B -m unittest discover -s tests -p 'test_*.py' -v`.
