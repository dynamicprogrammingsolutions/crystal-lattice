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
`DOCGUIDE-005`–`DOCGUIDE-006`, `DOCFLOW-002`–`DOCFLOW-004`,
`DOCVAL-001`, `DOCVAL-012`

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
- [ ] Task guidance derives only necessary, traceable requirements, groups
  variants and examples proportionately, and keeps implementation, testing,
  documentation, and verification work in the plan unless its resulting
  outcome is independently required.
- [ ] Public APIs, persisted data, compatibility, security, privacy, and
  user-visible behavior are never treated as local reversible decisions without
  explicit authority.
- [ ] Planning may run safe diagnostics but leaves no generated or other
  unrequested workspace changes behind when the requested output is only a
  task file.
- [ ] Requirement verification identifies the smallest reliable evidence at
  the boundary containing the claimed behavior, while additional
  implementation verification remains limited to distinct material risks.
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

### Evidence-backed TASKS-v7 replacements

Subtask 067 established the current-guidance baseline before this wording is
applied. The candidate should replace existing sentences in place and avoid a
new long section.

#### Requirement definition

Replace the first requirement definition under `## Terms` with:

> A **requirement** is a necessary, approved completed-state outcome or
> constraint. Implementation, tests, documentation, and verification belong in
> the plan unless their outcome is independently required.

#### Requirement derivation and grouping

Replace the requirement-writing paragraph beginning `Start each task with a
title...` with:

> Start each task with a title, short description, and
> `## Requirements checklist`. Derive the minimum approved outcomes and
> constraints needed for completion. A requirement must trace to the request,
> an explicitly preserved contract, a necessary consequence, or an approved
> policy or decision. Group variants, operations, boundaries, and examples
> unless separate acceptance, ownership, or status adds value. Keep
> implementation, testing, documentation, refactoring, and verification work
> in the plan unless its outcome is independently required.

#### Public decisions versus local choices

Replace the second bullet under `### Questions and decisions` with:

> In a retained plan, collect material decisions and questions immediately
> before documentation and give unresolved decisions a recommendation and
> tradeoffs. Resolve local, reversible implementation choices. Public APIs,
> persisted data, compatibility, security, privacy, and user-visible behavior
> are material; ask unless the user or approved task authorized that decision.

#### Planning mutation boundary

Add this bullet under `### Status tracking`:

> Planning may run safe diagnostics, but task creation leaves only the
> requested task-file changes. Remove generated and incidental changes before
> handoff.

#### Requirement verification

Replace the paragraph beginning `Requirement verification maps...` under
`## Execution plans` with:

> Requirement verification maps each requirement or coherent group to the
> smallest reliable evidence at the user-relevant or public boundary containing
> the behavior. A mock is insufficient when it bypasses that behavior. Use
> representative boundaries and regressions; do not test unresolved or
> unapproved behavior. Additional implementation verification covers only
> distinct material risks. Routine quality checks are supporting evidence.

These replacements are intentionally short. General definitions, examples,
quality requirements, testing-level guidance, and `testing-strategy.md` remain
owned by `docs/development/documentation.md` and are not repeated in every
task-enabled developer message.

## Execution plan

Status: Approved

1. Compare canonical and bundled v7 files and the config paths that load them.
2. Confirm `agents/TASKS-v7.md` as the canonical authored/evaluated source
   unless packaging inspection demonstrates a material ownership problem.
3. Update the governing specification and requirements before changing the
   guide.
4. Apply the five evidence-backed replacements above together with the concise
   target-spec/requirements/task/current-doc relationship and
   contributor-guide routing.
5. Remove or avoid duplicated broad workflow text; keep the net recurring
   developer-message increase small.
6. Add `scripts/sync_tasks_v7.py` with update and `--check` modes, plus
   `application/python/tests/test_tasks_v7_sync.py` as an exact-byte parity
   test for the bundled copy.
7. Regenerate
   `application/python/agent_terminal_app/default_config/TASKS_v7.md` from the
   canonical file rather than editing both copies independently.
8. Move the task-guidance evaluation suite, fixtures, README, and
   task-specific review/assertion tooling into the `maintainer/`-owned
   agent-evaluation layout; adapt it to the generic kernel and Crystal Lattice
   environment where equivalent behavior is verified and update all commands,
   imports, and consumers.
9. Update deterministic fixtures/assertions for requirement grouping, public
   decision authority, planning cleanliness, verification boundaries, and
   premature notes.
10. Add or update concise-prompt evaluation cases without mentioning testing
    when standing task guidance should elicit it.
11. Run deterministic evaluation and exact-parity tests.
12. Hand the synchronized candidate to subtask 069 for the exact paired
    21-cell real-model comparison and later decomposition scenarios.
13. Document any intentionally deferred empirical evaluation.

### Implementation decisions and open questions

- Concise task guidance, routing to `CONTRIBUTING.md`, short-prompt support, and
  mechanical canonical/bundled synchronization are approved.
- `agents/TASKS-v7.md` is the recommended canonical source because it matches
  the developer-message guidance evaluated by subtask 067; approval of this
  plan approves that ownership unless packaging inspection finds a material
  blocker.
- Use both generation and an exact-byte parity test: generation provides the
  normal update path, while the test prevents drift when the command is not
  run.
- The synchronization command reads only `agents/TASKS-v7.md` and writes only
  `application/python/agent_terminal_app/default_config/TASKS_v7.md`; `--check`
  reports drift without modifying files.
- The five replacement blocks above are the complete candidate for this
  iteration. Do not add examples or longer explanations to `TASKS-v7` unless
  paired behavior evidence demonstrates a remaining semantic failure.
- Real-model evaluation is recommended because the guide affects model
  behavior, but hosted/provider-dependent execution must remain explicitly
  enabled and separately reported from deterministic acceptance.
- The generic kernel, Crystal Lattice environment, and
  documentation-standard first consumers are owned by subtask 015; this task
  owns task-guidance-specific adoption and migration.
- No requirement questions are open.

### Documentation

- Canonical `agents/TASKS-v7.md`
- Bundled `application/python/agent_terminal_app/default_config/TASKS_v7.md`
- `CONTRIBUTING.md` routing
- Task-guidance evaluation README/fixtures where behavior changes
- Maintainer-owned task-guidance evaluation code, fixtures, and documentation
- Any synchronization command documentation
- `scripts/sync_tasks_v7.py`
- `application/python/tests/test_tasks_v7_sync.py`

### Task checklist

- [x] Confirm canonical v7 source.
- [x] Update governing specification and requirements.
- [x] Apply the five evidence-backed concise replacements and focused v2
  refinements.
- [ ] Add specification/task relationship guidance.
- [ ] Add concise contributor-workflow routing.
- [x] Add canonical/bundled synchronization or parity enforcement.
- [x] Add the update/`--check` synchronization command.
- [x] Add the application-package exact-byte parity test.
- [x] Generate the bundled guidance from the canonical source.
- [ ] Move task-guidance evaluation infrastructure under `maintainer/`.
- [x] Update deterministic evaluation fixtures/assertions.
- [x] Add concise-prompt evaluation coverage.
- [x] Add planning-cleanliness and public-decision deterministic coverage.
- [x] Run deterministic tests.
- [x] Hand off the exact candidate hash to subtask 069.
- [x] Run or explicitly defer any real-model review not covered by subtask 069.
- [x] Record human review of the current/v1/v2 evaluation comparison.

### Requirement verification

| Requirement group | Acceptance evidence |
|---|---|
| Canonical source and parity | A documented canonical path exists; automated check or sync command demonstrates canonical and bundled files match. |
| Specification/task semantics | Guidance inspection and deterministic fixtures show agents treat specs as targets, requirements as live tracking, tasks as approval/execution records, preserve IDs, and avoid duplicate/conflicting contracts. |
| Requirement scope and decisions | Focused fixtures show requirements are necessary and traceable, variants remain grouped, and public-contract choices become questions rather than local decisions. |
| Verification planning | Concise prompts with no testing instruction still produce requirement verification at the correct boundary without tests for unresolved behavior or routine-check bloat. |
| Planning cleanliness | Task-only planning leaves one authorized task-file mutation and no generated output or premature implementation/completion notes. |
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

## Implementation Notes

- September 15, 2026: Established `agents/TASKS-v7.md` as the canonical
  authored/evaluated source. Added `scripts/sync_tasks_v7.py` with update and
  `--check` behavior, generated the application default-config copy, and added
  an exact-byte application-package parity test.
- September 15, 2026: Updated the production compiled-message integration to
  exercise the non-mutating inspection action for all configured default
  agents. The shared fixture was corrected to retain current mixins, persist
  sessions correctly, and use `claude-openrouter`; the focused test passes.
- September 15, 2026: Applied requirement, public-decision,
  planning-cleanliness, exact-heading, and verification wording through
  candidate v2. The task-specific real-model comparison is owned and recorded
  by subtask 069. Specification/task relationship text, contributor routing,
  the remaining root `test/task_guidance` migration, and human acceptance
  remain open.
- September 15, 2026: The user accepted the task-structure direction,
  requirement refinement direction, normative-only treatment of
  approval-gated recommendations, and shorter testing ablation. Final guidance
  acceptance remains pending the v3 comparison.
