Parent Task: tasks/20260728-package-local-documentation-standard/000-main.md

Depends On:

- `tasks/20260728-package-local-documentation-standard/010-documentation-standard-and-agent-guidance.md`
- `tasks/20260728-package-local-documentation-standard/015-agent-evaluation-framework.md`
- `tasks/20260728-package-local-documentation-standard/016-root-agents-documentation-consolidation.md`
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

Align `TASKS-v7` with the package-local specification, establish a canonical
authored source, keep the bundled developer-message copy synchronized, and
evaluate the changed task guidance through a staged workflow that imitates how
humans use `CONTRIBUTING.md` without routing agents to or injecting that
human-facing guide.

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
- [ ] Task guidance distinguishes target specifications from published current
  user/developer documentation, preserves the branch-only `Not implemented`
  review option owned by the documentation guide, and prevents target-only text
  from being published as available behavior.
- [ ] The guide remains concise because it is appended to developer messages
  whenever task-file guidance is active.
- [ ] `TASKS-v7` is self-contained for task-file behavior and does not route
  agents to or require them to read human-facing `CONTRIBUTING.md`.
- [ ] Standing task rules remain in the developer-message guidance so normal
  user prompts can be short and stage-specific.
- [ ] Task-guidance evaluation fixtures and deterministic assertions are
  updated for changed semantics.
- [ ] A task-guidance test workflow is specified and approved before scenario
  implementation; it derives realistic prompts and stage boundaries from the
  human-led contributor workflow without using its human step numbers as the
  evaluator's structure.
- [ ] Each test-workflow stage is evaluated independently across the selected
  agent/profile cohort using the same fixed conversation prefix, workspace
  state, task/specification inputs, and current-stage prompt.
- [ ] Downstream stage tests use one reviewed canonical prior result rather
  than inheriting a different upstream result from each tested agent, so task
  creation, planning, implementation, and completion behavior remain
  comparable.
- [ ] Separate boundary tests cover both a fresh-agent handoff through durable
  task files and a same-agent continuation across adjacent workflow stages.
- [ ] Handoff evidence shows whether a task contains enough verified facts,
  decisions, unresolved questions, and pointers for a later agent to prepare a
  correct plan without repeating the first agent's broad investigation.
- [ ] Same-agent continuation evidence records whether the next stage reuses
  prior research and requires fewer scenario-defined investigation reads or
  tool calls than the initial research/task-creation stage.
- [ ] Evaluation scenarios use concise human prompts drawn from the workflow
  where appropriate and rely on injected task guidance rather than restating
  task-file rules.
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

Current inspection on September 14, 2026 confirms the divergence remains:

- `agents/TASKS-v7.md`: 1,273 words;
- bundled `application/python/agent_terminal_app/default_config/TASKS_v7.md`:
  1,453 words;
- the files have different SHA-256 hashes;
- the specialized evaluator remains under `test/task_guidance/`;
- no migrated `maintainer/agent-evaluation/suites/task_guidance/` suite exists.

The repository version already contains concise requirement-minimality rules.
Subtask 068 must preserve them, while subtask 069 separately owns
baseline-first requirement-scope and decomposition refinement.

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
- no dependency on human-facing contributor documentation.

It should not contain:

- the full seven-step contributor workflow;
- all example prompts from `CONTRIBUTING.md`;
- broad package documentation structure;
- detailed human code-review checklists;
- repeated generic coding/testing rules already provided elsewhere.

`CONTRIBUTING.md` is for humans. It is neither task guidance nor an agent
instruction dependency. Its relevance here is limited to test design: the
evaluator should imitate the prompts, approvals, and handoff boundaries a human
uses while directing task-based work.

### Staged evaluation workflow

The task must define and obtain approval for a test-owned workflow before
implementing scenarios. It should use descriptive evaluator stages rather than
the numbered human steps in `CONTRIBUTING.md`.

Recommended initial stages:

1. **Task handoff creation:** turn agreed scope and repository facts into a
   self-contained task or task directory.
2. **Execution-plan preparation:** load a fixed task handoff, inspect only what
   remains necessary, and write a Draft plan.
3. **Approved implementation:** continue from a fixed reviewed plan and
   explicit approval, implement the bounded change, and keep task state current.
4. **Evidence and completion update:** start from a fixed implemented state,
   reconcile requirements/evidence/completion notes, and report what remains.
5. **Follow-up planning:** start from a fixed review finding and plan it as new
   work without silently implementing or expanding the completed task.

The exact stages, prompts, and acceptance boundaries remain part of the test
workflow that this task must present for approval. The contributor guide may
supply the human prompts, but it is not loaded as model guidance.

#### Independent stage matrix

For the primary matrix:

- select a stable cohort of supported agents or model profiles;
- give every subject for one stage the same canonical conversation prefix,
  workspace snapshot, task/specification files, and current-stage prompt;
- score only the current stage;
- use one reviewed canonical prior result for the next stage rather than each
  subject's generated output;
- hash the prefix, workspace, task, prompt, model, reasoning effort, and
  guidance in cache identity and evidence.

For example, every plan-preparation subject receives the same task file. Every
implementation subject receives the same approved plan and a prefix that
already contains the request to load the task and prepare that plan. This
isolates whether the subject performs the current stage correctly.

The number of subjects is selected when the workflow is approved according to
available agents, cost, and variance. It is not fixed at seven merely because
seven human workflow steps exist.

#### Boundary continuity tests

Stage isolation does not prove handoff quality. Add separate bounded tests:

- **Fresh-agent handoff:** a task produced by one subject is given to a
  different fresh agent without the first conversation. Assert that the task
  preserves enough facts, decisions, questions, source pointers, and scope for
  a correct plan without broad rediscovery.
- **Same-agent continuation:** continue the actual task-creation session into
  plan preparation. Assert that prior investigation is reused and compare
  scenario-owned investigation reads/tool calls with the first stage.
- **Selected downstream boundary:** when justified by cost, continue a fixed
  approved plan into implementation or an implemented state into completion
  reporting to verify authority and status transitions.

Do not run a full cross-product in which every subject's variable output feeds
every later stage. A single reviewed linear reference flow supplies canonical
stage fixtures; independent stage matrices and focused boundary continuations
test the important behavior separately.

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

Published user and developer documentation describes available behavior.
Target-only user text may be reviewed on a development branch with the
documentation guide's visible `Not implemented` marker, but it is not
published as current behavior by default.

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

1. Complete subtask 016 so recurring root instructions are stable before
   task-guidance request evidence is captured.
2. Compare the canonical candidate, bundled copy, and every configuration path
   that loads task guidance.
3. Confirm `agents/TASKS-v7.md` as canonical or present a material alternative
   if packaging ownership disproves it.
4. Define the instruction-layer boundary:
   - documentation guide owns general document/specification/requirement
     meaning;
   - TASKS-v7 owns task-file mechanics and a concise task-specific form of
     cross-cutting rules;
   - `CONTRIBUTING.md` remains human-only and informs test prompts and
     boundaries without becoming agent guidance.
5. Add the concise specification/requirements/task/current-doc relationship
   to TASKS-v7; do not add a `CONTRIBUTING.md` route or copy the public guide or
   human workflow.
6. Add a deterministic sync command plus exact-parity test, then regenerate the
   bundled copy from the canonical file.
7. Move `test/task_guidance/` into a coherent
   `maintainer/agent-evaluation/suites/task_guidance/` layout using the generic
   evaluation kernel and Crystal Lattice environment; update commands, imports,
   docs, fixtures, and consumers without leaving a duplicate maintained suite.
8. Specify the test-owned staged workflow, exact human prompts, canonical
   prefixes/workspaces, agent/profile cohort, stage assertions, and boundary
   continuations; present that workflow for approval before model execution.
9. Implement independent stage matrices using fixed canonical prior results.
10. Implement fresh-agent and same-agent boundary tests with task completeness,
    repeated-investigation, tool-call, and plan-correctness evidence.
11. Update deterministic fixtures/assertions for target/live/task semantics,
    canonical provenance, parity, fixed-prefix isolation, and concise
    developer-message delivery without preempting subtask 069's
    requirement-count or decomposition matrix.
12. Run deterministic package, parity, migration, prefix, continuation, and
    compiled-instruction tests.
13. Run representative explicitly enabled
    `glm-5.3-flash:cloud` task-guidance comparison and preserve human-review
    inputs; use hosted sentinels only after separate authorization.
14. Update documentation, task state, and requirements while reporting any
    intentionally deferred empirical evaluation.

### Implementation decisions and open questions

- Concise self-contained task guidance, short-prompt support, and mechanical
  canonical/bundled synchronization are approved.
- `agents/TASKS-v7.md` is the recommended canonical source, subject to
  confirming packaging ownership during implementation.
- Recommendation: use a small sync command and an exact-equality test. The
  command makes maintenance easy; the test makes drift fail deterministically.
- Recommendation: treat the implemented `CONTRIBUTING.md` content as stable
  test-design input even though subtask 065 still awaits human readability
  closeout. It supplies realistic human prompts and boundaries only.
- Decided: `CONTRIBUTING.md` is not linked from TASKS-v7, injected into tested
  model instructions, or required reading for task work.
- Recommendation: use one reviewed five-stage reference workflow to produce
  canonical prefixes and workspace fixtures, then test each stage separately
  across a stable cohort.
- Recommendation: add selected fresh-agent and same-agent boundary tests rather
  than a full cross-product of variable upstream outputs.
- The exact cohort size, selected downstream boundary, and scenario-specific
  “less repeated investigation” threshold are material test-workflow decisions
  to present for approval before model execution.
- Real-model evaluation is recommended because the guide affects model
  behavior, but hosted/provider-dependent execution must remain explicitly
  enabled and separately reported from deterministic acceptance.
- The generic kernel, Crystal Lattice environment, and
  documentation-standard first consumers are owned by subtask 015; this task
  owns task-guidance-specific adoption and migration.
- Subtask 069 and the concurrent Test-22 work own requirement-minimality and
  task-decomposition refinement. This task preserves current wording and
  supplies the canonical/evaluation foundation without changing those rules.
- No requirement questions are open.

### Documentation

- Canonical `agents/TASKS-v7.md`
- Bundled `application/python/agent_terminal_app/default_config/TASKS_v7.md`
- Current `docs/development/documentation.md` and
  `docs/development/crystal-lattice-documentation.md` routes where needed
- A maintainer-owned staged task-guidance test-workflow specification with
  exact prompts, canonical prefixes, fixtures, stage assertions, and boundary
  scenarios
- Task-guidance evaluation README/fixtures where behavior changes
- Maintainer-owned task-guidance evaluation code, fixtures, and documentation
- Any synchronization command documentation

### Task checklist

- [ ] Confirm canonical v7 source.
- [ ] Confirm root AGENTS stabilization from subtask 016.
- [ ] Add specification/task relationship guidance.
- [ ] Confirm TASKS-v7 contains no `CONTRIBUTING.md` route or dependency.
- [ ] Add canonical/bundled synchronization or parity enforcement.
- [ ] Update bundled guidance.
- [ ] Move task-guidance evaluation infrastructure under `maintainer/`.
- [ ] Specify and obtain approval for the staged test workflow.
- [ ] Add fixed-prefix independent stage matrices.
- [ ] Add fresh-agent handoff and same-agent continuation tests.
- [ ] Update deterministic evaluation fixtures/assertions.
- [ ] Add concise human-prompt evaluation coverage without injecting
  `CONTRIBUTING.md`.
- [ ] Run deterministic tests.
- [ ] Run or explicitly defer representative real-model review.
- [ ] Record human review of evaluation artifacts.

### Requirement verification

| Requirement group | Acceptance evidence |
|---|---|
| Canonical source and parity | A documented canonical path exists; automated check or sync command demonstrates canonical and bundled files match. |
| Specification/task semantics | Guidance inspection and deterministic fixtures show agents treat specs as targets, requirements as live tracking, tasks as approval/execution records, preserve IDs, and avoid duplicate/conflicting contracts. |
| Concision and human-guide boundary | Diff and rendered developer-message inspection confirm TASKS-v7 is self-contained, contains no `CONTRIBUTING.md` route, and embeds neither the seven-step workflow nor its prompt library. |
| Independent stage behavior | Every subject for a stage receives the same hashed prefix, workspace state, canonical prior result, task/specification inputs, and current-stage prompt; assertions score only that stage. |
| Handoff quality | Fresh-agent planning from a generated task demonstrates sufficient durable context and bounded rediscovery; same-agent continuation demonstrates reuse of prior investigation with scenario-owned read/tool-call evidence. |
| Short prompts | Evaluation cases use concise prompts drawn from the human workflow where useful while the compiled developer message contains the standing task guidance and no contributor-guide content. |
| Maintainer ownership | Task-guidance evaluation code, fixtures, documentation, imports, and commands operate from the approved `maintainer/` layout; old root test locations are removed or intentionally covered by compatibility behavior. |
| Evaluation | Deterministic evaluation tests pass; any real-model run is recorded with exact guidance hash and human-readable artifacts, or is explicitly reported as not run. |
| Human responsibility | Evaluation and guide text do not treat empirical AI review as final acceptance or manual verification. |

### Additional implementation verification

- Inspect compiled developer messages for at least one task-enabled agent.
- Compare canonical and bundled file hashes.
- Verify `CONTRIBUTING.md` content is absent from task-guidance instructions.
- Verify fixed conversation prefixes and canonical workspace snapshots are
  byte-identical across subjects within each stage.
- Verify downstream stage matrices do not consume each subject's variable
  upstream output.
- Compare fresh-agent and same-agent investigation reads/tool calls against
  scenario-owned expectations without using raw count alone as correctness.
- Run task-guidance deterministic tests and artifact preparation.
- If a real-model evaluation is run, record provider/model, guidance hash,
  prompts, outputs, assertions, and human review status.
