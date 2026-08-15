# Severity-weighted quality scores

Campaign: `campaign-20260814-v4`
Analysis date: 2026-08-15
Status: supplemental, post-hoc, non-canonical

This supplemental analysis adds a severity-weighted view of residual solution quality to the frozen benchmark results. It does **not** replace the sealed attempt-1 resolved-rate leaderboard in [`results/2026-08-14-v4`](results/2026-08-14-v4/README.md), and it is not part of the original campaign manifest.

The canonical campaign answers a binary question: did the primary attempt satisfy the complete deterministic grader? These quality scores ask a different question: after reading the public task contract and the publicly documented failure, how much of the required behavior remained correct?

## Overall ranking

The overall score is the equal-weight mean of the ten category scores.

| Rank | Route condition | Quality score | Canonical resolved rate |
|---:|---|---:|---:|
| 1 | Luna | 98.3% | 90.0% |
| 2 | Terra | 97.6% | 85.0% |
| 3 | Daybreak Blue | 96.4% | 92.5% |
| 4 | Sol standard | 92.6% | 80.0% |
| 5 | DeepSeek V4 Flash | 89.6% | 70.0% |
| 6 | DeepSeek V4 Pro | 82.8% | 62.5% |

These columns are different metrics and must not be subtracted or treated as interchangeable confidence estimates.

## Category scores

| Category | Daybreak Blue | Luna | Terra | Sol standard | DeepSeek V4 Flash | DeepSeek V4 Pro |
|---|---:|---:|---:|---:|---:|---:|
| DevOps | 90.0 | 90.0 | 90.0 | 90.0 | 90.0 | 78.8 |
| Cloud | 100.0 | 100.0 | 100.0 | 100.0 | 80.0 | 100.0 |
| Front end | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 |
| Back end | 100.0 | 93.0 | 97.0 | 93.4 | 90.0 | 93.4 |
| Full stack | 100.0 | 100.0 | 100.0 | 100.0 | 85.0 | 15.0 |
| Bug fixing | 100.0 | 100.0 | 96.4 | 96.4 | 81.0 | 98.4 |
| Feature implementation | 100.0 | 100.0 | 98.5 | 100.0 | 87.0 | 95.5 |
| Data / SQL | 94.0 | 100.0 | 94.0 | 83.0 | 83.0 | 84.0 |
| SRE | 100.0 | 100.0 | 100.0 | 100.0 | 100.0 | 63.3 |
| Security | 80.0 | 100.0 | 100.0 | 63.3 | 100.0 | 100.0 |

## Method

1. A primary attempt that resolved the task receives 100.
2. An unresolved task receives a residual-quality score from 0 to 99 based on the public contract behavior that remained correct and the severity of the publicly documented gap.
3. Residual scores are interpretive. They were not emitted by the sealed grader, and their evidence confidence is recorded as `high`, `medium`, or `limited` in [`quality-scores.json`](quality-scores.json).
4. `UI-05` is excluded for every route because its failing coupon-action return contract was not explicit in the visible task statement. The Front end score is therefore the mean of four rated tasks.
5. Each category is the arithmetic mean of its rated task scores.
6. The overall score gives each of the ten categories equal weight. It is not a task-weighted mean.
7. Repeat reliability remains a separate stability metric and is not blended into the quality score.

## Interpretation limits

- The analysis is bounded to the same frozen tasks, route conditions, public contracts, and published failure analysis as the v4 campaign.
- Private grader assertions, raw model outputs, and hidden implementation details were not used or reconstructed.
- When the public report names multiple possible failure causes, the residual score is deliberately conservative and its confidence is reduced.
- Daybreak Blue and Sol standard remain separate route conditions sharing the same declared GPT-5.6 Sol underlying model. These scores do not establish different model weights.
- Capability, cost, latency, reliability, canonical resolved rate, and severity-weighted quality remain separate axes.

## Sources

- [`PUBLIC-FAILURE-ANALYSIS.md`](PUBLIC-FAILURE-ANALYSIS.md)
- [`results/2026-08-14-v4/final-report.md`](results/2026-08-14-v4/final-report.md)
- [`results/2026-08-14-v4/summary.json`](results/2026-08-14-v4/summary.json)
- Counted source commit: `19484e9a36f1626fa7aadc6b87e1467e1da53153`
