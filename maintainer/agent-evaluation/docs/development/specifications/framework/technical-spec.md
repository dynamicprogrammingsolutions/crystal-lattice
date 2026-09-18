# Agent evaluation framework technical specification

## Architecture

The reusable package under `maintainer/agent-evaluation/src/agent_eval/` owns:

- `AgentEval`, the run coordinator;
- `RunEnvironment`, the runtime replacement protocol;
- `RunServices`, evidence and record services available during execution;
- `Run`, the immutable completed result;
- workspace preparation and optional Git helpers;
- explicit cache and continuation support;
- canonical and raw result persistence.

Generic modules must remain importable without importing the bundled Crystal
Lattice environment.

## Kernel API

```python
AgentEval.run(
    name,
    program,
    *,
    environment=None,
    continue_from=None,
    workspace=None,
    cache_key=None,
)
```

`program(context)` may execute arbitrary Python and return any value supported
by result serialization. The kernel does not inspect program source or assign
meaning to messages, prompts, guidance, models, scores, or files.

## Run environment

A `RunEnvironment` supplies:

```python
fingerprint() -> object
open(*, services, workspace, parent_snapshot) -> context manager
snapshot(context) -> object | None
finalize(context) -> object
```

The fingerprint participates in cache and continuation compatibility. `open`
owns runtime lifecycle. `snapshot` returns reusable environment state.
`finalize` returns a concise environment observation for the completed run.

## Lifecycle

For an uncached run the kernel:

1. establishes run identity and result paths;
2. prepares the workspace;
3. resolves and fingerprints the environment;
4. validates parent compatibility;
5. checks an explicit cache key;
6. opens the environment and calls the program;
7. snapshots and finalizes the environment;
8. records workspace changes, evidence, value, and errors;
9. publishes a complete cache entry when applicable;
10. returns an immutable `Run`.

Failures at preparation, environment, program, snapshot, finalize, or
persistence boundaries remain structured and inspectable.

## Workspace, continuation, and cache

A run may use no workspace, an existing path, or a caller-owned workspace
factory. The optional Git helper creates clean pinned worktrees and reports
status and diffs.

Continuation requires a compatible environment fingerprint and hash-verified
parent snapshot. Caching is opt-in and combines caller key, environment,
workspace, parent state, and cache schema. Program source is not inferred;
callers change their cache key when semantics change.

## Evidence and results

Evidence is a named observation. Files saved for later inspection are result
files. The kernel maintains concise canonical records and separately retained
raw environment, workspace, and error data. Environments and programs may
redact, project, or select evidence appropriate to an evaluator or reviewer.

A `Run` exposes value, snapshot, observation, workspace, changed paths, result
location, parent/cache provenance, and structured error information. It does
not own a universal pass/fail verdict.

## Security and retention

Default result paths are ignored local output. Authentication material and
secrets are excluded or redacted by the owning environment. Cache writes are
locked and atomic; incomplete entries are not reusable.

## Optional environments

The bundled Crystal Lattice adapter is specified separately by
[Crystal Lattice evaluation environment](../crystal-lattice-environment/index.md).
Consumer suites remain ordinary package clients and own their scenarios,
models, assertions, and delivery semantics.
