# Crystal Lattice guidance integration technical specification

## Documentation routes

- `docs/development/documentation.md` is the reusable guide.
- `docs/development/crystal-lattice-documentation.md` maps package paths,
  plugin guidance, publication, migration, and repository exceptions.
- Package README and docs directories own package-facing material.
- `maintainer/docs/` owns cross-cutting maintainer concepts and interpreted
  evaluation results.

## Repository guidance

`maintainer/guidance/current/` owns portable sections. The Crystal Lattice
target adds package routes and maintainer entry points and compiles root
`AGENTS.md`. The source path, compilation hash, and runtime delivery are
recorded separately.

Canonical `agents/TASKS-v7.md` is synchronized byte-identically to the bundled
application copy. Its content is delivered through the task-enabled developer
message; it is not inferred from the filename.

## Requirements, testing, and task guidance

Portable root Requirements owns generic completed-state, traceability,
grouping, approval, and record-role behavior. Portable root Testing owns
generic evidence selection, layer, crossing, mock, proportionality, and
reporting behavior.

TASKS owns:

- task-file creation triggers and structure;
- approval and execution authorization;
- plan status and required task sections;
- specification/task relationships;
- retain-plan and omit-plan handoffs;
- task versus subtask decomposition;
- parent mappings and dependencies;
- implementation, evidence, completion, and follow-up state.

TASKS may contain short reinforcement that maps root rules into
`## Requirements checklist`, `### Requirement verification`, and optional
additional implementation verification. It does not need to duplicate the
complete generic rules when the target compiler and runtime preflight prove
that root Requirements and Testing are in the same effective instruction.

An optional detailed-page design keeps essential rules in the effective
instruction and uses workspace pages only for examples and extended
explanation. The compiler target owns concrete destination paths and ensures
both root and task guidance route consistently.

## Task-guidance baseline and placement

The package-owned task-guidance evaluation suite defines:

- [Stage B0 — Current-guidance baseline](../../../evaluations/task-guidance/test-plan.md#stage-b0--current-guidance-baseline);
- [Stage B1 — Task-mechanics candidate](../../../evaluations/task-guidance/test-plan.md#stage-b1--task-mechanics-candidate);
- concise TASKS reinforcement;
- generic centralization in root guidance;
- optional routed explanation pages.

All placement candidates use the same semantic rule set. Compilation hashes,
effective message/tool delivery, stage inputs, and run attempts participate in
evidence identity.

## Publication and generated output

`docs_site/packages.toml` registers package documentation. Preparation assembles
maintained sources into `docs_site/prepared/`; build output lives under
`docs_site/dist/`. Generated directories are never edited directly. Navigation,
triggers, and compatibility routes remain repository integration concerns.

## Maintainer boundary

Maintainer concepts and results live under `maintainer/docs/`. Package-owned
framework and compiler specifications live with their packages. Cross-cutting
documentation guidance and this integration specification live under
`maintainer/docs/development/specifications/`.

## Evaluation

The documentation-guidance suite is a consumer of the reusable evaluation
framework. Scenario prompts and targets are suite inputs; frozen JSON is suite
evidence; dated Markdown reports live under
`maintainer/docs/evaluations/documentation-guidance/`.

The task-guidance suite target lives under
`maintainer/agent-evaluation/suites/task_guidance/`. It owns staged task
handoff, plan continuation, decomposition, and efficiency evaluation. Its
legacy CLI, assertions, imported-session forks, review tooling, and fixtures
are package-owned; the staged current-guidance baseline and task-mechanics
candidate extensions remain with task 090.
