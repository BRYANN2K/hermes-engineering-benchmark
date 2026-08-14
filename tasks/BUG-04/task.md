# BUG-04: Fix streaming UTF-8 NDJSON decoding

Repair `ndjson_stream.py` and keep class `NDJSONDecoder(max_line_bytes=65536)` with `feed(chunk)` and `finish()`.

`chunk` must be bytes-like. Bytes may split anywhere, including inside a UTF-8 code point. A line ends at LF; an immediately preceding CR is excluded. Blank/ASCII-whitespace-only lines are ignored. Each nonblank line must be UTF-8 JSON whose top-level value is an object. `feed` returns all complete objects produced by that chunk. `finish` parses a final unterminated line, then becomes idempotent and returns `[]` on later calls. Feeding after finish raises `RuntimeError`.

`max_line_bytes` is a positive, non-boolean integer and limits raw bytes excluding LF and the optional CR. Exceeding it raises `ValueError`. Invalid UTF-8, invalid JSON, or a non-object raises `ValueError` containing the one-based physical line number as `line N`. Once any decoding error occurs, later calls raise `RuntimeError`.

## Environment

- Python 3.13 standard library only
- No network access or third-party packages

## Public tests

Run exactly:

```bash
python3 -B -m unittest discover -s tests -p 'test_*.py' -v
```

Make the smallest maintainable change that satisfies the contract.
