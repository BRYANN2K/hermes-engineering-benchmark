# FULL-01 — Optimistic task board API

Finish `app.py`, the standard-library HTTP/SQLite backend used by the supplied task-board page.

`make_server(db_path, port=0)` must return an `HTTPServer`-compatible server and initialize durable storage. JSON responses use `application/json`.

- `GET /` serves `index.html`; `GET /app.js` serves the client module.
- `GET /api/tasks` returns `{ "tasks": [...] }`, ordered by integer id.
- `POST /api/tasks` accepts exactly `{ "title": string }`. Trim title; require 1–80 characters. Return the created `{id,title,completed:false,version:1}` with 201. Bad JSON/schema returns 400 and creates nothing.
- `PATCH /api/tasks/<id>` accepts exactly `{ "completed": boolean, "version": integer }` (booleans are not integer versions). If the id is missing return 404. If version is stale return 409 with `{ "error":"version_conflict", "task": currentTask }` and do not mutate. Otherwise update completion, increment version, and return the task.
- Other routes return 404 JSON. Include a correct `Content-Length`. Data must survive server restart.

Keep the public function and CLI (`python3 app.py DATABASE [PORT]`) working. No dependencies or network access.

## Public test

```bash
python3 -m unittest discover -s tests -v
```

Run the visible tests with `python3 -B -m unittest discover -s tests -p 'test_*.py' -v`.
