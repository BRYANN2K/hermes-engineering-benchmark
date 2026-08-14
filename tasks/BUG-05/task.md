# BUG-05: Correct per-label backup retention selection

Repair `retention.py` and keep `select_deletions(names, keep, now, max_age_days)`.

Valid backup names are exactly `backup-YYYYMMDDTHHMMSSZ-LABEL.tar.gz`, where `LABEL` is one or more lowercase ASCII letters, digits, or hyphens. Invalid names and impossible dates are ignored, never returned. `now` must be a timezone-aware `datetime`; compare in UTC. `keep` is a non-negative non-boolean integer. `max_age_days` is a non-negative real number but not a boolean.

For each label independently, protect its `keep` newest backups. Newest ordering is timestamp descending, then filename lexicographically ascending for equal timestamps. Of the remaining valid backups, select those strictly older than `now - timedelta(days=max_age_days)`. A backup exactly on the cutoff, or dated in the future, is not deleted. Return selected filenames in lexicographic order. Duplicate input names appear at most once. Invalid arguments raise before any result is produced and input is not mutated.

## Environment

- Python 3.13 standard library only
- No network access or third-party packages

## Public tests

Run exactly:

```bash
python3 -B -m unittest discover -s tests -p 'test_*.py' -v
```

Make the smallest maintainable change that satisfies the contract.
