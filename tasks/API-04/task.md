# API-04: Implement webhook HMAC verification and replay defense

Implement `WebhookReceiver(secret, tolerance, clock)` in `webhook.py`. `handle(headers, body)` returns `(status, payload_dict)`.

Constructor requires nonempty bytes `secret`, a non-negative non-boolean real tolerance in seconds, and callable clock. Header names are case-insensitive and exactly one logical `X-Webhook-Timestamp` and `X-Webhook-Signature` must be present; conflicting case variants make the request invalid. Body must be bytes-like.

Timestamp is canonical unsigned decimal integer text (zero allowed, no leading zeros except `0`). Signature is exactly lowercase `v1=` followed by 64 lowercase hex characters. Expected signature is `HMAC-SHA256(secret, timestamp_ascii + b'.' + body)`. Use constant-time comparison. Read clock exactly once per structurally valid request; it must return a real non-boolean. Accept when absolute skew is at most tolerance. Invalid structure/signature returns `401 {"error":"unauthorized"}`; stale/future skew returns `408 {"error":"timestamp_out_of_range"}`.

For an authenticated, timely request, UTF-8 decode and parse JSON. It must be an object with exactly nonempty string `id`, nonempty string `type`, and arbitrary JSON-compatible `data`; otherwise return `400 {"error":"invalid_event"}`. Successfully accepted IDs are remembered. A replay of an accepted ID returns `409 {"error":"replayed_event"}`. Failed authentication, skew, or invalid event must not reserve an ID. Success returns `202 {"accepted": ID}`. `accepted_ids()` returns an immutable tuple in acceptance order.

## Environment

- Python 3.13 standard library only
- No network access or third-party packages

## Public tests

Run exactly:

```bash
python3 -B -m unittest discover -s tests -p 'test_*.py' -v
```

Make the smallest maintainable change that satisfies the contract.
