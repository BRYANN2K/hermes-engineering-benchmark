# Verify signed webhook requests without replay leaks

Repair `verify_request(secret, headers, body, now, store_path, tolerance=300)` in `solution.py`.

This sandbox uses local HMAC, not a network service. Inputs:

- `secret`: non-empty bytes.
- `headers`: string-to-string dictionary. Header names are case-insensitive and must be unique case-insensitively. Required: `X-Webhook-Timestamp`, `X-Webhook-Nonce`, `X-Webhook-Signature`.
- Timestamp: canonical decimal non-negative integer text (`"0"` or no leading zeroes).
- Nonce: 16..64 ASCII alphanumeric, `_`, or `-`.
- Signature: exactly `v1=` plus 64 lowercase hex characters.
- `body`: bytes; `now`: non-negative integer; `tolerance`: non-negative integer (booleans invalid).

Expected signature is HMAC-SHA256 over `timestamp_ascii + b"." + nonce_ascii + b"." + body`, compared in constant time.

Return `True` only for a valid signature whose absolute timestamp skew is at most tolerance and whose nonce has not been accepted before. Persist accepted nonces in the JSON file `store_path` as `{"nonces":{"NONCE":TIMESTAMP,...}}`. Before replay checking, prune stored entries with `timestamp < now - tolerance`; entries exactly on the boundary remain. Validate stored schema; reject a symlink store path. Atomically replace the store after acceptance. Invalid, stale, malformed, replayed, or bad-signature requests return `False` and must not create or change the store. Concurrent processes must not both accept one nonce: coordinate with an exclusive sibling lock file created with `O_CREAT|O_EXCL`, bounded retries, and always clean it up. A stale lock older than 10 seconds may be removed.

Keep `sign(secret, timestamp, nonce, body)` working. Standard library only; no secret/signature/body data in diagnostics.

Run the visible tests with `python3 -B -m unittest discover -s tests -p 'test_*.py' -v`.
