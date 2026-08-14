# FEAT-03: Implement dependency batch partitioning

Implement `build_batches(tasks, max_batch)` in `batch_plan.py`.

`tasks` is a list of dictionaries with exactly `id`, optional `after` (default `[]`), and optional `group` (default `None`). IDs and non-None groups are non-empty strings; `after` is a list of unique non-empty strings. Reject malformed input, duplicate IDs, self/unknown dependencies, and non-positive or boolean `max_batch` with `ValueError`. Cycles raise `ValueError('dependency cycle')`.

Return a list of batches, each a list of task IDs. A task can be scheduled only after all its dependencies appear in earlier batches. At each batch, scan ready tasks in declaration order and greedily take up to `max_batch`, except two tasks with the same non-None group may not share a batch. If a ready task conflicts with a group already chosen, skip it and continue scanning later ready tasks. Every batch must be nonempty and include each task once. Empty tasks returns `[]`. Do not mutate input.

## Environment

- Python 3.13 standard library only
- No network access or third-party packages

## Public tests

Run exactly:

```bash
python3 -B -m unittest discover -s tests -p 'test_*.py' -v
```

Make the smallest maintainable change that satisfies the contract.
