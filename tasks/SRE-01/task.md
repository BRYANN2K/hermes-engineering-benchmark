# Repair the hysteretic incident detector

Implement `detect_incidents(samples, threshold)` in `solution.py`.

`samples` is a list of objects with exactly `timestamp` (strictly increasing non-negative integer; booleans invalid) and `value` (a finite non-negative int/float, booleans invalid, or `null`). `threshold` is a finite non-negative number.

A non-null value strictly greater than the threshold is breaching; a value at or below it is healthy. Open an incident at the timestamp of the **third consecutive breaching sample**. While open, resolve it at the timestamp of the **second consecutive healthy sample**. A null sample resets both consecutive-run counters but does not open or resolve an incident. Samples consumed to open or resolve belong only to that transition; a new run begins afterward.

Return incidents in order as objects:

`{"opened_at": TS, "resolved_at": TS_OR_NULL, "peak": NUMBER}`

`peak` is the greatest non-null value observed from the first sample in the three-sample opening run through the resolving sample (or end of input if unresolved). Thus the opening prelude contributes to the peak. Preserve numeric values rather than rounding. Reject malformed input with `ValueError`, do not mutate it, and retain the JSON CLI. Standard library only.

Run the visible tests with `python3 -B -m unittest discover -s tests -p 'test_*.py' -v`.
