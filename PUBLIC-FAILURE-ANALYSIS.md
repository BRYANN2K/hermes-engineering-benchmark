# Hermes Engineering Benchmark v4 — public failure analysis

Campaign: `campaign-20260814-v4`

This document supports the X thread that follows the category slides. It is deliberately separate from the visual deck.

## Interpretation rules

- A failure means the primary attempt did not satisfy the deterministic grader.
- The descriptions below name the public task behavior that was missed. They do not reproduce hidden-test names, grader code, assertion text, stack traces, private references, or raw model output.
- These observations describe artifacts from one fixed campaign. They are not causal explanations of model behavior.
- Several routes passed visible tests and still missed private edge cases.
- `UI-05` has an important benchmark-spec limitation: the failing edge enforced a coupon-action return contract that was not explicit in the visible task statement. Its score remains part of the frozen campaign, but the thread must flag that limitation rather than presenting it as a clean capability failure.

Supplemental post-hoc severity-weighted scores are published in [`QUALITY-SCORES.md`](QUALITY-SCORES.md), with machine-readable data in [`quality-scores.json`](quality-scores.json). They exclude `UI-05` from every route because the enforced return contract was not explicit in the visible task. The sealed resolved-rate leaderboard remains canonical.

Route abbreviations:
- Daybreak = Daybreak Blue route condition
- Luna = GPT-5.6 Luna route
- Terra = GPT-5.6 Terra route
- Sol = GPT-5.6 Sol standard route condition
- DS Flash = DeepSeek V4 Flash route
- DS Pro = DeepSeek V4 Pro route

## 01 — DevOps

| Task | Public behavior missed | Failed routes |
|---|---|---|
| `DEVOPS-02` | Atomic release publication did not fully clean state after a failed first publication. | Daybreak, Luna, Terra, Sol, DS Flash, DS Pro |
| `DEVOPS-04` | Restart-safe migration validation and failure recovery were incomplete. | DS Pro |

Public summary: every route missed the same first-publication cleanup edge. DS Pro also missed restart-safe migration behavior.

## 02 — Cloud

| Task | Public behavior missed | Failed routes |
|---|---|---|
| `CLOUD-01` | Infrastructure changes were not consistently ordered by dependencies; replacement and invalid-graph handling were incomplete. | DS Flash |

Public summary: five routes cleared all three Cloud tasks. DS Flash missed dependency-safe planning.

## 03 — Front end

| Task | Public behavior missed | Failed routes |
|---|---|---|
| `UI-05` | Persistent cart coupon-action behavior failed the private grader. | Luna, Terra, DS Flash, DS Pro |

Public summary: Daybreak and Sol cleared all five Front end tasks. Four routes missed the same `UI-05` edge. This result must be accompanied by the spec-limitation disclosure above because the enforced return contract was not explicit in the visible task.

## 04 — Back end

| Task | Public behavior missed | Failed routes |
|---|---|---|
| `API-01` | Conditional-write precondition handling returned the wrong response behavior. | Luna |
| `API-02` | Signed cursor validation did not reject every invalid encoding/signature case. | DS Flash |
| `API-03` | Inventory reservation input/clock validation semantics were incorrect. | Luna, Terra, Sol, DS Flash, DS Pro |
| `API-04` | Webhook signature, timestamp, or header-validation ordering was incorrect. | Sol, DS Pro |

Public summary: Daybreak was the only route to clear all five Back end tasks. `API-03` was the shared failure for every other route.

## 05 — Full stack

| Task | Public behavior missed | Failed routes |
|---|---|---|
| `FULL-01` | The task-board HTTP API was incomplete; one route also violated optimistic-concurrency behavior. | DS Flash, DS Pro |
| `FULL-02` | The poll-voting HTTP handlers were not implemented end to end. | DS Pro |
| `FULL-03` | The support-ticket HTTP handlers were not implemented end to end. | DS Pro |

Public summary: Daybreak, Luna, Terra, and Sol cleared all three Full stack tasks. DS Flash missed the task-board API. DS Pro returned unimplemented HTTP behavior across all three tasks.

## 06 — Bug fixing

| Task | Public behavior missed | Failed routes |
|---|---|---|
| `BUG-02` | Deep configuration merge broke immutability, sibling preservation, deletion semantics, or input validation. | DS Flash |
| `BUG-04` | Streaming NDJSON validation did not enforce byte-based line limits correctly. | DS Pro |
| `BUG-05` | Backup retention mishandled per-label selection, duplicate names, or time validation. | Terra, Sol, DS Flash |

Public summary: Daybreak and Luna cleared all five bug-fixing tasks. The remaining misses were concentrated in deep merge, streaming validation, and retention edge cases.

## 07 — Feature implementation

| Task | Public behavior missed | Failed routes |
|---|---|---|
| `FEAT-01` | Environment placeholder expansion accepted an invalid input/type edge. | Terra, DS Pro |
| `FEAT-03` | Dependency batch grouping constraints were not preserved. | DS Flash |
| `FEAT-04` | Retry-policy validation happened with incorrect semantics or ordering. | DS Flash, DS Pro |

Public summary: Daybreak, Luna, and Sol cleared all four feature tasks. Terra missed one validation edge; both DeepSeek routes missed two tasks.

## 08 — Data / SQL

| Task | Public behavior missed | Failed routes |
|---|---|---|
| `DATA-01` | Strict CSV ingestion rejection/accounting semantics were incorrect. | Daybreak, Terra, Sol, DS Flash, DS Pro |
| `DATA-02` | The SQLite invoice migration did not satisfy the required atomic migration behavior. | Sol |
| `DATA-03` | The SQL report returned incorrect aggregate results. | DS Pro |
| `DATA-05` | Inventory batch validation allowed an invalid intermediate stock state. | DS Flash |

Public summary: `DATA-01` was the shared wall. Luna was the only route to clear all five Data / SQL tasks.

## 09 — SRE

| Task | Public behavior missed | Failed routes |
|---|---|---|
| `SRE-01` | Incident hysteresis timing, null resets, or input validation was incorrect. | DS Pro |
| `SRE-03` | Outage reconstruction mishandled same-timestamp batches, stale probes, or quorum transitions. | DS Pro |

Public summary: five routes cleared all three SRE tasks. DS Pro missed two state-machine edge cases.

## 10 — Security

| Task | Public behavior missed | Failed routes |
|---|---|---|
| `SEC-01` | Safe bundle installation missed rollback, path-prefix, or symlink-ancestor safety behavior. | Daybreak, Sol |
| `SEC-02` | Replay protection mishandled concurrency or state-mutation boundaries. | Sol |

Public summary: Luna, Terra, DS Flash, and DS Pro cleared all three Security tasks. Daybreak missed the bundle-install task; Sol missed both bundle installation and replay protection.
