# API-03: Implement atomic inventory reservations

Implement `InventoryStore` in `inventory.py` using SQLite. `InventoryStore(path, clock)` initializes the schema; separate instances may share a database. `close()` is idempotent.

- `add_stock(sku, quantity)`: SKU is a nonempty string; quantity is a positive non-boolean integer. Atomically add stock and return the new integer stock.
- `reserve(sku, quantity, key)`: quantity validation is identical and key is a nonempty string. Return `(created, reservation)` where reservation is a new dictionary `{"key", "sku", "quantity", "created_at"}`. First use of key atomically subtracts stock and records `created_at=clock()`. Same key/SKU/quantity replays the original with `created=False`, without clock use or stock change. Same key with different SKU/quantity raises `ReservationConflict`. Insufficient or unknown stock raises `InsufficientStock` and records nothing. The check, decrement, and insert must be one `BEGIN IMMEDIATE` transaction so separate instances cannot oversell.
- `stock(sku)` returns current stock or 0. `reservations()` returns new dictionaries ordered by creation row order.

The clock must return a real, non-boolean number. Validate arguments before starting mutations. Use parameterized SQL, a finite busy timeout, explicit commit/rollback, and no module-global or process-only lock. Reopening preserves data.

## Environment

- Python 3.13 standard library only
- No network access or third-party packages

## Public tests

Run exactly:

```bash
python3 -B -m unittest discover -s tests -p 'test_*.py' -v
```

Make the smallest maintainable change that satisfies the contract.
