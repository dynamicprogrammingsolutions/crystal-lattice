# Agent evaluation framework product specification

## Purpose

Provide a reusable Python kernel for executing evaluation programs, preparing
workspaces, caching compatible work, continuing from immutable state, recording
evidence, preserving errors, and returning durable results without hardcoding
one agent runtime or evaluation domain.

## Users

Evaluation authors write ordinary Python and pytest code. They need to run
arbitrary programs, select an environment, reuse expensive setup, isolate
workspaces, record evidence, and choose deterministic, model-based, or human
review appropriate to their suite.

Environment authors need one broad replacement seam for runtime-specific
context, compatibility, state restoration, snapshots, and final observation.
Reviewers need compact routine results with access to raw evidence for diagnosis
and reproduction.

## Target experience

The minimal operation is:

```python
run = evaluation.run("case-name", exercise)
run.raise_for_error()
```

The callback receives the context supplied by the selected `RunEnvironment` and
may return any Python value. The kernel owns lifecycle, workspace, cache,
parent linkage, evidence services, error preservation, and result storage. It
does not interpret prompts, message roles, tools, model scores, or domain
requirements.

A continuation restores a compatible parent snapshot into a clean workspace.
A cache hit reuses a completed equivalent run without opening the environment.
Both paths preserve provenance and leave the parent immutable.

## Goals

- Keep the generic kernel importable without Crystal Lattice dependencies.
- Use ordinary Python callbacks instead of a mandatory evaluation DSL.
- Make `RunEnvironment` the complete runtime replacement boundary.
- Support existing paths, workspace factories, and pinned Git workspaces.
- Preserve compatible continuation and explicit cache identity.
- Record canonical evidence separately from raw diagnostic data.
- Return arbitrary program values and structured failures.
- Let suites choose assertions, evaluators, presentation, and human review.
- Use pytest as an initial runner without making pytest part of the kernel API.

## Non-goals

- Defining universal prompt, message, agent, tool-loop, scoring, or reviewer
  abstractions.
- Assigning a framework-owned verdict to every run.
- Treating model assessment as deterministic proof or human approval.
- Embedding one consumer suite's scenarios, models, requirements, or guidance
  delivery semantics in the kernel.
- Building a hosted benchmark or leaderboard service.

## Acceptance examples

A replay environment can replace the complete runtime without importing
Crystal Lattice. A repository evaluation can cache a read-only investigation
and fork several clean child tasks. A failed program returns a structured run
with phase, error, workspace state, and raw evidence rather than losing its
result directory.
