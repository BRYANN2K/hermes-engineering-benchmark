# API-02: Add signed cursor pagination for events

Implement `list_events(records, query, secret)` in `event_page.py`, returning `(status, payload)`.

Every record must be a dictionary with exactly `id` (non-empty string), `created_at` (non-negative non-boolean integer), and arbitrary JSON-compatible `data`; IDs must be unique. Validate all records and `secret` (nonempty bytes) before query handling, raising `TypeError` or `ValueError` for server/programmer input errors.

`query` is a mapping whose only allowed keys are `limit` and `cursor`, each with a string value. `limit` defaults to 20 and must be canonical decimal text from 1 through 100 (no sign or leading zero). Unknown/duplicate-like non-string inputs produce `400 {"error":"invalid_query"}`. Results sort by `created_at` descending, then ID lexicographically ascending. Return `200 {"items": [...], "next_cursor": token_or_None}` with deep-copied records. The cursor resumes strictly after the last returned sort tuple. If there are no more records, it is null.

Tokens are base64url without padding of `payload_bytes + b'.' + lowercase_hex_hmac`, where payload is compact sorted UTF-8 JSON exactly `{"created_at": INT, "id": STRING}` and the HMAC is SHA-256 using `secret`. Invalid base64/UTF-8/JSON/schema/canonical encoding/signature or a cursor tuple absent from current records returns `400 {"error":"invalid_cursor"}` without items. Compare signatures safely. Do not mutate inputs.

## Environment

- Python 3.13 standard library only
- No network access or third-party packages

## Public tests

Run exactly:

```bash
python3 -B -m unittest discover -s tests -p 'test_*.py' -v
```

Make the smallest maintainable change that satisfies the contract.
