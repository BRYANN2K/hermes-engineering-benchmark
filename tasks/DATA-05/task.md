# DATA-05 — Atomic inventory movement batches

Implement `apply_batch(db_path, batch_csv)` in `inventory.py`.

CSV header must be exactly `batch_id,movement_id,sku,delta`. A file has at least one data row; all rows share one trimmed nonempty batch_id. Movement id and sku are trimmed nonempty strings. Delta is a canonical nonzero base-10 integer (no `+`, leading zeroes, decimals, or whitespace after trimming).

Create and maintain:

- `inventory(sku TEXT PRIMARY KEY, quantity INTEGER NOT NULL CHECK(quantity >= 0))`
- `movements(movement_id TEXT PRIMARY KEY, batch_id TEXT NOT NULL, sku TEXT NOT NULL, delta INTEGER NOT NULL)`
- `batches(batch_id TEXT PRIMARY KEY, digest TEXT NOT NULL)`

Validate the entire file before changing the DB. Apply movements in CSV order in one transaction. Every intermediate quantity must remain nonnegative; absent skus start at zero. Duplicate movement ids inside a batch or ids already used by another batch are errors. On first success, record a SHA-256 digest of the normalized row sequence and return `{batch_id, applied: N, replayed: false, balances: {affected sku: final quantity}}` with sku keys sorted.

Reapplying byte/whitespace-equivalent normalized content for the same batch id is a replay: no writes, `applied:0`, `replayed:true`, current affected balances. Same batch id with different normalized content raises `ValueError`. Any error leaves all three tables unchanged. Do not close a connection you did not create (the API receives a path, so it creates/closes its own).

## Public test

```bash
python3 -m unittest discover -s tests -v
```

Run the visible tests with `python3 -B -m unittest discover -s tests -p 'test_*.py' -v`.
