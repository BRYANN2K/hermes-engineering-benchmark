# FEAT-02: Implement a keyed sliding-window rate limiter

Implement `RateLimiter` in `rate_limiter.py`.

`RateLimiter(limit, window, clock)` requires a positive non-boolean integer limit, a positive non-boolean real window, and a callable clock. `allow(key)` returns `(allowed, retry_after)`.

For each key independently, an allowed call records the current timestamp. A call is allowed when fewer than `limit` recorded timestamps lie in the half-open interval `(now-window, now]`. Timestamps exactly `window` old are expired. A rejected call is not recorded and returns the non-negative number of seconds until the oldest active timestamp expires; allowed calls return `0.0`. Preserve fractional values. `clock` must return a real, non-boolean number and must never move backwards across calls (even across different keys); otherwise raise `RuntimeError` without changing state. `reset(key)` forgets only that key and returns whether it existed. `snapshot()` returns a new dictionary mapping keys to tuples of currently active timestamps, purging expired timestamps using one clock reading. Keys may be any hashable value; unhashable keys raise `TypeError` without state changes.

## Environment

- Python 3.13 standard library only
- No network access or third-party packages

## Public tests

Run exactly:

```bash
python3 -B -m unittest discover -s tests -p 'test_*.py' -v
```

Make the smallest maintainable change that satisfies the contract.
