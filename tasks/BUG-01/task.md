# BUG-01: Repair TTL cache expiry and LRU accounting

Repair `ttl_cache.py` without changing the public `TTLCache` API.

- `TTLCache(capacity, clock)` requires a positive, non-boolean integer capacity. `clock` is a zero-argument callable returning a numeric monotonic timestamp.
- `set(key, value, ttl)` requires a non-negative real `ttl` (booleans are invalid). The deadline is `clock() + ttl`. A deadline equal to the current clock is expired, so `ttl=0` is never observable and consumes no capacity.
- `get(key, default=None)` returns `default` for missing or expired keys. Reading a live key makes it most recently used.
- `len(cache)` and `cache.keys()` purge expired entries first. `keys()` returns live keys from least to most recently used.
- Before inserting, purge all expired entries. If a live insertion exceeds capacity, evict the least recently used live key. Updating a key replaces its TTL/value and makes it most recent.
- Invalid constructor or TTL arguments raise `TypeError`/`ValueError` and do not mutate existing state.

## Environment

- Python 3.13 standard library only
- No network access or third-party packages

## Public tests

Run exactly:

```bash
python3 -B -m unittest discover -s tests -p 'test_*.py' -v
```

Make the smallest maintainable change that satisfies the contract.
