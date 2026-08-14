# Reconcile a multi-region object replica

Repair `reconcile(regions, tombstones)` in `solution.py`.

`regions` is a non-empty object mapping unique region-name strings to lists of object records. A record has exactly `key` (non-empty safe relative POSIX path), `version` (positive integer; booleans invalid), and `content` (string). A region cannot contain the same key twice. `tombstones` is a list of records with exactly `key` and positive integer `version`, with unique keys. Reject unsafe keys (absolute, backslash, empty/`.`/`..` component) and malformed input with `ValueError`.

For each key, the globally greatest version wins across object records and its tombstone. Equal-version rules:

- Object contents at the same greatest version must agree or the input is irreconcilably split-brain: raise `ValueError`.
- A tombstone wins over an object at equal version (prevents resurrection).

Return one action for every region that differs from the winner:

- Winner object: `{"action":"put","region":R,"key":K,"version":V,"content":C}` unless that exact object already exists there.
- Winner tombstone: `{"action":"delete","region":R,"key":K,"version":V}` unless the region has no object for the key (a stale/absent object already needs no action).

Sort actions by `(key, region, action)`. Validate the entire input before returning anything and do not mutate it. Standard library only. CLI reads regions JSON and tombstones JSON and prints compact JSON.

Run the visible tests with `python3 -B -m unittest discover -s tests -p 'test_*.py' -v`.
