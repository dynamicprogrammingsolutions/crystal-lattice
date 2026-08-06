# Agent evaluation framework product specification

## Purpose

Maintainers need to verify that an agent understands and applies instructions,
prompts, tools, skills, configuration, and repository context. These
evaluations often require an expensive repository investigation followed by
many cheaper continuations with different inputs.

The repository already has a task-guidance evaluator that demonstrates
conversation reuse, clean fork workspaces, exact prompt provenance,
deterministic assertions, empirical review, and human-readable artifacts. Its
current implementation is specialized and exposes too much scenario-specific
machinery to be reused comfortably.

The target is a small Python library that makes Crystal Lattice programs easier
to exercise from tests without defining an evaluation DSL.

## Users

### Evaluation authors

Evaluation authors write ordinary Python and pytest tests. They need to:

- run arbitrary Crystal Lattice application logic;
- configure custom agents, providers, plugins, skills, and prompt behavior;
- perform one or several requests in a run;
- cache a costly investigation;
- fork many continuations from the same conversation;
- inspect responses, tool activity, errors, changed files, and custom return
  values;
- assert results with normal Python;
- ask another model for booleans, scores, rankings, or any structured result
  without adopting a framework-owned reviewer concept.

### Human and AI reviewers

Reviewers need a compact deterministic result containing the useful visible
interaction, primary outputs, tool counts, failures, and provenance. They
should not need to inspect multi-megabyte event streams or complete runtime
state during ordinary review.

Raw evidence remains available for diagnosis and reproduction.

### Framework maintainers

Framework maintainers need:

- a narrow public API;
- one justified strategy boundary between generic evaluation lifecycle and a
  concrete runtime;
- deterministic tests around caching, forking, artifact generation, and error
  handling;
- the freedom to improve internals without changing evaluation code;
- real consumers that demonstrate value without becoming framework semantics.

## Target experience

An evaluation author creates an `AgentEval`, supplies an arbitrary execution
callback, and receives a `Run`:

```python
run = evaluation.run(
    "mobile-specification-ownership",
    execute,
    continue_from=repository_investigation,
)
```

The callback receives a Crystal Lattice context. It may use convenience
methods or access the underlying `AgentApplication`, `AgentCore`, session, and
configuration directly.

The framework does not ask whether text is guidance, a system message, a user
message, a skill, or a reviewer prompt. That meaning belongs to the configured
application and test.

## Goals

- Provide a small programmatic library built on Crystal Lattice Core and
  Application.
- Use arbitrary Python execution callbacks rather than declarative scenarios.
- Make all evaluation-specific abstractions optional.
- Support fresh runs, cached runs, and clean continuations from previous runs.
- Preserve exact compatibility and provenance for reused conversation state.
- Support isolated repositories and arbitrary workspace factories.
- Return arbitrary Python values from an evaluation.
- Capture normalized observations and complete raw evidence.
- Produce compact artifacts suitable for human and AI review.
- Use pytest as the initial suite discovery, fixture, parametrization, and
  assertion framework.
- Verify the documentation-standard instructions as the first consumers.
- Preserve the existing task-guidance evaluator until its owning task adopts
  the library.

## Non-goals

- Defining a declarative YAML or TOML evaluation language.
- Defining `Case`, `Suite`, `Check`, `Reviewer`, `Score`, or `RunPolicy` as
  required public abstractions.
- Hardcoding prompt roles, instruction injection, guidance files, model
  selection, skills, tools, or provider options.
- Replacing Crystal Lattice configuration and plugins.
- Replacing pytest assertion semantics.
- Requiring every evaluation to return pass/fail.
- Treating model-based evaluation as deterministic proof or human approval.
- Building a general benchmark, leaderboard, dataset, or hosted evaluation
  service in the first version.
- Moving the existing task-guidance evaluator in this task.
- Running real-model suites as part of ordinary default package tests.

## Acceptance examples

### Cached repository investigation

A pytest session fixture investigates a pinned repository with a default
Codex or Claude configuration. The investigation is guidance-neutral, performs
no mutations, and is reused by several continuations.

### User-message instruction variation

A test concatenates candidate documentation rules with a task prompt inside a
user message. No framework input changes are required.

### Plugin or skill variation

A test constructs a Crystal Lattice configuration that injects the candidate
rules through a feature plugin or skill. The same evaluation API is used.

### Multi-turn interaction

One execution callback asks for a plan, sends a confirmation, and returns both
assistant responses. The framework snapshots the final conversation.

### Structured scoring

A second run asks a model for a JSON scorecard. The callback validates the JSON
into a test-owned type and returns that object. Pytest asserts score ranges.
The framework has no reviewer or scorecard abstraction.

### Documentation-standard verification

Tests fork a shared repository investigation and exercise package ownership,
package-specific refinements, specification target versus current state,
anti-duplication, discoverability, plugin documentation, package profiles, and
maintainer routing. Results map to `DOCGEN-*` and `DOCREP-*` requirements while
human verification remains separate.