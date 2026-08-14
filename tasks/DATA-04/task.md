# DATA-04 — Deterministic JSONL sessionization

Implement `sessionize(input_jsonl, output_jsonl, gap_minutes=30)` in `sessionize.py`.

Each nonblank input line must be a JSON object with exactly string fields `event_id,user_id,timestamp,path`; all must be nonempty. Timestamp format is exact UTC `YYYY-MM-DDTHH:MM:SSZ`. Event ids must be globally unique. Any malformed line, duplicate id, or non-positive integer gap raises `ValueError` and leaves an existing output file untouched.

Sort events by `user_id`, parsed timestamp, then `event_id`. Within each user, begin a new session only when the gap from the previous event is **strictly greater** than `gap_minutes`.

Write compact JSONL, sessions sorted by start timestamp then user_id. Each object has keys in this order:

`session_id,user_id,started_at,ended_at,duration_seconds,event_count,unique_paths`

`session_id` is `<user_id>:<started_at>:<ordinal>`, where ordinal starts at 1 per user in chronological order. `unique_paths` preserves first occurrence order within the session. Replace output atomically and return `{events, sessions}`.

## Public test

```bash
python3 -m unittest discover -s tests -v
```

Run the visible tests with `python3 -B -m unittest discover -s tests -p 'test_*.py' -v`.
