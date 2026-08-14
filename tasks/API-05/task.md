# API-05: Implement versioned profile PATCH semantics

Implement `ProfileService` in `profile_service.py`. `request(method, path, headers, body)` returns `(status, response_headers, response_body)`; all bodies are compact sorted JSON bytes with `Content-Type: application/json`.

Only `/profiles/{id}` is valid, with ID `[a-z][a-z0-9-]{0,31}`. Header names are case-insensitive.

`seed(id, profile)` is setup API: profile must have exactly `display_name` (nonempty string), `email` (lowercase canonical address matching `[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}`), and `notifications` (boolean). It creates version 1 and rejects an existing ID. It returns a deep-copied profile representation with `id` and `version`.

`GET` returns 404 or 200 plus ETag `"vN"`. `PATCH` requires existing profile, `Content-Type: application/merge-patch+json` with optional parameters, and `If-Match` exactly current ETag. Error precedence after route/existence/method is media type (415), malformed JSON (400), non-object (422), then missing precondition (428), then stale precondition (412), then patch validation (422). A patch may contain only the three editable fields. `null` is invalid (fields cannot be deleted); resulting fields obey seed validation. Empty patch succeeds, increments version, and returns 200. Failed requests never mutate or increment. Unknown methods return 405. Errors are `{"error": CODE}`. Successful profiles contain exactly `id`, the three fields, and `version`. Returned data must not alias internal state.

## Environment

- Python 3.13 standard library only
- No network access or third-party packages

## Public tests

Run exactly:

```bash
python3 -B -m unittest discover -s tests -p 'test_*.py' -v
```

Make the smallest maintainable change that satisfies the contract.
