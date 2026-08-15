# LLM Engineering Benchmark — Final Report

**Campaign:** `campaign-20260814-v4`  
**Generated:** 2026-08-15T00:42:29Z  
**Status:** complete; 360/360 planned cells sealed and integrity-verified  
**Counted source commit:** `19484e9a36f1626fa7aadc6b87e1467e1da53153`  
**Frozen source tree:** `ee3327ff74001ae79175c7b103ebcf88b61b2797d3d966aeacf4efac38d13d6f`

> This is the human-readable analysis of the sealed campaign. The canonical machine-generated metrics remain in [`report.md`](report.md), [`summary.json`](summary.json), and [`runs.csv`](runs.csv). No raw model response is included in the public result set.

## Executive summary

The benchmark evaluated six model routes on 40 original executable software-engineering tasks using one frozen Hermes Agent scaffold. The primary leaderboard contains 240 attempt-1 runs. A preregistered, track-balanced subset of ten tasks received two additional attempts per route, adding 120 reliability runs. All 360 planned cells were found, sealed, checksum-valid, and accepted by the full integrity verifier.

Daybreak Blue recorded the highest primary resolved rate at **37/40 (92.5%)**. Luna followed at **36/40 (90.0%)** while posting the lowest mean API-equivalent cost among routes with complete primary-run token telemetry. Terra resolved **34/40 (85.0%)**, had the lowest median latency, and matched Daybreak's perfect 10/10 strict repeat score. Sol resolved **32/40 (80.0%)**. DeepSeek V4 Flash and Pro resolved **28/40 (70.0%)** and **25/40 (62.5%)**, respectively.

Daybreak Blue and Sol are not two independently identified model snapshots. They are two route/policy conditions mapped to the same declared GPT-5.6 Sol underlying snapshot. Daybreak succeeded on five tasks that Sol missed, while Sol succeeded on no task that Daybreak missed. The exact paired two-sided McNemar value is `0.0625`: suggestive, but not conventional `p < 0.05` evidence. The result supports a route-condition difference in this campaign; it does **not** establish different underlying weights or a general capability gap.

## Headline results

Primary leaderboard, attempt 1 only:

| Route condition | Resolved | Rate | Mean API-eq. cost¹ | Coverage | Cost / resolved² | Median | P95 | Repeat 3/3³ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **Daybreak Blue** | **37/40** | **92.5%** | $0.4763 | 40/40 | $0.5149 | 184.9s | 300.2s | **10/10** |
| **Luna** | **36/40** | **90.0%** | **$0.0203** | 40/40 | **$0.0225** | 220.2s | 297.5s | 9/10 |
| **Terra** | **34/40** | **85.0%** | $0.1725 | 40/40 | $0.2029 | **180.8s** | **261.8s** | **10/10** |
| **Sol standard** | **32/40** | **80.0%** | $0.5937 | 38/40 | — | 261.4s | 366.0s | 7/10 |
| **DeepSeek V4 Flash** | **28/40** | **70.0%** | $0.0132 | 33/40 | — | 264.4s | 529.6s | 6/10 |
| **DeepSeek V4 Pro** | **25/40** | **62.5%** | $0.0329 | 31/40 | — | 304.2s | 847.1s | 4/10 |

1. Mean over primary runs with observed provider token telemetry, using the frozen API-equivalent price table. Missing telemetry is excluded, never treated as zero cost.  
2. Reported only when primary cost coverage is complete.  
3. Number of tasks in the ten-task repeat subset resolved on all three attempts. Repeats are excluded from the primary leaderboard.

### What the table supports

- **Highest measured pass rate:** Daybreak Blue.
- **Strongest measured cost/capability combination with complete telemetry:** Luna, with 90.0% resolved at a $0.0203 observed mean API-equivalent cost.
- **Lowest observed latency:** Terra, at 180.8 seconds median and 261.8 seconds P95.
- **Strict repeat leaders:** Daybreak Blue and Terra, both 10/10.
- **No scalar overall winner:** capability, cost, reliability, and latency remain separate axes by design.

## Experimental design

### Task suite

The suite contains 40 original tasks across ten tracks:

| Track | Tasks |
|---|---:|
| Bug fixing | 5 |
| Feature implementation | 4 |
| Backend/API | 5 |
| Frontend/UI | 5 |
| Full-stack | 3 |
| Data/SQL | 5 |
| DevOps/CI | 4 |
| Cloud/IaC | 3 |
| SRE | 3 |
| Security | 3 |
| **Total** | **40** |

Each task is a small repository with a public contract, starter tests, and a deterministic hidden grader. Hidden graders run outside the agent context and without external network access.

### Route matrix

| Route | Requested model | Declared underlying snapshot | Condition |
|---|---|---|---|
| Sol standard | `openai-codex/gpt-5.6-sol` | GPT-5.6 Sol | standard safeguards |
| Daybreak Blue | `openai-codex/gpt-daybreak-blue-latest` | GPT-5.6 Sol | separately provisioned defensive-cyber safeguard profile |
| Terra | `openai-codex/gpt-5.6-terra` | GPT-5.6 Terra | standard route |
| Luna | `openai-codex/gpt-5.6-luna` | GPT-5.6 Luna | standard route |
| DeepSeek V4 Flash | `opencode-go/deepseek-v4-flash` | DeepSeek V4 Flash | OpenCode Go route |
| DeepSeek V4 Pro | `opencode-go/deepseek-v4-pro` | DeepSeek V4 Pro | OpenCode Go route |

There are six route conditions but only five declared underlying model snapshots. Daybreak Blue is a separately provisioned defensive-cyber safeguard condition and is not counted as a sixth unique model.

### Controlled variables

Every comparable route used the same:

- task prompt and starter repository;
- Hermes scaffold and frozen runtime;
- `reasoning=high` setting;
- terminal and file tool surface;
- maximum turns and wall timeout;
- no-fallback rule;
- hidden grader and grading timeout;
- source, runner, sandbox, pricing table, and stopping rules.

Each cell received a fresh starter copy and synthetic private Git baseline, a disposable `HERMES_HOME`, no memory, no context files, no soul identity, and no session persistence. Candidate tools had no network access. The provider transport remained in the host Hermes process. Graders ran after the agent stopped in a separate no-network sandbox.

### Attempts and metrics

- **240 primary runs:** 40 tasks × six routes × attempt 1.
- **120 repeat runs:** two additional attempts for ten preregistered tasks × six routes.
- **360 total sealed runs.**
- Primary metric: resolved rate at attempt 1.
- Primary economic metric: API-equivalent cost, with telemetry coverage shown explicitly.
- Secondary metrics: strict all-three repeat reliability, median/P95 latency, API calls, sandboxed tool invocations, and provider errors.

Functional correctness is a gate. Low cost cannot compensate for an unresolved task.

## Results by engineering category

All 40 primary tasks are assigned exactly once across ten publication categories. The five categories requested at inception appear first, followed by five complementary categories added for broader engineering coverage.

| Group | Publication category | Frozen track | Tasks |
|---|---|---|---:|
| Requested | DevOps | `devops_ci` | 4 |
| Requested | Cloud | `cloud_iac` | 3 |
| Requested | Front end | `frontend_ui` | 5 |
| Requested | Back end | `backend_api` | 5 |
| Requested | Full stack | `full_stack` | 3 |
| Complementary | Bug fixing | `repository_bug_fixing` | 5 |
| Complementary | Feature implementation | `feature_implementation` | 4 |
| Complementary | Data / SQL | `data_sql` | 5 |
| Complementary | SRE | `sre_troubleshooting` | 3 |
| Complementary | Security | `security` | 3 |
| **Total** |  |  | **40** |

Primary resolved count and rate:

| Category | Daybreak | Luna | Terra | Sol | DS Flash | DS Pro |
|---|---:|---:|---:|---:|---:|---:|
| DevOps | 3/4 · 75% | 3/4 · 75% | 3/4 · 75% | 3/4 · 75% | 3/4 · 75% | 2/4 · 50% |
| Cloud | 3/3 · 100% | 3/3 · 100% | 3/3 · 100% | 3/3 · 100% | 2/3 · 66.7% | 3/3 · 100% |
| Front end | 5/5 · 100% | 4/5 · 80% | 4/5 · 80% | 5/5 · 100% | 4/5 · 80% | 4/5 · 80% |
| Back end | 5/5 · 100% | 3/5 · 60% | 4/5 · 80% | 3/5 · 60% | 3/5 · 60% | 3/5 · 60% |
| Full stack | 3/3 · 100% | 3/3 · 100% | 3/3 · 100% | 3/3 · 100% | 2/3 · 66.7% | 0/3 · 0% |
| Bug fixing | 5/5 · 100% | 5/5 · 100% | 4/5 · 80% | 4/5 · 80% | 3/5 · 60% | 4/5 · 80% |
| Feature implementation | 4/4 · 100% | 4/4 · 100% | 3/4 · 75% | 4/4 · 100% | 2/4 · 50% | 2/4 · 50% |
| Data / SQL | 4/5 · 80% | 5/5 · 100% | 4/5 · 80% | 3/5 · 60% | 3/5 · 60% | 3/5 · 60% |
| SRE | 3/3 · 100% | 3/3 · 100% | 3/3 · 100% | 3/3 · 100% | 3/3 · 100% | 1/3 · 33.3% |
| Security | 2/3 · 66.7% | 3/3 · 100% | 3/3 · 100% | 1/3 · 33.3% | 3/3 · 100% | 3/3 · 100% |

Notable fixed-suite observations:

- `DEVOPS-02` was unresolved by all six routes.
- `API-03` and `DATA-01` were each resolved by only one route.
- `UI-05` was resolved by two routes.
- Fifteen tasks were resolved by all six routes.
- Track counts are descriptive; several tracks contain only three tasks and should not be generalized as standalone domain benchmarks.

## Sol standard versus Daybreak Blue

Both routes are mapped to the same declared GPT-5.6 Sol underlying snapshot, but they are different route/policy conditions.

### Paired primary outcomes

| Outcome over the same 40 tasks | Count |
|---|---:|
| Both resolved | 32 |
| Both failed | 3 |
| Daybreak only | 5 |
| Sol only | 0 |

Daybreak-only tasks: `API-03`, `API-04`, `BUG-05`, `DATA-02`, and `SEC-02`.

The exact paired two-sided McNemar value is `0.0625`. Because the suite is a fixed set of 40 tasks rather than a random sample of all software engineering, this value is a sensitivity check, not a population-level proof. It is also slightly above the conventional `0.05` threshold.

The routes had almost identical mean API-call counts—17.125 for Daybreak and 17.15 for Sol—so the observed primary gap is not explained by Daybreak simply receiving more agent iterations. Daybreak also had a lower median wall time and stronger strict repeat score in this campaign. Possible causes include the route policy, inference stochasticity, or provider-side serving differences. The artifacts do not identify a causal mechanism.

Most importantly, requested route IDs and provider metadata do not independently prove immutable provider-side weights. The report therefore claims a measured **route-condition difference**, not that one set of model weights is intrinsically better than another.

## Reliability

The repeat subset contains ten preregistered tasks balanced across the ten tracks. A task counts as reliable only if all three attempts resolved it.

| Route | All three attempts resolved | Strict consistency |
|---|---:|---:|
| Daybreak Blue | 10/10 | 100% |
| Terra | 10/10 | 100% |
| Luna | 9/10 | 90% |
| Sol standard | 7/10 | 70% |
| DeepSeek V4 Flash | 6/10 | 60% |
| DeepSeek V4 Pro | 4/10 | 40% |

This metric is intentionally strict. It is not pass@3 and does not award success when only one of three attempts resolves the task.

## Cost analysis

The report does not assert an actual billed campaign total. Billing evidence and normalized economic comparisons remain separate.

Across all 360 sealed runs:

| Cost status | Runs |
|---|---:|
| `included` | 237 |
| `unknown` | 96 |
| `usage_unavailable` | 27 |

`api_equivalent_cost_usd` is normalized from the frozen public token-price table. Reasoning tokens are reported separately but are not added again when already included in output-token accounting. Provider estimates, included-account usage, unknown billing, and actual billed evidence are never collapsed into one number.

Two Sol primary runs, seven DeepSeek V4 Flash primary runs, and nine DeepSeek V4 Pro primary runs lacked provider token telemetry. Their capability outcomes remain counted, but they are excluded from mean-cost calculations. For that reason, cost-per-resolved is not asserted for those routes.

The normalized cost data supports a strong descriptive result for Luna: its 90.0% resolved rate came with complete primary telemetry and a $0.0203 mean API-equivalent cost. DeepSeek V4 Flash has a lower observed mean, but only 33/40 primary runs have cost telemetry, so the comparison is not complete.

## Latency and operational behavior

| Route | Median wall time | P95 wall time | Mean API calls | Mean sandboxed tool invocations |
|---|---:|---:|---:|---:|
| Terra | 180.8s | 261.8s | 14.45 | 52.60 |
| Daybreak Blue | 184.9s | 300.2s | 17.13 | 59.48 |
| Luna | 220.2s | 297.5s | 17.40 | 55.23 |
| Sol standard | 261.4s | 366.0s | 17.15 | 61.38 |
| DeepSeek V4 Flash | 264.4s | 529.6s | 20.65 | 53.75 |
| DeepSeek V4 Pro | 304.2s | 847.1s | 17.90 | 47.18 |

Wall time is observational shared-service latency, not pure model compute time. It includes provider transport and the complete agent trajectory.

## Integrity and auditability

The counted campaign is bound to:

| Artifact | Commitment |
|---|---|
| Source commit | `19484e9a36f1626fa7aadc6b87e1467e1da53153` |
| Source inventory | 471 files |
| Source tree | `ee3327ff74001ae79175c7b103ebcf88b61b2797d3d966aeacf4efac38d13d6f` |
| Hermes runtime | 594 files; `a996ff33779fd30e727144c28d3b3fbb391031f293ed2ecfd11233d29faf2c45` |
| Executed derived plan | 360 cells; `6a91fbf2a972cfd7135a5a5c6bc5cc21949857eb60fb1643ef3d67c8d428fdf2` |
| Sealed archive | 9,577,232 bytes; `0c8e655af8d36fde2b4efa34650900fd5c5bb57b3323cf2dd1ebdf203114c375` |

The full integrity verifier reported:

- 360 expected runs;
- 360 runs found;
- zero missing run keys;
- zero extra run keys;
- valid seals and checksums;
- verified runtime and tool-sandbox attestations;
- completed Hermes and grader execution for every counted cell.

The public candidate includes the per-run CSV, machine summary, charts, full integrity report, derived plan, incident reports, grader commitments, and post-seal grader disclosure. The raw sealed archive contains model outputs and remains private; its manifest and checksum are public-facing audit attestations.

## Incidents and disclosures

### Stale frozen proof plan

The frozen `proof/campaign-plan.json` retained v3 command strings and a stale order. It was not consumed by the execution or integrity paths. Both paths derived the 360-cell plan from the frozen `suite.json`. The stale proof and incident are retained unchanged, while the derived executed v4 plan is disclosed separately.

### Driver interruptions

The campaign driver was externally interrupted twice. Six incomplete cells with dead runner/lock PIDs and no surviving command-line references were archived and excluded. Previously sealed runs were preserved. The excluded cells were rerun under their original planned attempt labels; only the final checksum-valid sealed cells are counted.

### Daybreak route rejection

One unsealed Daybreak request for `DATA-04`, attempt 3, was rejected before a counted response because the requested route was temporarily reported unsupported for the account. The partial artifact was archived and excluded. The exact same route later succeeded and the planned cell was rerun without provider or model fallback.

### Inherited nonsecret dashboard username

The frozen runner inherited a nonsecret dashboard username setting into Hermes/tool process environments and emitted the same warning across all 360 sealed runs. No dashboard password or secret variable was present. The final text-artifact scan found zero references to the dashboard-auth variable names, and recorded JSONL isolation traces contained no `env`, `printenv`, or `/proc/*/environ` marker. Those traces are not a complete candidate command ledger, so this is evidence of no observed use—not proof that the inherited value was inaccessible. The explicit environment-allowlist fix is deferred to a separate post-campaign change and is not presented as retroactive protection.

## Limitations and non-claims

1. Route names and provider metadata do not independently prove immutable provider-side weights.
2. Six route conditions represent five declared underlying model snapshots.
3. Forty fixed tasks provide an auditable benchmark result, not a universal estimate of all software-engineering ability.
4. Small track sizes make track-level differences descriptive only.
5. Shared-service latency is observational and may vary with provider load.
6. Twenty-seven runs lack provider token telemetry; no missing cost is treated as zero.
7. Actual billed campaign cost is not asserted.
8. Hidden graders were private during execution. Their frozen commitments are public; complete grader implementations are not included in this release.
9. Historical v1–v3 campaigns and the pilot remain excluded from the leaderboard.
10. No combined scalar ranking is produced.

## Per-route primary failures

| Route | Failed task IDs |
|---|---|
| Daybreak Blue | `DATA-01`, `DEVOPS-02`, `SEC-01` |
| Luna | `API-01`, `API-03`, `DEVOPS-02`, `UI-05` |
| Terra | `API-03`, `BUG-05`, `DATA-01`, `DEVOPS-02`, `FEAT-01`, `UI-05` |
| Sol standard | `API-03`, `API-04`, `BUG-05`, `DATA-01`, `DATA-02`, `DEVOPS-02`, `SEC-01`, `SEC-02` |
| DeepSeek V4 Flash | `API-02`, `API-03`, `BUG-02`, `BUG-05`, `CLOUD-01`, `DATA-01`, `DATA-05`, `DEVOPS-02`, `FEAT-03`, `FEAT-04`, `FULL-01`, `UI-05` |
| DeepSeek V4 Pro | `API-03`, `API-04`, `BUG-04`, `DATA-01`, `DATA-03`, `DEVOPS-02`, `DEVOPS-04`, `FEAT-01`, `FEAT-04`, `FULL-01`, `FULL-02`, `FULL-03`, `SRE-01`, `SRE-03`, `UI-05` |

## Artifacts

### Results

- [Canonical metrics report](report.md)
- [Per-run metrics](runs.csv)
- [Machine-readable summary](summary.json)
- [Report manifest](report-manifest.json)

### Charts

- [Resolved rate](resolved-rate.svg)
- [API-equivalent cost](api-equivalent-cost.svg)
- [Median latency](median-latency.svg)
- [Repeat reliability](repeat-reliability.svg)
- [Resolved rate versus cost](resolved-vs-cost.svg)

### Proofs

- [Full campaign integrity](../../proof/campaign-20260814-v4/full-integrity.json)
- [Derived executed plan](../../proof/campaign-20260814-v4/derived-plan.json)
- [Incident disclosures](../../proof/campaign-20260814-v4/incidents/)
- [Private archive release manifest](../../proof/campaign-20260814-v4/private-archive-release-manifest.json)
- [Frozen grader commitments](../../proof/grader-commitments.json)
- [Frozen suite definition](../../suite.json)

## Conclusion

The strongest defensible conclusions from `campaign-20260814-v4` are:

1. **Daybreak Blue achieved the highest measured primary pass rate and perfect strict repeat reliability.**
2. **Luna delivered the strongest measured capability/cost combination with complete primary telemetry.**
3. **Terra was the fastest route and matched Daybreak's strict repeat reliability.**
4. **The Daybreak-versus-Sol result is a route-condition finding, not evidence of different underlying model weights.**
5. **The DeepSeek routes were cheaper on observed normalized usage but less capable and less consistent on this fixed suite; incomplete cost telemetry limits direct economic comparison.**

These claims are bounded to the frozen tasks, harness, route identities, provider conditions, and campaign date documented above.
