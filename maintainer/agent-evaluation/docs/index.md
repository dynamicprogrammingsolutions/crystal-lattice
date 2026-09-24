# Agent Evaluation Documentation

## What this library is for

Agent evaluation tests whether an agent behaves as intended when it receives
instructions, configuration, tools, repository context, and follow-up
messages.

This differs from an ordinary unit test. A model-driven operation may involve:

- an expensive repository investigation;
- several conversational turns;
- tool calls and workspace changes;
- nondeterministic or structured model output;
- deterministic assertions, AI-based assessment, and human review;
- enough runtime data that the complete log is difficult to inspect.

`agent_eval` provides the repeatable execution and observability around that
work. The test itself remains ordinary Python, normally run by pytest.

## How it works

```text
pytest test
    │
    ▼
AgentEval kernel
    ├── prepares a workspace
    ├── opens an environment
    ├── runs your Python callback
    ├── records evidence and artifacts
    └── captures a reusable snapshot
            │
            ▼
          Run[T]
    value, snapshot, observation,
    changed paths, errors, artifacts
```

The generic kernel does not know what an agent message or tool loop is. A
`RunEnvironment` supplies that execution model. The included
`CrystalLatticeEnvironment` opens a real `AgentApplication`, creates or
restores a session, and exposes a `CrystalLatticeContext` to the callback.

## Main concepts

| Concept | Meaning |
|---|---|
| Evaluation program | Your Python callback. It sends messages, runs requests, inspects files, invokes other models, and returns any value useful to the test. |
| Kernel | `AgentEval`. It owns the generic run, workspace, cache, continuation, artifact, and error lifecycle. |
| Environment | The execution-specific integration. It creates the context, restores and captures state, and summarizes what happened. |
| Context | The object given to the program. In Crystal Lattice it exposes the application, core, session, configuration, request helpers, workspace, and evidence services. |
| Run | The durable result of one invocation. It contains the program value, environment snapshot and observation, changed paths, error, and artifact location. |
| Snapshot | Environment-owned state that can initialize a later run. A Crystal Lattice snapshot contains the session and continuation-related configuration. |
| Continuation | A new run that starts from a parent snapshot. The new program still executes, usually in a fresh workspace. |
| Cache hit | Reuse of a previously completed equivalent run. Neither the environment nor the program executes again. |
| Evidence | A named fact or observation recorded while the run executes, such as a prompt, response, request summary, tool event, changed file, score, or failure. |
| Projection | An explicit selection or transformation of evidence for one consumer, such as deterministic assertions, an assessment model, or a human reviewer. |
| Artifact | A file written for later inspection. Canonical artifacts summarize a run; raw artifacts retain detailed diagnostics; presentations are audience-specific artifacts. |

An evaluation does not need to use every concept. A simple test may only create
an environment, run one callback, and assert on `run.value`.

## Typical evaluation flow

1. Construct an environment from normal Crystal Lattice configuration.
2. Construct `AgentEval` with artifact and optional cache roots.
3. Write a program callback.
4. Start or restore an agent session inside the callback.
5. Send messages and requests.
6. Return the value that the test should inspect.
7. Assert with ordinary pytest.
8. Open `result.md` when the assertion or behavior needs review.
9. Use a snapshot or cache key only when reuse is valuable.
10. Create explicit evidence projections before giving material to another
    model or a human reviewer.

## Documentation map

Use these pages according to the work you are doing:

- [Quickstart](quickstart.md): run a first Crystal Lattice evaluation, inspect
  its result, understand the objects created by the example, and continue it.
- [Environments and customization](environments.md): understand the generic
  environment/context boundary, Crystal Lattice requests and outcomes, custom
  drivers, stopping, configuration, snapshots, evaluation, and presentation.
- [Continuation and cache](continuation-and-cache.md): understand the
  difference between snapshots, continuations, and cache hits, then reuse
  conversation and repository state safely.
- [Run model](run-model.md): understand the reusable layer above the
  kernel — request identity, run labels, samples, and the consolidation
  core — and how evaluation suites consume it.
- [Artifacts and evidence](artifacts-and-evidence.md): understand what evidence
  is, how it becomes canonical/raw artifacts or projections, and how to select
  compact AI and human review inputs.
- [Development](development/index.md): package architecture, tests, and
  maintenance boundaries.

The generic target specification lives under
`maintainer/agent-evaluation/docs/development/specifications/framework/`.
The Crystal Lattice environment has a separate package-local specification.
Optional support for durable completed-evaluation review packages is specified
separately under
`maintainer/agent-evaluation/docs/development/specifications/result-packages/`;
it is not part of the generic kernel contract.
These pages describe current implemented behavior; requirements record which
target parts are implemented and verified.