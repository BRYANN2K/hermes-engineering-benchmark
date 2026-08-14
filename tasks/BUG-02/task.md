# BUG-02: Fix immutable deep configuration merge

Repair `config_merge.py` and preserve `merge_config(base, overlay)`.

Both top-level arguments must be dictionaries or `TypeError` is raised. The result must share no mutable dictionaries, lists, sets, or tuples-with-mutable-members with either input. Neither input may be mutated.

For each overlay key: recursively merge only when both existing values are dictionaries; otherwise a deep copy of the overlay value replaces the base value. The exact string `"__DELETE__"` deletes that key when used as a dictionary value (a missing key stays missing). Delete markers work at every dictionary depth but have no special meaning inside lists. Keys absent from the overlay are deep-copied from the base. Key iteration order follows normal Python dictionaries: retained base keys keep position and new overlay keys append in overlay order.

## Environment

- Python 3.13 standard library only
- No network access or third-party packages

## Public tests

Run exactly:

```bash
python3 -B -m unittest discover -s tests -p 'test_*.py' -v
```

Make the smallest maintainable change that satisfies the contract.
