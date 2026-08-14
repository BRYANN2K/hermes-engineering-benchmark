# FULL-02 — Durable poll voting service

Implement the SQLite API in `app.py` that powers the supplied live poll page. `make_server(db_path, port=0)` initializes one poll with choices `alpha`, `beta`, `gamma` and returns a standard-library HTTP server.

- `GET /` and `GET /app.js` serve the supplied UI files.
- `GET /api/poll` returns `{choices:[{id,label,votes}], totalVotes}` in alpha/beta/gamma order. Labels are `Alpha`, `Beta`, `Gamma`.
- `POST /api/vote` requires header `X-Voter-ID`: a trimmed 1–64 character string and JSON exactly `{choiceId}` where choiceId is one of the choices. Bad input is 400.
- A voter has one durable vote. First vote returns 201. Repeating the same choice returns 200 without increasing totals. Changing choice returns 200 and atomically moves the vote.
- Every successful `POST /api/vote` response body is the current poll plus `selectedChoiceId` for that voter.
- Concurrent requests and server restarts must preserve exactly one vote per voter. Unknown routes return JSON 404. Correctly frame all responses.

CLI: `python3 app.py DATABASE [PORT]`. No dependencies.

## Public test

```bash
python3 -m unittest discover -s tests -v
```

Run the visible tests with `python3 -B -m unittest discover -s tests -p 'test_*.py' -v`.
