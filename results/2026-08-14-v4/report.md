# LLM Engineering Benchmark — campaign-20260814-v4

## Integrity

- 360/360 expected runs observed and verified.
- Primary leaderboard: attempt 1 only, 40 tasks per route.
- Attempts 2–3: preregistered 10-task repeat subset only.
- Six route conditions, five underlying model snapshots; Sol and Daybreak Blue remain distinct route/safeguard conditions.

## Route results

| Route | Resolved | Rate | Mean API-eq. cost | Cost coverage | Cost / resolved | Median | P95 | 3/3 repeat |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Sol | 32/40 | 80.0% | $0.5937 | 38/40 | — | 261.4s | 366.0s | 7/10 |
| Daybreak Blue | 37/40 | 92.5% | $0.4763 | 40/40 | $0.5149 | 184.9s | 300.2s | 10/10 |
| Terra | 34/40 | 85.0% | $0.1725 | 40/40 | $0.2029 | 180.8s | 261.8s | 10/10 |
| Luna | 36/40 | 90.0% | $0.0203 | 40/40 | $0.0225 | 220.2s | 297.5s | 9/10 |
| DeepSeek V4 Flash | 28/40 | 70.0% | $0.0132 | 33/40 | — | 264.4s | 529.6s | 6/10 |
| DeepSeek V4 Pro | 25/40 | 62.5% | $0.0329 | 31/40 | — | 304.2s | 847.1s | 4/10 |

## Cost semantics

- Actual billed total: not asserted.
- Run cost-status inventory: `{'included': 237, 'unknown': 96, 'usage_unavailable': 27}`.
- `api_equivalent_cost_usd` uses the frozen public token-price table.
- Runs with unavailable provider usage are classified as `usage_unavailable`, never as zero-cost observations. Cost charts use the mean over usage-observed primary runs and show coverage explicitly.
- Provider estimates, included usage, unknown billing, and actual billed evidence remain separate.

## Charts

- [Resolved rate](resolved-rate.svg)
- [API-equivalent cost](api-equivalent-cost.svg)
- [Median latency](median-latency.svg)
- [Repeat reliability](repeat-reliability.svg)
- [Resolved rate vs cost](resolved-vs-cost.svg)

## Limitations

- Requested route IDs and provider-reported metadata do not independently prove immutable provider-side weights.
- Shared-service wall latency is observational, not pure model compute time.
- Hidden graders are disclosed only after campaign sealing to avoid contamination.
- The frozen `proof/campaign-plan.json` retained unused v3 command strings and a stale order. The executed and integrity-checked v4 plan was deterministically derived from the frozen `suite.json`; the 360-cell identity sets are equal. The stale proof is retained and disclosed rather than rewritten.
- The campaign driver was externally interrupted twice. Six unsealed partial cells with dead lock PIDs were archived and excluded, then rerun under their originally planned attempt labels. Only checksum-valid sealed artifacts are counted.
- One Daybreak request was rejected before any counted response with the provider error that the requested model was unsupported for the account. The unsealed partial was archived and excluded; the same exact route later succeeded and the planned cell was rerun without fallback.
- The frozen runner inherited a nonsecret dashboard username setting into Hermes/tool process environments, producing the same configuration warning across all 360 sealed runs. The final artifact rescan found no dashboard-auth variable-name reference, and no recorded JSONL isolation trace contained an `env`, `printenv`, or `/proc/*/environ` marker. Those JSONL traces cover sandbox/isolation events rather than a complete candidate command ledger, so this is evidence of no observed use—not proof that the inherited value was inaccessible. The strict environment-allowlist fix is post-campaign.
- No combined scalar ranking is produced; capability, reliability, latency, and normalized cost remain separate axes.
