# Reconstruct outage intervals from noisy probe events

Implement `reconstruct_outages(events, quorum, stale_after)`.

Each event has exactly `timestamp` (non-negative integer), `probe` (non-empty string), and `status` (`up` or `down`). Events must be in nondecreasing timestamp order. A probe may report at most once per timestamp. `quorum` and `stale_after` are positive integers (booleans invalid).

Process distinct timestamps as batches. At timestamp `t`, first expire a probe's prior state when `t - last_timestamp > stale_after`, then apply all reports at `t`, then evaluate service state. The service is:

- `down` when at least `quorum` currently fresh probes report down;
- `up` when at least `quorum` currently fresh probes report up;
- otherwise `unknown`.

Open an outage only when the last known (non-unknown) state is `up` and a batch evaluates `down`, at that batch timestamp. An initial `unknown -> down` does not open one. An intervening `unknown` does not erase the last known state. Once open, keep it open through `down` and `unknown`; resolve on the first later `up` batch. Return `{"started_at":..., "ended_at":...}` intervals, with `ended_at: null` if still open. Expiration and reports at one timestamp are one batch evaluation, so they cannot create an intermediate transition.

Reject malformed input with `ValueError`, do not mutate it, and keep the CLI. Standard library only.

Run the visible tests with `python3 -B -m unittest discover -s tests -p 'test_*.py' -v`.
