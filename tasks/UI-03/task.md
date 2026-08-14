# UI-03 — Deterministic customer table model

Implement `buildTableModel(rows, options)` in `starter/table.mjs` for a paginated customer table.

Options are `{ query = "", sortKey = "name", direction = "asc", page = 1, pageSize = 10 }`. Do not mutate `rows`.

- Filter by a trimmed, case-insensitive substring in `name` or `email`.
- Valid sort keys are `name`, `email`, `plan`, and `lastSeen`. Unknown keys fall back to `name`; direction is `desc` only when exactly `"desc"`.
- Compare strings case-insensitively. `null`/`undefined`/empty values always sort after populated values in both directions. Equal values retain input order.
- `pageSize` must be a positive integer (otherwise 10). Clamp page to the available range; an empty result uses page 1 and totalPages 1.
- Return `{ rows, total, page, pageSize, totalPages, summary, empty }`. `summary` is `"Showing X–Y of N"`, or `"Showing 0 of 0"`. `empty` is `null`, `"no-data"` when the input is empty, or `"no-matches"` when filtering removed all rows.

## Public test

```bash
node --test tests/table.test.mjs
```
