# Repair the deterministic deployment planner

`solution.py` plans a deployment from a JSON manifest, but it currently ignores service dependencies. Implement a safe deterministic planner.

## Contract

`build_plan(manifest)` accepts a dictionary with exactly one `services` list. Every service must be an object with exactly `name` (a non-empty string) and `depends_on` (a list of service-name strings).

- Names must be unique; every dependency must exist; self-dependencies and dependency cycles are invalid.
- Return every service name exactly once, after all of its dependencies.
- When several services are ready, choose the lexicographically smallest name. This makes the complete plan deterministic.
- Raise `ValueError` for every invalid manifest. Do not mutate the input.
- Keep the CLI: `python3 solution.py manifest.json` prints the plan as one JSON array and exits nonzero for invalid input.

Use only Python 3.13 standard library. Do not weaken tests.

Run the visible tests with `python3 -B -m unittest discover -s tests -p 'test_*.py' -v`.
