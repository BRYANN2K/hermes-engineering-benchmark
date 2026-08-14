# API-01: Implement conditional document writes with ETags

Implement `DocumentAPI` in `document_api.py`. `request(method, path, headers, body)` returns `(status, response_headers, response_body)` where the body is UTF-8 JSON bytes and response header keys are canonical `Content-Type` and `ETag` where applicable.

The only route is `/documents/{id}` where ID matches `[A-Za-z0-9_-]{1,32}` without URL decoding. Header names are case-insensitive. `GET` ignores its body: missing resource is `404 {"error":"not_found"}`; existing is `200` with `{"id", "content", "version"}` and ETag equal to the quoted decimal version, e.g. `"1"`.

`PUT` accepts exactly a JSON object `{"content": string}` and Content-Type `application/json`, optionally followed by parameters. Invalid route is 404, unsupported route method 405, invalid media/JSON/schema is 415/400/422 respectively, and none mutate state. Creating requires `If-None-Match: *`; otherwise return 428, or 412 if any resource already exists. Successful creation is 201 version 1. Updating an existing resource requires `If-Match` exactly equal to its current ETag; missing gives 428 and stale/malformed gives 412. Successful update is 200 and increments version, even if content is unchanged. Error bodies are exactly `{"error": CODE}` with compact, sorted JSON and Content-Type `application/json`. Success bodies use the same encoding. Do not expose internal mutable state.

## Environment

- Python 3.13 standard library only
- No network access or third-party packages

## Public tests

Run exactly:

```bash
python3 -B -m unittest discover -s tests -p 'test_*.py' -v
```

Make the smallest maintainable change that satisfies the contract.
