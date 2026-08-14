# Compute a rolling multi-window error-budget burn alert

Implement `burn_alert(samples, slo, short_window, long_window, short_burn, long_burn)`.

Each sample has exactly `timestamp`, `good`, and `total`: strictly increasing non-negative integer timestamps; non-negative integer counters with `good <= total` (booleans invalid). Samples are interval buckets at their timestamp, not cumulative counters. All window arguments are positive integers; thresholds are finite non-negative numbers. `slo` is finite and strictly between 0 and 1.

For every sample timestamp `t`, a window of width `W` includes samples whose timestamp is in `(t-W, t]`. Aggregate errors as `sum(total-good) / sum(total)`. When total is zero, its error rate and burn are 0. Burn is `error_rate / (1-slo)`.

Return the earliest timestamp where both short-window burn is **greater than or equal to** `short_burn` and long-window burn is **greater than or equal to** `long_burn`, as:

`{"alert_at": t, "short_burn": number, "long_burn": number}`

Return `null` if no alert. Do not round. Reject malformed input with `ValueError` and do not mutate it. The implementation should handle 10,000 samples comfortably; use a rolling-window approach rather than rescanning the full history at every point. Standard library only; keep the CLI.

Run the visible tests with `python3 -B -m unittest discover -s tests -p 'test_*.py' -v`.
