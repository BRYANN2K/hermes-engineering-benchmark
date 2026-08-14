# DATA-01 — Idempotent CSV ledger ingestion

Implement `ingest(input_csv, db_path, rejects_csv)` in `pipeline.py`.

Input must have the exact header `event_id,account_id,occurred_at,amount_cents`. For each data row:

- event/account ids are trimmed non-empty strings;
- `occurred_at` must be a real UTC timestamp formatted exactly `YYYY-MM-DDTHH:MM:SSZ`;
- amount must be a base-10 integer from -1,000,000 through 1,000,000 (JSON-style forms, decimals, and blanks are invalid).

Create SQLite table `ledger_events(event_id TEXT PRIMARY KEY, account_id TEXT NOT NULL, occurred_at TEXT NOT NULL, amount_cents INTEGER NOT NULL)`. Valid rows whose event id is already in the database are idempotent duplicates and do not overwrite the first event. Invalid rows go to `rejects_csv` with exact header `line,error`, in input order. Line is the 1-based physical CSV line; errors are one of `column_count`, `event_id`, `account_id`, `occurred_at`, `amount_cents`. Validate fields in that priority order after column count.

DB writes must be transactional (no partial event inserts), and the reject file must be replaced atomically rather than written in place. Input/header validation errors leave both destinations untouched. Return `{read, inserted, duplicates, rejected}`. Exact-header failure raises `ValueError` before creating or changing the DB/rejects.

No dependencies.

## Public test

```bash
python3 -m unittest discover -s tests -v
```

Run the visible tests with `python3 -B -m unittest discover -s tests -p 'test_*.py' -v`.
