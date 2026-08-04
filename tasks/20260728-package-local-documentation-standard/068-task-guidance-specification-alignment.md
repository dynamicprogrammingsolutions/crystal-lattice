Parent Task: tasks/20260728-package-local-documentation-standard/000-main.md

Depends On:

- `tasks/20260728-package-local-documentation-standard/010-documentation-standard-and-agent-guidance.md`
- `tasks/20260728-package-local-documentation-standard/065-contributing-and-ai-assisted-development-workflow.md`

Related Existing Task:

- `tasks/20260721-task-guidance-evaluation-workflow.md`

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
- [ ] When a durable specification exists, task files link to it, preserve its
  identifiers, and avoid conflicting requirement paraphrases or duplicated
  plan content.
- [ ] Task guidance explains that living specifications and task plans must
  both be updated when material implementation discoveries change accepted
  design or scope.
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

- the specification is the durable source for product behavior, technical
  design, and normalized requirement IDs;
- the task links to the specification and records execution scope,
  dependencies, plan, findings, and completion state;
- task requirements map to specification requirements rather than silently
  rewording them into a second contract;
- requirement evidence links tests, documentation, task files, and delivery
  references;
- implementation discoveries update the task plan and the living specification
  when they change accepted behavior or design;
- requirement changes still require approval.

Small changes without durable specifications continue to use task-local
requirements as the completed-state contract.

### Existing evaluation workflow

Use the completed infrastructure documented in:

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

The update should preserve that separation.

## Execution plan

Status: Draft

1. Compare canonical and bundled v7 files and the config paths that load them.
2. Confirm or refine the canonical-source decision.
3. Add the concise specification/task relationship and contributor-guide
   routing to the canonical guidance.
4. Remove or avoid duplicated broad workflow text.
5. Add a synchronization command, packaging step, or exact-equality test for
   the bundled copy.
6. Update the bundled file from the canonical source.
7. Update deterministic fixtures/assertions for the changed guidance.
8. Add or update concise-prompt evaluation cases.
9. Run deterministic evaluation tests.
10. Run a representative real-model evaluation when practical and explicitly
    enabled, then prepare artifacts for human inspection.
11. Document any intentionally deferred empirical evaluation.

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
- No requirement questions are open.

### Documentation

- Canonical `agents/TASKS-v7.md`
- Bundled `application/python/agent_terminal_app/default_config/TASKS_v7.md`
- `CONTRIBUTING.md` routing
- Task-guidance evaluation README/fixtures where behavior changes
- Any synchronization command documentation

### Task checklist

- [ ] Confirm canonical v7 source.
- [ ] Add specification/task relationship guidance.
- [ ] Add concise contributor-workflow routing.
- [ ] Add canonical/bundled synchronization or parity enforcement.
- [ ] Update bundled guidance.
- [ ] Update deterministic evaluation fixtures/assertions.
- [ ] Add concise-prompt evaluation coverage.
- [ ] Run deterministic tests.
- [ ] Run or explicitly defer representative real-model review.
- [ ] Record human review of evaluation artifacts.

### Requirement verification

| Requirement group | Acceptance evidence |
|---|---|
| Canonical source and parity | A documented canonical path exists; automated check or sync command demonstrates canonical and bundled files match. |
| Specification/task semantics | Guidance inspection and deterministic fixtures show agents link durable specs, preserve IDs, and avoid duplicate/conflicting contracts. |
| Concision | Diff and rendered developer-message inspection confirm the guide routes to `CONTRIBUTING.md` instead of embedding the six-step workflow and prompt library. |
| Short prompts | Evaluation cases use concise stage-specific prompts while the compiled developer message contains the standing task guidance. |
| Evaluation | Deterministic evaluation tests pass; any real-model run is recorded with exact guidance hash and human-readable artifacts, or is explicitly reported as not run. |
| Human responsibility | Evaluation and guide text do not treat empirical AI review as final acceptance or manual verification. |

### Additional implementation verification

- Inspect compiled developer messages for at least one task-enabled agent.
- Compare canonical and bundled file hashes.
- Run task-guidance deterministic tests and artifact preparation.
- If a real-model evaluation is run, record provider/model, guidance hash,
  prompts, outputs, assertions, and human review status.
