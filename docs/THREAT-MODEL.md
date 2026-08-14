# Threat model and isolation claims

## Protected assets

- Hidden grader source and assertions during a live campaign.
- Other runs' workspaces and trajectories.
- Host credentials and Hermes authentication material.
- Frozen starters, prompts, runner, sandbox, pricing and roster.
- Sealed completed run artifacts.

## Agent boundary

The model-facing Hermes process must reach the selected provider API, so the host process itself is not placed in a no-network namespace. Instead, the benchmark injects a versioned hook into Hermes' local tool backend. Every terminal/file operation is executed by `runtime/sandbox/sandbox-run` with:

- a private user, mount, network and PID namespace;
- loopback down and socket syscalls denied by seccomp;
- Landlock read/write rules limited to the current workspace plus explicit read-only runtime paths;
- no inherited regular-file stdin/stdout/stderr descriptors;
- no ambient capabilities and `no_new_privs`;
- bounded CPU, memory, process and file resources;
- a minimal environment with credential-like variables removed.

`sitecustomize.py` is loaded only in the host Hermes process. Before the one-shot agent is constructed it forces `skip_memory=true`, `skip_context_files=true`, `load_soul_identity=false` and `fallback_model=None`. Every run must contain exactly one applied cognitive-isolation marker or it is an infrastructure failure.

`HERMES_HOME` is a fresh disposable directory per run and is removed before grading and sealing. Authentication is the only shared state: OpenAI Codex uses the host-side auth store and OpenCode Go receives its provider key in the host Hermes environment. `sandbox-run` rebuilds a minimal environment and removes credential and hook variables before executing every untrusted tool command. The integration proof checks that the OpenCode key is absent inside a real Hermes terminal tool invocation.

## Grader boundary

The grader is never included in the model prompt or workspace. After Hermes exits, the runner:

1. copies the final workspace into a disposable writable directory;
2. invokes the grader through the same no-network sandbox;
3. grants read-only access only to that task's grader bundle;
4. captures one JSON object plus process/timing evidence;
5. destroys the disposable copy.

## Frozen inputs

`freeze-manifest.json` records SHA-256 and byte size for all tasks, graders, harness files, sandbox source, scripts, roster and pricing. The campaign driver calls `freeze.py verify` before selecting any run.

The external Hermes installation is bound separately by `runtime/hermes-runtime-manifest.json`. It inventories the launcher, root Python modules, `agent/`, `hermes_cli/`, `tools/`, dependency lockfiles, Python interpreter hash and installed distribution file hashes. The driver verifies it before campaign selection and the runner verifies it again before every real cell. Safe-mode-excluded UI, skills, plugins, gateway state, user config, memory, sessions and credentials are not content-hashed.

Each completed run records checksums for every retained artifact and a `COMPLETE` marker containing the checksum-file digest. Write bits are removed recursively. The aggregator revalidates these hashes before calculating metrics.

## Tested attacks

The versioned proofs exercise:

- external network connection attempts;
- socket creation;
- writes outside the workspace;
- reads outside the workspace;
- symlink and `/proc/self/fd` escapes;
- descriptor inheritance;
- process limit, capability and namespace state;
- terminal state persistence across legitimate tool calls;
- `write_file` content passed through anonymous stdin pipes;
- the real Hermes `LocalEnvironment` and `ShellFileOperations` classes.

## Non-claims

- This is not a VM boundary and is not presented as protection against a hostile kernel exploit.
- The filesystem owner or root can intentionally restore write bits or alter files; regulatory WORM guarantees require an object-lock store.
- Provider internals, routing and undisclosed model updates cannot be independently verified. The benchmark reports requested route, observed provider/model metadata and timestamped public documentation.
- A public hidden grader can contaminate later campaigns. Grader source is therefore withheld during the active campaign and disclosed afterward; its precommitted hash remains public.
- Wall latency on shared external services is observational, not a pure model-compute measurement.
