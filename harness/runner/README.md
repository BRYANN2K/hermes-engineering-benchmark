# LLM Engineering Benchmark runner

A dependency-free Python harness for running the **same agent scaffold** against the fixed six-route matrix and freezing one artifact directory per `route × task × attempt`.

The runner executes `/opt/hermes/bin/hermes` in one-shot mode, then invokes a separate hidden grader that is never included in the model prompt. It does not contain pricing tables or calculate normalized API-equivalent pricing.

## Frozen model matrix

| Provider | Model |
|---|---|
| `openai-codex` | `gpt-5.6-sol` |
| `openai-codex` | `gpt-daybreak-blue-latest` (Daybreak Blue; current snapshot: Sol) |
| `openai-codex` | `gpt-5.6-terra` |
| `openai-codex` | `gpt-5.6-luna` |
| `opencode-go` | `deepseek-v4-flash` |
| `opencode-go` | `deepseek-v4-pro` |

`run` rejects any provider/model pair outside this matrix. `matrix` always uses these six provider/model routes in this order.

Daybreak Blue currently uses `gpt-5.6-sol` as its default snapshot, but it is a separately approved route whose safeguards are calibrated for authorized defensive cybersecurity work. The matrix therefore keeps normal Sol and Daybreak Blue as distinct routes while reporting that they share a base snapshot. The accepted Codex slug is `gpt-daybreak-blue-latest`; the shorter `daybreak-blue-latest` slug is rejected by this surface.

## Reproducibility and isolation contract

For every model, the runner fixes or records:

- identical prompt bytes from `--prompt-file`;
- identical explicit `--reasoning` and `--toolsets` values;
- explicit provider, model, and `--usage-file` arguments;
- Hermes `--safe-mode` to exclude user config, rules, plugins, MCP servers and hooks;
- a disposable per-run `HERMES_HOME`, removed immediately after the agent process exits;
- a frozen constructor hook that forces `skip_memory`, `skip_context_files`, no soul identity and no fallback, with an applied marker required in the sealed trace;
- shared provider credentials available only to the host Hermes process; `sandbox-run` rebuilds a minimal environment and strips credential/hook variables before each tool command;
- `TZ=UTC`, `LC_ALL=C.UTF-8`, and the same wall-clock limits;
- a 90-turn budget. Hermes v0.20.0 one-shot constructs `AIAgent` with 90 turns and exposes no one-shot `--max-turns` flag, so this runner rejects every other `--max-turns` value rather than pretending it can enforce one;
- a content fingerprint for the external Hermes launcher, imported Python modules, lockfiles, interpreter and installed distribution files, verified before every real cell;
- the starter content digest, original Git metadata when available, prompt digest, grader digest, and exact command.

Each run receives a private copy of the starter **content**. Source `.git` metadata is not copied: copied linked worktrees can point their index back at the source, which is unsafe under parallelism. Instead, the runner creates a synthetic private baseline commit inside each workspace. This keeps source trees untouched and makes `git.diff`/`git.patch` describe only benchmark changes. Git-ignored starter files are included in the baseline.

The Python runner itself uses only the standard library. Runtime prerequisites are Python 3.10+, Git, the Hermes executable, and an executable grader.

## Hidden grader interface

The grader must be an executable with this interface:

```text
GRADER WORKSPACE [--grader-arg values ...]
```

- `WORKSPACE` is a disposable copy of the model-modified workspace.
- The grader is run only after Hermes exits or times out.
- The model receives only the task prompt; it never sees the grader path, arguments, or output.
- The grader must write exactly one JSON object to stdout. A conventional result is:

```json
{
  "passed": true,
  "score": 1.0,
  "details": {"tests": 12, "failed": 0}
}
```

`passed` must be a JSON boolean for `outcome.success` to become true. Any additional grader fields are preserved verbatim under `result.json` → `grader`. Grader stdout/stderr, exit status, timeout status, and timing are retained even when the output is invalid.

Dash-prefixed grader arguments should use the equals form so `argparse` does not consume them as runner options:

```bash
--grader-arg=--hidden-mode --grader-arg=strict
```

## Dry-run: no model calls and no run directories

Dry-run validates the starter and prompt, prints the exact six-run plan, and does **not** require the Hermes or grader paths to exist:

```bash
python3 runner.py matrix \
  --starter /path/to/starter \
  --prompt-file /path/to/prompt.txt \
  --task-id backend-001 \
  --grader /private/graders/backend-001 \
  --reasoning high \
  --toolsets terminal,file \
  --timeout 1800 \
  --grader-timeout 300 \
  --attempt 1 \
  --dry-run
```

Use this before any paid campaign to audit prompt hash, matrix, tools, reasoning, limits, and generated commands.

## Run one model

```bash
python3 runner.py run \
  --starter /path/to/starter \
  --prompt-file /path/to/prompt.txt \
  --task-id backend-001 \
  --grader /private/graders/backend-001 \
  --provider openai-codex \
  --model gpt-5.6-sol \
  --reasoning high \
  --toolsets terminal,file \
  --timeout 1800 \
  --grader-timeout 300 \
  --attempt 1
```

A random, collision-resistant run ID is generated by default. Use a fixed key when orchestration needs deterministic resume behavior:

```bash
python3 runner.py run ... --run-key campaign1__backend-001__a1__gpt-5.6-sol
python3 runner.py run ... --run-key campaign1__backend-001__a1__gpt-5.6-sol --resume
```

A second invocation without `--resume` always refuses to overwrite the directory.

## Run the matrix in parallel

```bash
python3 runner.py matrix \
  --starter /path/to/starter \
  --prompt-file /path/to/prompt.txt \
  --task-id backend-001 \
  --grader /private/graders/backend-001 \
  --reasoning high \
  --toolsets terminal,file \
  --timeout 1800 \
  --grader-timeout 300 \
  --attempt 1 \
  --jobs 6 \
  --batch-id campaign1
```

`--jobs` bounds concurrent subprocesses. Every worker has a different run directory and private workspace. Matrix stdout is one summary object in fixed model order. A worker setup/finalization exception appears in `errors` and makes the matrix process return 2; task failure, model timeout, or grader failure still produces a complete run artifact and is represented by `result.json` rather than discarded.

Resume the same deterministic matrix keys with:

```bash
python3 runner.py matrix ... --jobs 6 --batch-id campaign1 --resume
```

Completed runs are checksum-verified and returned as `already_complete`. Incomplete runs resume only when `request.json` exactly matches the current starter, prompt, grader, executable paths, model, provider, reasoning, tools, arguments, and limits. Live PID locks block concurrent reuse. This prevents a nominal resume from silently changing the benchmark inputs.

## Timeout behavior

Hermes and the grader run in separate process groups. At timeout, the runner sends `SIGTERM` to the whole group, waits three seconds, then sends `SIGKILL` if needed. A timed-out Hermes run still gets:

- stdout/stderr and exit/timing records;
- a synthetic `usage.json` with unavailable values represented as `null` if Hermes did not write one;
- Git evidence from whatever state the workspace reached;
- a grader invocation and `result.json`.

No telemetry category is converted from unknown to zero.

## Artifact layout

A completed directory under `runs/` contains:

```text
<run-id>/
├── COMPLETE                 completion marker + checksum-file digest
├── checksums.sha256         SHA-256 for every retained artifact except marker/checksum file
├── request.json             frozen resume identity
├── manifest.json            model/task/scaffold/limit/grader metadata
├── prompt.txt               exact prompt bytes used
├── stdout.txt               Hermes final stdout
├── stderr.txt               Hermes stderr
├── usage.json               Hermes-native usage, or explicit null fallback
├── timing.json              Hermes + grader UTC timestamps and wall seconds
├── exit_status.json         return code, timeout flag, launch error
├── git-status.txt           final porcelain status
├── git.diff                 readable full workspace diff, including untracked text
├── git.patch                binary/full-index applyable patch
├── grader.stdout.txt        grader's raw JSON/output
├── grader.stderr.txt        grader diagnostics
├── result.json              parsed grader result + benchmark outcome
├── state.json               final resumable stage record
└── workspace/               final model-modified private Git workspace
```

`manifest.json`, `result.json`, and native usage have schemas in [`schemas/`](schemas/):

- `manifest.schema.json`
- `result.schema.json`
- `usage.schema.json`

A complete run has all write bits recursively removed after checksums are written. The exclusive directory policy, frozen request identity, lock, checksums, completion marker, and read-only permissions make the artifact immutable by normal runner operation. A filesystem owner/root can still deliberately change Unix permissions; use a WORM/object-lock store for regulatory immutability.

## Result interpretation

The runner process returning 0 means the artifact was successfully finalized, **not** that the model passed. Read:

```json
{
  "outcome": {
    "success": true,
    "passed": true,
    "score": 1.0,
    "hermes_completed": true,
    "grader_completed": true
  }
}
```

`outcome.success` requires all three conditions: Hermes completed without timeout, the grader completed without timeout, and the grader returned `"passed": true`.

`usage.json` is retained in Hermes-native form. The manifest intentionally has:

```json
{
  "pricing": {
    "normalized_api_cost_usd": null,
    "price_snapshot_id": null,
    "status": "not_configured"
  }
}
```

No public-price assumptions or guessed normalized prices are present.

## Local verification (no model calls)

The test suite creates temporary Git starters, a mock Hermes executable, and a mock hidden grader. It covers planning, all six parallel workers, artifacts, patch capture, timeout handling, no-overwrite behavior, checksum-verified resume, and changed-input rejection:

```bash
python3 -m unittest discover -s tests -v
```

The tests never execute `/opt/hermes/bin/hermes` and never access a model provider.
