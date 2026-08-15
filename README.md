<div align="center">
  <h1>LLM Engineering Benchmark</h1>

  <p><strong>40 executable tasks. 10 engineering tracks. 6 agent routes. 360 verified runs.</strong></p>

  <p>An auditable benchmark for AI coding routes, built from real repositories and deterministic grading.</p>

  [![Preflight](https://github.com/BRYANN2K/llm-engineering-benchmark/actions/workflows/preflight.yml/badge.svg)](https://github.com/BRYANN2K/llm-engineering-benchmark/actions/workflows/preflight.yml)
  [![Campaign](https://img.shields.io/badge/campaign-2026--08--14%20v4-7C3AED?style=flat-square)](results/2026-08-14-v4/)
  [![Runs](https://img.shields.io/badge/runs-360%2F360-111827?style=flat-square)](proof/campaign-20260814-v4/full-integrity.json)
  [![License](https://img.shields.io/badge/license-MIT-2563EB?style=flat-square)](LICENSE)
</div>

<p align="center">
  <a href="quality-score-slides/00-overall-hook.svg">
    <img src="quality-score-slides/00-overall-hook.svg" alt="Severity-weighted quality ranking across the six benchmark routes" width="100%">
  </a>
</p>

The benchmark measures whether an agent can change a small software repository and satisfy its public contract plus deterministic private grading. Every route receives the same frozen task, harness, tools, reasoning level, timeout and stopping rules. Provider fallback is disabled.

The first completed release is dated **2026-08-14**. It contains 240 primary runs and 120 preregistered repeats across six route conditions representing five declared underlying models.

## Latest results

Primary attempt only:

| Rank | Route | Resolved | Rate | Mean API-eq. cost | Cost coverage | Repeat 3/3 |
|---:|---|---:|---:|---:|---:|---:|
| 1 | Daybreak Blue | 37/40 | 92.5% | $0.4763 | 40/40 | 10/10 |
| 2 | Luna | 36/40 | 90.0% | $0.0203 | 40/40 | 9/10 |
| 3 | Terra | 34/40 | 85.0% | $0.1725 | 40/40 | 10/10 |
| 4 | Sol standard | 32/40 | 80.0% | $0.5937 | 38/40 | 7/10 |
| 5 | DeepSeek V4 Flash | 28/40 | 70.0% | $0.0132 | 33/40 | 6/10 |
| 6 | DeepSeek V4 Pro | 25/40 | 62.5% | $0.0329 | 31/40 | 4/10 |

The cost column is an API-equivalent estimate over primary runs with provider token telemetry. Missing telemetry is excluded, never counted as zero.

- [Read the dated release summary](results/2026-08-14-v4/)
- [Open the full narrative report](results/2026-08-14-v4/final-report.md)
- [Inspect all 360 result rows](results/2026-08-14-v4/runs.csv)
- [Use the machine-readable summary](results/2026-08-14-v4/summary.json)
- [Verify the campaign integrity proof](proof/campaign-20260814-v4/full-integrity.json)

## Supplemental quality audit

The canonical leaderboard above remains a binary measure of whether each primary attempt satisfied the complete deterministic grader. A separate post-hoc audit scores the residual implementation quality from 0 to 100 using only visible task contracts and the public failure analysis. Its ten category scores are equally weighted, repeat reliability remains separate, and `UI-05` is excluded for every route because the enforced coupon return contract was not explicit in the visible task.

| Rank | Route condition | Quality score | Canonical resolved rate |
|---:|---|---:|---:|
| 1 | Luna | 98.3% | 90.0% |
| 2 | Terra | 97.6% | 85.0% |
| 3 | Daybreak Blue | 96.4% | 92.5% |
| 4 | Sol standard | 92.6% | 80.0% |
| 5 | DeepSeek V4 Flash | 89.6% | 70.0% |
| 6 | DeepSeek V4 Pro | 82.8% | 62.5% |

Luna is the standout on this view: a 98.3% quality score with a mean API-equivalent cost of $0.0203 across 40/40 covered primary runs. That is an observed cost/capability result under this campaign's fixed harness and specifications, not a universal model ranking or a billed-cost claim.

- [Read the scoring method and interpretation limits](QUALITY-SCORES.md)
- [Inspect the machine-readable quality scores](quality-scores.json)
- [Read the public failure analysis](PUBLIC-FAILURE-ANALYSIS.md)
- [Browse the slide deck and its deterministic verifier](quality-score-slides/)

<details>
<summary><strong>Browse all 10 category scorecards</strong></summary>
<br>

<table>
  <tr>
    <td width="50%"><strong>DevOps</strong><br><a href="quality-score-slides/01-devops.svg"><img src="quality-score-slides/01-devops.svg" alt="Severity-weighted DevOps scores" width="100%"></a></td>
    <td width="50%"><strong>Cloud</strong><br><a href="quality-score-slides/02-cloud.svg"><img src="quality-score-slides/02-cloud.svg" alt="Severity-weighted Cloud scores" width="100%"></a></td>
  </tr>
  <tr>
    <td width="50%"><strong>Front end</strong><br><a href="quality-score-slides/03-front-end.svg"><img src="quality-score-slides/03-front-end.svg" alt="Severity-weighted Front end scores" width="100%"></a></td>
    <td width="50%"><strong>Back end</strong><br><a href="quality-score-slides/04-back-end.svg"><img src="quality-score-slides/04-back-end.svg" alt="Severity-weighted Back end scores" width="100%"></a></td>
  </tr>
  <tr>
    <td width="50%"><strong>Full stack</strong><br><a href="quality-score-slides/05-full-stack.svg"><img src="quality-score-slides/05-full-stack.svg" alt="Severity-weighted Full stack scores" width="100%"></a></td>
    <td width="50%"><strong>Bug fixing</strong><br><a href="quality-score-slides/06-bug-fixing.svg"><img src="quality-score-slides/06-bug-fixing.svg" alt="Severity-weighted Bug fixing scores" width="100%"></a></td>
  </tr>
  <tr>
    <td width="50%"><strong>Feature implementation</strong><br><a href="quality-score-slides/07-feature-implementation.svg"><img src="quality-score-slides/07-feature-implementation.svg" alt="Severity-weighted Feature implementation scores" width="100%"></a></td>
    <td width="50%"><strong>Data / SQL</strong><br><a href="quality-score-slides/08-data-sql.svg"><img src="quality-score-slides/08-data-sql.svg" alt="Severity-weighted Data and SQL scores" width="100%"></a></td>
  </tr>
  <tr>
    <td width="50%"><strong>SRE</strong><br><a href="quality-score-slides/09-sre.svg"><img src="quality-score-slides/09-sre.svg" alt="Severity-weighted SRE scores" width="100%"></a></td>
    <td width="50%"><strong>Security</strong><br><a href="quality-score-slides/10-security.svg"><img src="quality-score-slides/10-security.svg" alt="Severity-weighted Security scores" width="100%"></a></td>
  </tr>
</table>

</details>

## Why this benchmark

- **Executable work:** every task is a repository with code, tests and a concrete contract.
- **Deterministic grading:** private graders run after the agent stops and outside its context.
- **Fixed conditions:** tasks, prompts, tools, timeouts, pricing, route roster and seeds are frozen before the campaign.
- **Isolated runs:** each cell gets a fresh workspace, disposable agent state, blocked fallback and a no-network grading sandbox.
- **Auditable outputs:** per-run results, aggregate data, reports, charts, manifests, incidents and integrity proofs are versioned together.

## Experimental routes

| Route | Requested model | Underlying snapshot | Condition |
|---|---|---|---|
| OpenAI Sol | `openai-codex/gpt-5.6-sol` | GPT-5.6 Sol | standard safeguards |
| OpenAI Daybreak Blue | `openai-codex/gpt-daybreak-blue-latest` | GPT-5.6 Sol | separately provisioned defensive-cyber safeguard profile |
| OpenAI Terra | `openai-codex/gpt-5.6-terra` | GPT-5.6 Terra | standard route |
| OpenAI Luna | `openai-codex/gpt-5.6-luna` | GPT-5.6 Luna | standard route |
| DeepSeek V4 Flash | `opencode-go/deepseek-v4-flash` | DeepSeek V4 Flash | OpenCode Go route |
| DeepSeek V4 Pro | `opencode-go/deepseek-v4-pro` | DeepSeek V4 Pro | OpenCode Go route |

Daybreak Blue is a distinct **route/policy condition**, not a sixth unique set of weights. The benchmark reports both route identity and underlying snapshot so the distinction is not obscured.

## Task suite

| Track | IDs | Tasks |
|---|---|---:|
| Bug fixing | `BUG-01..05` | 5 |
| Feature implementation | `FEAT-01..04` | 4 |
| Backend/API | `API-01..05` | 5 |
| Frontend/UI | `UI-01..05` | 5 |
| Full-stack | `FULL-01..03` | 3 |
| Data/SQL | `DATA-01..05` | 5 |
| DevOps | `DEVOPS-01..04` | 4 |
| Cloud/IaC | `CLOUD-01..03` | 3 |
| SRE | `SRE-01..03` | 3 |
| Security | `SEC-01..03` | 3 |
| **Total** |  | **40** |

The exact task IDs, tracks, route matrix, repeat subset, randomization seed, metrics and run counts are preregistered in [`suite.json`](suite.json).

## Campaign design

- 40 tasks × 6 routes × one primary attempt = **240 primary runs**.
- A preregistered, track-balanced subset of 10 tasks gets two additional attempts per route = **120 repeat runs**.
- Total = **360 runs**.
- Primary leaderboard: attempt 1 only.
- Repeats: reliability/variance analysis only; never used to improve the primary score.
- Primary metrics: **resolved rate** and **API-equivalent cost**, with telemetry coverage reported explicitly.
- Secondary metrics: latency, tokens, API/tool calls, agent completion, grader completion and repeat reliability.
- Functional correctness is a gate. Lower cost never compensates for an unresolved task.

## Isolation

Every experimental cell gets:

1. a fresh starter copy and synthetic private Git baseline;
2. a disposable per-run `HERMES_HOME`; a frozen constructor hook forces `skip_memory=true`, `skip_context_files=true`, no soul identity and no fallback, then records an attestation in every run;
3. terminal and file tools confined to the run workspace by user/mount/network/PID namespaces, Landlock, seccomp, capability removal and resource limits;
4. no socket creation and no provider credentials inside agent tools, while the host Hermes process retains only the credential and egress needed to call the selected route;
5. a hidden grader invoked only after the agent stops, in a separate no-network sandbox over a disposable writable copy;
6. a sealed artifact directory containing prompt, stdout/stderr, usage, timing, patch, workspace, grading output and checksums.

The kernel sandbox and the hook into Hermes' real local backend are independently tested under [`proof/`](proof/). See [`docs/THREAT-MODEL.md`](docs/THREAT-MODEL.md) for boundaries and non-claims.

The external Hermes runtime is also frozen by content: launcher, imported Python modules, lockfiles, interpreter, and installed distribution files. The driver verifies that fingerprint before selecting runs, and the runner verifies it again before each real cell.

## Validate the public repository

Requirements: Linux with unprivileged user namespaces and Landlock, Python 3.10+, Git and a C compiler.

```bash
python3 -m py_compile scripts/*.py harness/runner/runner.py
./scripts/build-sandbox
./runtime/sandbox/run-tests
python3 -m unittest discover -s harness/runner/tests -v
python3 -m unittest discover -s tests -v
python3 -m json.tool quality-scores.json >/dev/null
python3 quality-score-slides/verify-slides.py
shasum -a 256 -c SHA256SUMS
```

These are the same public checks run by CI and make no model calls. Full suite and runner-integration validation additionally require the private graders; their frozen commitments and campaign-time validation summaries remain available under [`proof/`](proof/).

## Run campaign

The driver refuses to run unless the frozen source manifest matches byte-for-byte:

```bash
./scripts/build-sandbox
python3 scripts/freeze.py verify
python3 scripts/verify_hermes_runtime.py verify
python3 scripts/run_campaign.py --dry-run
python3 scripts/run_campaign.py --jobs 3 --resume
```

Do not change tasks, prompts, graders, runner, sandbox, route roster, pricing or seeds after the freeze. A change requires a new benchmark version and a fresh campaign.

This operator path is retained for methodology review. Reproducing the original scores also requires the frozen private graders and campaign runtime package, which are not part of this public release.

## Aggregate

```bash
python3 scripts/aggregate.py \
  --runs-root runs/campaign-20260814-v4 \
  --output-dir results/2026-08-14-v4
```

The aggregator verifies every sealed run checksum before computing results. It writes `runs.csv` and `summary.json` under the selected dated output directory. `reasoning_tokens` are reported but not added to output tokens when already included there.

## Cost semantics

- `actual_cost_usd`: populated only when the provider supplies explicit evidence of a billed amount.
- `provider_reported_estimated_cost_usd`: retained separately when Hermes reports a local/provider estimate without billing evidence.
- `api_equivalent_cost_usd`: normalized from frozen public per-token prices.
- `included` and `unknown` are retained as statuses, never silently converted to a billed dollar amount.

See [`pricing/official-pricing-2026-08-13.json`](pricing/official-pricing-2026-08-13.json).

## Public disclosure

This release includes the frozen suite, public task repositories, harness, dated aggregate results, per-run metrics, charts, manifests, integrity evidence and post-campaign incident disclosures.

Raw model outputs, credentials, private archives and complete grader implementations are not included. Public grader commitments bind the withheld grader sources used during the campaign without exposing hidden assertions.

The frozen [`suite.json`](suite.json) keeps its original internal benchmark name and randomization seed. Changing either would break the counted campaign identity and published source commitment; the public repository and release identity are **LLM Engineering Benchmark**.

## Repository structure

```text
.
├── tasks/                         # 40 public executable task repositories
├── results/
│   ├── README.md                  # release index
│   └── 2026-08-14-v4/            # dated reports, CSV, JSON and charts
├── proof/
│   └── campaign-20260814-v4/      # integrity and incident disclosures
├── quality-score-slides/          # overall + 10 category scorecards
├── QUALITY-SCORES.md              # supplemental scoring method and results
├── quality-scores.json            # machine-readable supplemental scores
├── PUBLIC-FAILURE-ANALYSIS.md     # public-safe failure evidence
├── scripts/                       # runner, verification and aggregation tools
├── docs/                          # methodology and threat model
├── pricing/                       # frozen public pricing inputs
└── suite.json                     # task, route and repeat-subset definition
```

## Historical pilot

A five-route, one-task pilot validated early runner and grader mechanics. It is permanently excluded from the leaderboard because the grading command and one hidden assertion were corrected after model calls. Its results are not mixed into this campaign.

## License

Code and task materials are released under the MIT License unless a file says otherwise.
