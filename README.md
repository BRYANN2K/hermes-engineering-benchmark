# Hermes Engineering Benchmark

A reproducible benchmark of raw coding-model routes operating through one fixed [Hermes Agent](https://github.com/NousResearch/hermes-agent) scaffold.

The suite contains **40 original, executable software-engineering tasks** across ten tracks. Each task is a small repository with a public contract and starter tests. Deterministic hidden graders run outside the agent context. The preregistered campaign compares six experimental routes (five underlying model snapshots) over **360 isolated runs**.

> **Campaign status:** suite construction and preflight validation. No leaderboard is published until all frozen runs have completed and passed integrity review.

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

## Suite

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
- Primary metrics: **resolved rate** and **API-equivalent cost per resolved task**.
- Secondary metrics: latency, tokens, API/tool calls, agent completion, grader completion and repeat reliability.
- Functional correctness is a gate. Lower cost never compensates for an unresolved task.

## Isolation

Every experimental cell gets:

1. a fresh starter copy and synthetic private Git baseline;
2. a fresh safe-mode Hermes one-shot session with no user memory, soul, rules, plugins, MCP servers or fallback provider;
3. terminal and file tools confined to the run workspace by user/mount/network/PID namespaces, Landlock, seccomp, capability removal and resource limits;
4. no socket creation from agent tools, while the host Hermes process retains only the egress needed to call the selected model route;
5. a hidden grader invoked only after the agent stops, in a separate no-network sandbox over a disposable writable copy;
6. a sealed artifact directory containing prompt, stdout/stderr, usage, timing, patch, workspace, grading output and checksums.

The kernel sandbox and the hook into Hermes' real local backend are independently tested under [`proof/`](proof/). See [`docs/THREAT-MODEL.md`](docs/THREAT-MODEL.md) for boundaries and non-claims.

## Reproduce preflight tests

Requirements: Linux with unprivileged user namespaces and Landlock, Python 3.10+, Git, a C compiler, and Hermes for the tool-hook integration test.

```bash
./scripts/test-all
python3 scripts/validate_tool_sandbox.py
python3 scripts/validate_runner_integration.py --jobs 4
python3 scripts/freeze.py verify
```

These commands make no model calls. The suite validator requires `private_graders/`; those sources are withheld only while a campaign is live and are published with the final proof bundle.

## Run campaign

The driver refuses to run unless the frozen source manifest matches byte-for-byte:

```bash
./scripts/build-sandbox
python3 scripts/freeze.py verify
python3 scripts/run_campaign.py --dry-run
python3 scripts/run_campaign.py --jobs 3 --resume
```

Do not change tasks, prompts, graders, runner, sandbox, route roster, pricing or seeds after the freeze. A change requires a new benchmark version and a fresh campaign.

## Aggregate

```bash
python3 scripts/aggregate.py
```

The aggregator verifies every sealed run checksum before computing results. It writes `results/runs.csv` and `results/summary.json`. `reasoning_tokens` are reported but not added to output tokens when already included there.

## Cost semantics

- `actual_cost_usd`: populated only when the provider supplies evidence of a priced/billed amount.
- `api_equivalent_cost_usd`: normalized from frozen public per-token prices.
- `included` and `unknown` are retained as statuses, never silently converted to a billed dollar amount.

See [`pricing/official-pricing-2026-08-13.json`](pricing/official-pricing-2026-08-13.json).

## Repository disclosure phases

1. **Pre-campaign:** public briefs/starters, harness, methodology, grader hashes and preflight proofs; active hidden grader sources may remain private.
2. **Post-campaign:** hidden graders, reference/known-bad fixtures, immutable result export, final CSV/report and charts are published.

This prevents agents in a live campaign from retrieving hidden assertions while still making the final benchmark auditable.

## Historical pilot

A five-route, one-task pilot validated early runner and grader mechanics. It is permanently excluded from the leaderboard because the grading command and one hidden assertion were corrected after model calls. Its results are not mixed into this campaign.

## License

Code and task materials are released under the MIT License unless a file says otherwise.
