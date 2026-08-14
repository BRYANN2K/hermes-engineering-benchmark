# DATA-02 — Atomic SQLite invoice migration

Implement `migrate(connection)` in `migration.py`. The legacy database has `PRAGMA user_version=1`, table `customers(id INTEGER PRIMARY KEY, email TEXT NOT NULL)`, and:

```sql
invoices(id INTEGER PRIMARY KEY, customer_id INTEGER, total_dollars TEXT, paid INTEGER)
```

Migrate atomically to version 2:

- Preserve invoice ids and rows in a rebuilt `invoices` table.
- `customer_id INTEGER NOT NULL REFERENCES customers(id) ON DELETE RESTRICT`.
- Replace `total_dollars` with `total_cents INTEGER NOT NULL CHECK(total_cents >= 0)`. Accept only canonical non-negative decimal strings with zero, one, or two fractional digits (`0`, `12`, `12.3`, `12.34`); convert exactly, without float arithmetic.
- `paid INTEGER NOT NULL CHECK(paid IN (0,1))`; legacy NULL becomes 0, but any other value outside 0/1 is invalid.
- Create index `idx_invoices_customer_id` on `customer_id` and set user_version 2.

Foreign-key violations or invalid money/paid values raise `ValueError` and leave schema, rows, and user_version unchanged. Calling migrate at version 2 is a no-op. Any other starting version raises `ValueError` without changes. The caller owns the connection; do not close it.

## Public test

```bash
python3 -m unittest discover -s tests -v
```

Run the visible tests with `python3 -B -m unittest discover -s tests -p 'test_*.py' -v`.
