Parent Task: tasks/20260728-package-local-documentation-standard/000-main.md

Depends On:

- `tasks/20260728-package-local-documentation-standard/010-documentation-standard-and-agent-guidance.md`
- `tasks/20260728-package-local-documentation-standard/015-agent-evaluation-framework.md`
- `tasks/20260728-package-local-documentation-standard/065-contributing-and-ai-assisted-development-workflow.md`

Related Existing Task:

- `tasks/20260721-task-guidance-evaluation-workflow.md`

Related Specification:

- `maintainer/specifications/agent-evaluation-framework/index.md`

Specification:
`maintainer/specifications/documentation-and-specification-standard/index.md`

Requirement IDs:
`DOCFLOW-002`–`DOCFLOW-004`, `DOCVAL-001`

# Task Guidance and Specification Alignment

Align `TASKS-v7` with the package-local specification and contributor workflow,
establish a canonical authored source, keep the bundled developer-message copy
synchronized, and evaluate the changed task guidance without embedding the
full contributor guide in every task-related developer message.

## Requirements checklist

- [ ] A canonical authored source for v7 task guidance is explicitly declared.
- [ ] The bundled `application/python/agent_terminal_app/default_config/TASKS_v7.md`
  copy matches the canonical guidance used for evaluation and repository
  maintenance.
- [ ] A mechanical synchronization or exact-parity check prevents future drift
  between canonical and bundled guidance.
- [ ] Task guidance explains how durable specifications, requirement IDs, task
  requirements, execution plans, verification evidence, and completion notes
  relate.
- [ ] Task guidance states that specifications describe the target while
  requirements track live implementation, verification, documentation, and
  evidence.
- [ ] When a durable specification exists, task files link to it, preserve its
  identifiers, and avoid conflicting requirement paraphrases or duplicated
  plan content.
- [ ] Task guidance makes task files the default approval record for
  specification/requirement changes and explains that specs need no mandatory
  approval status.
- [ ] Task guidance explains that target specifications and task plans must
  both be updated when material implementation discoveries change accepted
  design or scope.
- [ ] Task guidance distinguishes target specs from current public and
  implementation documentation, which must stay consistent with committed
  code.
- [ ] The guide remains concise because it is appended to developer messages
  whenever task-file guidance is active.
- [ ] The guide points agents to root `CONTRIBUTING.md` for the broader
  AI-assisted workflow instead of repeating it.
- [ ] Standing task rules remain in the developer-message guidance so normal
  user prompts can be short and stage-specific.
- [ ] Task-guidance evaluation fixtures and deterministic assertions are
  updated for changed semantics.
- [ ] Evaluation scenarios exercise concise prompts that rely on the injected
  guidance rather than restating task rules.
- [ ] Task-guidance evaluation code, fixtures, documentation, and review
  tooling move from root `test/` locations into a coherent
  `maintainer/`-owned layout, with commands, imports, and consumers updated.
- [ ] Human review remains part of interpreting real-model evaluation
  artifacts; an AI-produced review is not the sole acceptance evidence.

## Supporting details

### Current source divergence

At task refinement on July 28, 2026:

- `agents/TASKS-v7.md` contained the most recent task-guidance refinements.
- `application/python/agent_terminal_app/default_config/TASKS_v7.md` differed
  from it.
- The default application config loaded the bundled file through
  `${file:${env:CONFIG_DIR}/TASKS_v7.md}` for multiple agent templates.

Updating only the repository guide would therefore not update the actual
developer-message guidance used by the default runtime.

### Recommended source-of-truth direction

Prefer:

```text
agents/TASKS-v7.md
```

as the canonical authored/evaluated source, with the bundled default-config
file copied or verified mechanically.

This recommendation remains reviewable. If build/package ownership indicates a
better canonical location, the implementation may propose it, but changing the
declared ownership is a material decision that must be recorded.

### Guidance boundary

`TASKS-v7` should contain:

- task creation and completion triggers;
- required task structure and status semantics;
- requirement versus execution-task distinctions;
- requirement-question and design-decision handling;
- plan approval and authorization rules;
- task/specification linking and stable ID behavior;
- evidence and completion-note rules;
- concise routing to `CONTRIBUTING.md`.

It should not contain:

- the full six-step contributor workflow;
- all example prompts from `CONTRIBUTING.md`;
- broad package documentation structure;
- detailed human code-review checklists;
- repeated generic coding/testing rules already provided elsewhere.

### Specification/task relationship

When a durable specification exists:

- the specification is the durable target for product behavior and technical
  design;
- the requirements record tracks live implementation, verification,
  documentation, and evidence;
- the task links to the specification and records execution scope,
  approval, dependencies, plan, findings, and completion state;
- task requirements map to specification requirements rather than silently
  rewording them into a second contract;
- requirement evidence links tests, documentation, task files, and delivery
  references;
- implementation discoveries update the task plan and target specification
  when they change accepted behavior or design;
- requirement changes still require approval.

Small changes without durable specifications continue to use task-local
requirements as the completed-state contract.

Task guidance should keep the workflow simple:

- update a specification before implementation;
- normally commit a simple spec change with the code or in the immediately
  preceding commit;
- create a new spec and requirements before implementing a new capability;
- use separate target versions only when a major multi-commit change would be
  clearer that way;
- use temporary progress tracking only when work spans multiple commits, link
  it to the task/requirements, and remove it after verification.

Public user documentation and implementation/maintainer documentation describe
current behavior and are committed with the code that makes new claims true.

### Existing evaluation workflow

Use the completed specialized infrastructure documented in:

- `tasks/20260721-task-guidance-evaluation-workflow.md`
- `test/task_guidance/README.md`
- `test/task_guidance/task_guidance_eval.py`
- `test/task_guidance/prepare_review_bundle.py`

The evaluation separates:

- real-model execution;
- deterministic assertions;
- empirical AI review;
- human-readable review bundles;
- human interpretation.

The update should preserve that separation while adopting the programmatic
framework from subtask 015 for generic runtime, continuation, cache, workspace,
and artifact behavior where it provides equivalent coverage.

## Execution plan

Status: Draft

1. Compare canonical and bundled v7 files and the config paths that load them.
2. Confirm or refine the canonical-source decision.
3. Add the concise target-spec/requirements/task/current-doc relationship and
   contributor-guide routing to the canonical guidance.
4. Remove or avoid duplicated broad workflow text.
5. Add a synchronization command, packaging step, or exact-equality test for
   the bundled copy.
6. Update the bundled file from the canonical source.
7. Move the task-guidance evaluation suite, fixtures, README, and
   task-specific review/assertion tooling into the `maintainer/`-owned
   agent-evaluation layout; adapt it to the shared library where equivalent
   behavior is verified and update all commands, imports, and consumers.
8. Update deterministic fixtures/assertions for the changed guidance.
9. Add or update concise-prompt evaluation cases.
10. Run deterministic evaluation tests.
11. Run a representative real-model evaluation when practical and explicitly
    enabled, then prepare artifacts for human inspection.
12. Document any intentionally deferred empirical evaluation.

### Implementation decisions and open questions

- Concise task guidance, routing to `CONTRIBUTING.md`, short-prompt support, and
  mechanical canonical/bundled synchronization are approved.
- `agents/TASKS-v7.md` is the recommended canonical source, subject to
  confirming packaging ownership during implementation.
- Exact-copy generation versus an equality-enforcing test is a reversible
  implementation choice if both make drift detectable before release.
- Real-model evaluation is recommended because the guide affects model
  behavior, but hosted/provider-dependent execution must remain explicitly
  enabled and separately reported from deterministic acceptance.
- The shared library contract and documentation-standard first consumers are
  owned by subtask 015; this task owns task-guidance-specific adoption and
  migration.
- No requirement questions are open.

### Documentation

- Canonical `agents/TASKS-v7.md`
- Bundled `application/python/agent_terminal_app/default_config/TASKS_v7.md`
- `CONTRIBUTING.md` routing
- Task-guidance evaluation README/fixtures where behavior changes
- Maintainer-owned task-guidance evaluation code, fixtures, and documentation
- Any synchronization command documentation

### Task checklist

- [ ] Confirm canonical v7 source.
- [ ] Add specification/task relationship guidance.
- [ ] Add concise contributor-workflow routing.
- [ ] Add canonical/bundled synchronization or parity enforcement.
- [ ] Update bundled guidance.
- [ ] Move task-guidance evaluation infrastructure under `maintainer/`.
- [ ] Update deterministic evaluation fixtures/assertions.
- [ ] Add concise-prompt evaluation coverage.
- [ ] Run deterministic tests.
- [ ] Run or explicitly defer representative real-model review.
- [ ] Record human review of evaluation artifacts.

### Requirement verification

| Requirement group | Acceptance evidence |
|---|---|
| Canonical source and parity | A documented canonical path exists; automated check or sync command demonstrates canonical and bundled files match. |
| Specification/task semantics | Guidance inspection and deterministic fixtures show agents treat specs as targets, requirements as live tracking, tasks as approval/execution records, preserve IDs, and avoid duplicate/conflicting contracts. |
| Concision | Diff and rendered developer-message inspection confirm the guide routes to `CONTRIBUTING.md` instead of embedding the six-step workflow and prompt library. |
| Short prompts | Evaluation cases use concise stage-specific prompts while the compiled developer message contains the standing task guidance. |
| Maintainer ownership | Task-guidance evaluation code, fixtures, documentation, imports, and commands operate from the approved `maintainer/` layout; old root test locations are removed or intentionally covered by compatibility behavior. |
| Evaluation | Deterministic evaluation tests pass; any real-model run is recorded with exact guidance hash and human-readable artifacts, or is explicitly reported as not run. |
| Human responsibility | Evaluation and guide text do not treat empirical AI review as final acceptance or manual verification. |

### Additional implementation verification

- Inspect compiled developer messages for at least one task-enabled agent.
- Compare canonical and bundled file hashes.
- Run task-guidance deterministic tests and artifact preparation.
- If a real-model evaluation is run, record provider/model, guidance hash,
  prompts, outputs, assertions, and human review status.
