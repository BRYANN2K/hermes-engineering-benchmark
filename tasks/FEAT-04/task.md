# FEAT-04: Add a deterministic retry executor

Implement `run_with_retry(operation, policy, sleep, retryable=(Exception,))` in `retry.py`.

`policy` is a list of non-negative real delays (booleans invalid). Attempt once immediately, then at most once after each listed delay. On a caught `retryable` exception, call `sleep(delay)` immediately before the next attempt. Return the operation result on success. If the last attempt fails, re-raise that exact exception object with its traceback. Exceptions outside `retryable` propagate immediately and never sleep. If `sleep` raises, propagate it and do not call the operation again.

Validate all inputs before the first operation call: `operation` and `sleep` callable; `retryable` is a nonempty tuple containing only exception classes; `policy` is a list with valid delays. Raise `TypeError`/`ValueError` as appropriate. Copy policy behaviorally: mutation of the original list by `operation` or `sleep` must not alter the scheduled retries. `on_retry` is not part of the API; do not add required parameters.

## Environment

- Python 3.13 standard library only
- No network access or third-party packages

## Public tests

Run exactly:

```bash
python3 -B -m unittest discover -s tests -p 'test_*.py' -v
```

Make the smallest maintainable change that satisfies the contract.
