# Results — 2026-08-14 (v4)

The first completed LLM Engineering Benchmark campaign: **40 executable tasks**, **10 engineering tracks**, **6 route conditions**, **240 primary runs** and **120 preregistered repeats**.

- **Campaign ID:** `campaign-20260814-v4`
- **Execution date:** 2026-08-14
- **Integrity:** 360/360 cells complete and verified
- **Counted source:** `19484e9a36f1626fa7aadc6b87e1467e1da53153`
- **Source tree SHA-256:** `ee3327ff74001ae79175c7b103ebcf88b61b2797d3d966aeacf4efac38d13d6f`

## Leaderboard

Primary attempt only:

| Rank | Route | Resolved | Rate | Repeat 3/3 |
|---:|---|---:|---:|---:|
| 1 | Daybreak Blue | 37/40 | 92.5% | 10/10 |
| 2 | Luna | 36/40 | 90.0% | 9/10 |
| 3 | Terra | 34/40 | 85.0% | 10/10 |
| 4 | Sol standard | 32/40 | 80.0% | 7/10 |
| 5 | DeepSeek V4 Flash | 28/40 | 70.0% | 6/10 |
| 6 | DeepSeek V4 Pro | 25/40 | 62.5% | 4/10 |

## Read the release

| Artifact | Purpose |
|---|---|
| [Final report](final-report.md) | Protocol, category breakdowns, route analysis, incidents, limits and conclusions |
| [Generated metrics report](report.md) | Canonical aggregate tables produced by the postprocessor |
| [Per-run results](runs.csv) | One row for each of the 360 verified runs |
| [Machine-readable summary](summary.json) | Aggregate metrics and telemetry coverage |
| [Release manifest](release.json) | Date, campaign identity, counted source and run inventory |
| [Report manifest](report-manifest.json) | Source and generated-output SHA-256 commitments |
| [SHA256SUMS](SHA256SUMS) | Checksums for every file in this dated release |

## Charts

- [Resolved rate](resolved-rate.svg)
- [API-equivalent cost](api-equivalent-cost.svg)
- [Median latency](median-latency.svg)
- [Repeat reliability](repeat-reliability.svg)
- [Resolved rate versus cost](resolved-vs-cost.svg)

## Important limits

- These rankings describe this fixed 40-task suite, not all software-engineering work.
- Daybreak Blue and Sol share the same declared underlying GPT-5.6 Sol model under different route conditions. The campaign does not establish different model weights.
- Twenty-seven runs had unavailable provider token telemetry. They remain in capability metrics and are excluded from cost means rather than treated as zero-cost runs.
- The visible `UI-05` task did not state its expected coupon-action return contract as clearly as it should have; that category result carries this caveat.
- Host-environment inheritance, the preflight `SIGTERM` behavior, the stale frozen proof plan and provider-side route differences are disclosed in the [full report](final-report.md) and [incident records](../../proof/campaign-20260814-v4/incidents/).

Raw model outputs, credentials, private archives and complete grader implementations are not included in this public release.
