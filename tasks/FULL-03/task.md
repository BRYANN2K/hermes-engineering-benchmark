# FULL-03 — Idempotent support-ticket intake

Implement `app.py`, the SQLite-backed API used by the supplied support form. `make_server(db_path, port=0)` returns a standard-library server.

- Serve `index.html` at `/` and `app.js` at `/app.js`.
- `POST /api/tickets` requires JSON exactly `{requestId, email, subject, priority}`. Trim strings. `requestId` is 1–64 chars; email must contain exactly one `@` with nonempty sides; subject is 1–120 chars; priority is `low`, `normal`, or `urgent`.
- First requestId creates a durable ticket and returns 201: `{id,requestId,email,subject,priority,status:"open"}`.
- Replaying the same normalized payload returns that exact original ticket with 200. Reusing requestId for a different payload returns 409 `{error:"idempotency_conflict"}` without mutation.
- `GET /api/tickets?status=open|closed` returns `{tickets:[...]}` ordered by id. The status parameter is required and no other query parameters are accepted. `PATCH /api/tickets/<id>` accepts exactly `{status:"open"|"closed"}`, returning updated ticket or 404.
- Invalid JSON/schema is 400 and never writes. Unknown routes are JSON 404. Include Content-Length; survive restart.

CLI: `python3 app.py DATABASE [PORT]`. No dependencies.

## Public test

```bash
python3 -m unittest discover -s tests -v
```

Run the visible tests with `python3 -B -m unittest discover -s tests -p 'test_*.py' -v`.
