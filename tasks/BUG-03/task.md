# BUG-03: Repair stable dependency-aware job planning

Repair `job_plan.py` while retaining `plan_jobs(jobs) -> list[str]`.

Each job is a dictionary with exactly `name`, optional `needs` (default `[]`), and optional `priority` (default `0`). Names are non-empty strings. `needs` is a list of unique non-empty strings. Priority is an integer but not a boolean. Reject malformed jobs, duplicate names, self-dependencies, and unknown dependencies with `ValueError`.

Return every job exactly once in topological order. Whenever multiple jobs are ready, choose the greatest priority first; ties use original declaration order. Newly-ready jobs participate in that same rule. Any cycle, including a disconnected cycle, raises `ValueError('dependency cycle')` rather than returning a partial plan. Do not mutate the input.

## Environment

- Python 3.13 standard library only
- No network access or third-party packages

## Public tests

Run exactly:

```bash
python3 -B -m unittest discover -s tests -p 'test_*.py' -v
```

Make the smallest maintainable change that satisfies the contract.
