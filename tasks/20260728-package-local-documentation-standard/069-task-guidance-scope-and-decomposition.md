Parent Task: tasks/20260728-package-local-documentation-standard/000-main.md

Depends On:

- `tasks/20260728-package-local-documentation-standard/068-task-guidance-specification-alignment.md`

Related Existing Task:

- `tasks/20260721-task-guidance-evaluation-workflow.md`

Related Specifications:

- `maintainer/specifications/documentation-and-specification-standard/index.md`
- `maintainer/specifications/agent-evaluation-framework/index.md`

Requirement IDs:

- Existing ownership: `DOCFLOW-002`–`DOCFLOW-004`, `DOCVAL-001`
- Add stable scope/decomposition and verification IDs to the governing
  requirements ledger during execution after confirming the next available IDs
  against concurrent specification work.

# Task Guidance Scope and Decomposition

Refine task guidance so agents derive the minimum sufficient requirements,
choose one task by default, and create subtasks only as independently
reviewable working iterations or isolated responsibilities. Verify the behavior
through six baseline-first real-model scenarios on the migrated programmatic
agent-evaluation framework.

## Requirements checklist

- [ ] Task guidance requires the smallest set of independently verifiable
  outcomes and constraints that can deliver the user-approved scope.
- [ ] Task guidance does not promote implementation phases, evidence types,
  optional improvements, non-blocking risks, or possible future work into
  requirements unless their outcome is independently required.
- [ ] Useful non-required ideas remain explicitly optional or deferred, and
  material scope expansion requires user approval.
- [ ] Necessary blockers, safety constraints, compatibility constraints, and
  genuine dependencies remain visible when the approved outcome cannot be
  delivered without them.
- [ ] Task guidance uses one task by default and defines deterministic reasons
  for choosing a task directory.
- [ ] A valid implementation subtask is either a working iteration that leaves
  a usable, reviewable state or an isolated component, contract, decision, or
  migration responsibility that can be completed and verified separately.
- [ ] Every subtask identifies the parent requirements it advances, has clear
  slice-specific acceptance requirements, and declares only real blocking
  dependencies.
- [ ] Implementation, tests, documentation, evidence, and relevant
  verification stay with the slice they complete instead of becoming generic
  horizontal phase subtasks.
- [ ] Testing, documentation, research, review, migration, or deployment may
  remain independent tasks when that artifact or result is itself an approved,
  independently reviewable outcome.
- [ ] Three single-task and three task-directory behavioral scenarios exercise
  direct task creation, guidance-bearing planning followed by task creation,
  and planning an existing approved task.
- [ ] Scenario descriptions are natural prose that does not enumerate the
  expected requirements or prescribe the task decomposition.
- [ ] Expensive repository investigation can remain guidance-neutral, but
  TASKS guidance is present when the model first derives requirements and task
  boundaries during planning.
- [ ] Current-guidance baseline runs use the same repositories, commits,
  prompts, fixtures, assertions, model profiles, and reasoning effort later
  used for candidate comparisons.
- [ ] No guidance change is made until representative baseline evidence shows
  requirement inflation in a single-task case or poor decomposition in a
  task-directory case.
- [ ] Requirement counts, unmatched outcomes, task counts, subtask roles,
  requirement mappings, dependency graphs, planning responses, and final task
  files are preserved as concise canonical evidence.
- [ ] High/max reasoning profiles are represented, and reasoning effort is
  recorded in cache identity and artifacts.
- [ ] Candidate guidance starts with the shortest general wording and grows
  only when paired evidence shows that the concise form is insufficient.
- [ ] Canonical and bundled TASKS-v7 guidance remain mechanically synchronized.
- [ ] Deterministic assertions, structured semantic assessment, and human
  review remain distinct evidence sources.
- [ ] The completion handoff explicitly offers the recorded optional
  post-completion expansion areas without exploring, planning, or making them
  prerequisites of this task.

## Scope

This task owns two related behaviors:

1. deriving a proportionate requirement set from a natural-language request;
2. deciding whether that requirement set belongs in one task or a task
   directory with coherent subtasks.

It consumes the canonical guidance, synchronization mechanism, and migrated
task-guidance evaluator delivered by subtask 068. It does not reopen the
generic evaluation-kernel implementation or duplicate migration ownership.

## Supporting details

### Observed behavior

Models often turn a request with approximately three independently verifiable
outcomes into six or ten requirements by promoting:

- implementation phases;
- testing and documentation work;
- optional improvements;
- general risk concerns;
- operational possibilities;
- future follow-ups;
- broader refactoring or framework work.

The same completeness bias can create task directories whose children are
horizontal phases such as implementation, tests, documentation, review, or
deployment. These subtasks are not independently complete and frequently delay
the initial working delivery.

The behavior is especially visible with high, xhigh, or max reasoning effort.
The existing task-guidance evaluator currently uses medium effort for its
ChatGPT profile and max effort for GLM. The migrated suite must expose and
record the selected effort instead of treating model identity alone as the
profile.

### Current evaluation limitation

The existing evaluation deliberately disables TASKS guidance for its planning
seed and enables it only for the task-creation continuation. That is valid for
testing task-file handoff rules, but it cannot determine whether TASKS guidance
prevents planning from introducing unnecessary requirements or subtasks.

If a guidance-neutral plan expands the scope and the user then approves that
plan, preserving the expanded requirements in the task file may be reasonable.
The new planning scenarios must therefore apply the selected baseline or
candidate guidance before the model first derives requirements and task
boundaries.

### Proposed requirement rule to test

The shortest candidate should express this concept:

> Derive the smallest set of independently verifiable outcomes and constraints
> from the approved request. Do not multiply requirements by implementation
> stages, evidence types, optional improvements, non-blocking risks, or possible
> future work. Keep non-required ideas explicitly optional or deferred, and ask
> before promoting them into scope.

This is a candidate hypothesis, not approved output wording. It may be added
only after baseline evidence demonstrates the targeted failure.

The rule must not hide real blockers, safety constraints, compatibility needs,
or dependencies required to deliver the approved outcome.

### Proposed decomposition rule to test

The shortest candidate should express these concepts:

- use one task by default;
- split only when approved requirements form independently reviewable slices;
- a slice is either a working iteration or an isolated responsibility;
- each subtask owns the implementation, focused tests, current documentation,
  evidence, and verification needed for that slice;
- avoid implementation/test/documentation/review/deployment phase subtasks
  unless that phase is itself an independently required deliverable;
- keep one task when every proposed part must land before any requirement is
  satisfied.

Possible concise wording:

> Use one task by default. Split only when the approved requirements form
> independently reviewable slices: an iteration that leaves a working solution,
> or an isolated component, contract, decision, or migration boundary with
> clear acceptance. Each subtask identifies the parent requirements it advances
> and owns the implementation, tests, documentation, and evidence needed for
> its slice. If all parts must land together before any requirement is
> satisfied, keep one task.

This also remains a candidate hypothesis until baseline behavior justifies a
guidance change.

### Decomposition rules

#### Working iteration

A working-iteration subtask:

- starts from a working state;
- adds a specific capability or requirement group;
- includes the verification and documentation needed for that addition;
- leaves another usable and reviewable state;
- allows a later subtask to extend rather than complete unfinished basics.

#### Isolated responsibility

An isolated-responsibility subtask:

- owns one package, component, contract, decision, migration boundary, or other
  separately reviewable result;
- can be implemented and verified without relying on unfinished sibling work,
  except for declared dependencies;
- links the parent requirements it advances;
- does not duplicate a shared contract in several children.

#### Dependency rules

- A dependency records a real implementation or verification blocker.
- Siblings that consume the same completed contract may run in parallel.
- Numbering does not itself create dependency.
- A final integration subtask is justified only when integrated behavior is a
  distinct requirement not already owned by another slice.
- If every child touches the same concern and none is useful or reviewable
  independently, use one task.

#### Parent and child requirements

The main task owns the overall completion contract. A subtask states the
parent requirement IDs it advances and the acceptance outcomes of its isolated
slice. It must not silently add a new parent-level outcome.

Raw checkbox totals across parent and child files are not sufficient evidence
because a child may legitimately refine a parent requirement. Evaluation
should record both:

- parent requirement count;
- semantic count of unique completion outcomes and unmatched child outcomes.

## Scenario matrix

The completing agent may select suitable public repository commits and issues.
Each selected case must be narrow enough for an inexpensive model to
investigate quickly. If an issue already enumerates requirements or proposes
subtasks, rewrite the scenario prompt as natural prose while preserving the
same derivable outcomes.

### Single-task scenarios

#### Single 1: cohesive bug fix, direct task creation

Candidate setup: the existing Codex MDM home-relative-path behavior rewritten
as prose.

Expected derivable outcomes:

1. MDM-delivered home-relative paths resolve against the current user home.
2. Equivalent home-relative MDM and filesystem inputs normalize equivalently.
3. Existing absolute, ordinary-relative, glob, and malformed-input behavior
   remains unchanged.

Expected task shape:

- one task file;
- three parent requirements;
- no subtasks;
- implementation, regression tests, and affected documentation remain plan
  work rather than additional product requirements.

This scenario isolates direct task-authoring behavior without a prior plan.

#### Single 2: bounded feature, planning then task creation

Candidate setup: one small CLI, SDK, or package feature with:

1. one new bounded behavior;
2. one observable result;
3. preservation of existing behavior when the new option is not used.

Expected task shape:

- the guidance-bearing plan contains only the necessary outcomes;
- one task file with three parent requirements;
- no generalized framework, telemetry, rollout program, or unrelated
  documentation project.

This scenario observes whether inflation first appears during planning or task
creation.

#### Single 3: existing approved requirements, add a plan

Setup:

- one prepared task with exactly three approved requirements;
- no execution plan;
- one cohesive package-local change.

Expected task shape:

- the three requirements remain byte-for-byte unchanged;
- only the named task file changes;
- no new task files or subtasks;
- implementation, tests, and documentation appear in the plan without
  becoming new requirements.

### Task-directory scenarios

#### Directory 1: isolated component boundaries, direct creation

Candidate setup: a shared contract with two independent consumers.

Expected parent outcomes:

1. define and verify the shared contract;
2. make the server conform;
3. make the client conform;
4. verify compatible integrated behavior.

Expected task shape:

```text
010: Define and verify the shared contract
020: Implement the server contract       # depends on 010
030: Implement the client contract       # depends on 010
```

Server and client do not depend on each other. Each subtask includes its own
implementation, focused tests, and applicable documentation.

#### Directory 2: incremental working solution, planning then creation

Candidate setup: a feature with a useful basic mode and a separately valuable
advanced extension.

Expected task shape:

```text
010: Deliver the basic working capability
020: Add the advanced behavior on top of the working baseline
```

The first subtask leaves a usable and tested solution. The second adds a
distinct capability rather than completing omitted tests, docs, or integration
for the first.

#### Directory 3: compatibility-preserving migration

Candidate setup: a persisted format, API, or configuration migration described
without enumerated requirements.

Expected task shape:

```text
010: Introduce the compatible new path while retaining old behavior
020: Migrate data, callers, or tooling using the compatible state
030: Retire or deprecate the old path after migration evidence
```

Each stage leaves a working state. Dependencies follow compatibility and
migration order rather than generic design/implementation/test phases.

## Evaluation topology

### Guidance-bearing planning

Reuse expensive factual investigation without reusing requirement or task
decisions across guidance variants:

```text
guidance-neutral factual investigation
    ├── pinned-baseline guidance planning
    │       └── pinned-baseline guidance task creation
    └── candidate guidance planning
            └── candidate guidance task creation
```

The selected guidance and reasoning effort participate in planning cache
identity. Candidate task creation never continues from a baseline-guidance
plan.

### Direct creation

Direct-creation scenarios branch from the same factual snapshot:

```text
guidance-neutral factual investigation
    ├── pinned-baseline direct task creation
    └── candidate direct task creation
```

### Existing task

Existing-task scenarios begin with the selected guidance present on the first
request. They do not need a guidance-neutral planning turn.

## Evidence and assertions

### Mechanical evidence

Record and assert where deterministic:

- expected and actual parent requirement count;
- expected requirement coverage;
- raw checkbox count;
- unique semantic outcome count supplied by structured assessment;
- unmatched added outcomes;
- task and subtask file count;
- parent links and requirement mappings;
- declared dependency graph and cycles;
- changed-path allowlist;
- obvious phase-only subtask names;
- exact prompt, guidance hash, model, reasoning effort, and parent snapshot;
- whether planning and task creation used the intended guidance;
- whether existing requirements remained byte-for-byte unchanged.

### Structured semantic assessment

The assessment input contains only the scenario contract, natural-language user
request, planning response, generated task files, dependency graph,
mechanical findings, and exact guidance identity.

Suggested result:

```json
{
  "required_outcomes": [],
  "optional_outcomes_presented_as_required": [],
  "unmatched_task_requirements": [],
  "proposed_task_count": 0,
  "horizontal_phase_tasks": [],
  "working_iterations": [],
  "isolated_slices": [],
  "unnecessary_dependencies": [],
  "scope_discipline_score": 0,
  "summary": ""
}
```

The reviewer judges task-guidance behavior only. It does not judge whether the
technical plan is optimal, whether every possible risk was found, or whether
future optional work would eventually be useful.

### Human review

Human review should answer:

- Were the derivable outcomes represented without multiplication?
- Did any requirement or task delay delivery without being necessary?
- Did expansion begin in planning or task creation?
- Does every subtask deliver a working iteration or isolated responsibility?
- Are tests and documentation attached to their owning slice?
- Do dependencies reflect real blockers?
- Did higher reasoning effort produce additional unapproved scope?

## Baseline-first approval gate

The six scenario contracts and assertions are completed before guidance edits.

Run the exact current post-068 guidance first. Require at least:

- one demonstrated requirement-inflation failure in a single-task scenario; or
- one demonstrated horizontal, excessive, or dependency-invalid decomposition
  in a task-directory scenario.

Prefer evidence for both before changing both guidance concepts. If only one
behavior fails, change only the wording governing that behavior.

If all representative baseline runs pass:

- do not change guidance;
- keep passing cases as robustness evidence;
- refine or replace a scenario without embedding the expected requirements or
  decomposition in the prompt;
- rerun the current guidance before proposing candidate wording.

Prompts, fixtures, assertions, model profiles, and reasoning effort stay
unchanged between a failing baseline and its candidate comparison.

## Reasoning-effort coverage

Initial discovery:

- GLM-5.2 at max effort: all six baseline scenarios;
- GPT at high or xhigh where supported: at least one single-task and two
  task-directory sentinels;
- one unchanged single-task and one task-directory scenario at medium and max
  on the same model to observe effort-related expansion.

Candidate runs reuse the exact failing model and effort profile. A full
model/effort cross-product is not required unless observed variance justifies
it.

## Optional post-completion expansion

Status: Not planned and not authorized by this execution plan.

After the core task is completed, the completing agent must explicitly offer
the following possible expansions to the user. It must not investigate them,
define detailed requirements, design scenarios, change guidance, or make them
conditions of core completion unless the user separately approves reopening or
extending the task.

### High-risk concerns absent from the request

Explore guidance and behavioral evaluation for situations where a user request
contains a clear high-risk defect or design, such as storing passwords in plain
text, even though the user did not explicitly ask for risk mitigation.

The later refinement should decide the desired boundary. A likely behavior is
to state the risk clearly and recommend a safe direction without silently
adding a broad remediation program to the task. Depending on the case, the
primary assertion may belong to the assistant response rather than the created
task file.

This possible expansion is not limited to security or privacy. It may cover
other high-impact safety, data-loss, legal, financial, compatibility, or
operational risks.

### Requirement verification semantics

Explore why models confuse:

- requirement verification;
- additional implementation verification;
- automated tests;
- manual verification.

The later refinement should clarify that requirement verification maps each
requirement or coherent group to acceptance evidence at a user-relevant or
public boundary. Most software requirements should normally have automated
test coverage where behavior is practically assertable, while some outcomes
require human verification. Additional implementation verification commonly
covers lower-level unit tests, internal invariants, robustness checks, or other
evidence that supports implementation quality without replacing requirement
acceptance.

The exact wording, exceptions, and scenarios are intentionally deferred.

### Proportional non-development task forms

Explore task shapes that do not require every development-plan element.
Potential examples include:

- documentation-only work that may not need a separate documentation section;
- research work that may not require product verification or documentation;
- narrowly scoped follow-up tests or reviews;
- other non-development or partial-development tasks.

The later work should determine which sections are required, optional, or not
applicable for each task type. No taxonomy or scenario matrix is selected in
this task.

## Execution plan

Status: Draft

### 1. Start from the migrated task-guidance suite

1. Wait for subtask 068 to establish the canonical TASKS-v7 source, bundled
   synchronization, migrated evaluator, commands, and fixtures.
2. Reassess the migrated public test helpers and scenario ownership without
   recreating the old specialized CLI beside the new framework.
3. Confirm the next available stable requirement IDs in the governing
   requirements ledger and add the approved scope/decomposition targets.

### 2. Specify six scenarios before changing guidance

1. Select or adapt pinned repository commits and narrow issue descriptions for
   the three single-task and three task-directory cases.
2. Rewrite prompts as natural prose when source issues already enumerate
   requirements or subtasks.
3. Record exact derivable parent outcomes, expected task shape, valid
   dependencies, mutation allowlists, and human-review questions.
4. Keep fixture facts sufficient for deterministic assertions without putting
   the expected answer in the user prompt.

### 3. Implement guidance-aware evaluation flow

1. Cache narrow factual investigation independently of guidance.
2. Create separate baseline/candidate planning branches with guidance present
   before requirement derivation.
3. Continue task creation only from the matching guidance-bearing plan.
4. Support direct-creation and existing-task variants.
5. Include guidance identity and reasoning effort in run/cache provenance.

### 4. Add objective and semantic evidence

1. Implement parent requirement-count, task-count, path, mapping, and
   dependency assertions.
2. Preserve planning and task-creation evidence separately.
3. Add a narrow structured assessment for unique outcomes, optional work,
   horizontal phases, working iterations, isolated slices, and unnecessary
   dependencies.
4. Add compact human-review presentation.

### 5. Run the current-guidance baseline

1. Run all six cases with GLM at max reasoning effort.
2. Run the focused GPT high/xhigh sentinel set.
3. Run selected same-model medium/max comparisons.
4. Classify failures as planning-stage expansion, task-creation expansion,
   requirement inflation, poor slice boundaries, or invalid dependencies.
5. Do not edit guidance until the applicable baseline failure gate is
   satisfied.

### 6. Test the shortest candidate

1. Add only the requirement-minimality wording supported by a demonstrated
   requirement-inflation failure.
2. Add only the decomposition wording supported by a demonstrated task-split
   failure.
3. Synchronize the canonical and bundled guidance through the mechanism owned
   by subtask 068.
4. Rerun the same failing model, effort, prompt, fixture, and assertions.
5. Try longer wording or examples only when the concise candidate remains
   insufficient.

### 7. Calibrate and hand off

1. Run deterministic package and parity tests.
2. Run the final supported-model matrix justified by observed variance.
3. Preserve canonical, raw, structured-assessment, and manual-review
   artifacts.
4. Update requirement evidence without marking human review complete
   automatically.
5. Summarize requirement counts, task shapes, effort effects, guidance changes,
   and remaining variance.
6. Complete the core task, then explicitly offer the three optional
   post-completion expansion areas without planning or starting them.

### Implementation decisions and open questions

- Approved: use a separate subtask 069 after the evaluator migration rather
  than expanding subtask 068 or modifying the in-progress subtask 015.
- Approved: use six core behavioral scenarios: three expected single-task
  outcomes and three expected task-directory outcomes.
- Approved: cover direct creation, guidance-bearing planning followed by task
  creation, and existing-task planning.
- Approved: reusable factual investigation may be guidance-neutral, but
  planning that derives requirements or task boundaries must receive the
  selected TASKS guidance.
- Approved: baseline failures are required before changing guidance.
- Approved: requirement count is the primary mechanical scope-expansion signal,
  supplemented by semantic unique-outcome and unmatched-outcome analysis.
- Approved: task-directory cases require working iterations or isolated
  responsibilities rather than horizontal phase subtasks.
- Approved: exact expected task/subtask counts are scenario-specific, not a
  universal preference for fewer files.
- Approved: GLM max and GPT high/xhigh profiles are used to expose the observed
  high-reasoning failure mode; comparisons preserve exact effort.
- Approved: optional high-risk behavior, verification semantics, and
  non-development task forms are post-completion offers only and receive no
  exploration or planning in this execution plan.
- Implementation decision: select exact repository commits/issues during
  execution using the scenario constraints above.
- Implementation decision: confirm stable requirement IDs after concurrent
  specification work settles; do not preempt IDs owned by another active fork.
- No open requirement question changes the core required outcome.

### Documentation

- Canonical TASKS-v7 guidance after evidence justifies a change
- Bundled TASKS-v7 copy through the synchronization mechanism from subtask 068
- Governing specification and requirements for scope/decomposition behavior
- Migrated task-guidance suite documentation
- Six scenario contracts with exact prompts, fixtures, assertions, profiles,
  and traceability
- Compact human-review instructions and artifact locations

No product-user documentation is required because this is repository
maintainer guidance and evaluation infrastructure.

### Task checklist

- [ ] Confirm subtask 068 migration and canonical guidance state.
- [ ] Confirm stable requirement IDs and update the governing target.
- [ ] Specify three single-task scenarios.
- [ ] Specify three task-directory scenarios.
- [ ] Implement guidance-bearing planning branches.
- [ ] Implement direct-creation and existing-task branches.
- [ ] Add requirement-count and unique-outcome evidence.
- [ ] Add task-tree, mapping, and dependency evidence.
- [ ] Add structured semantic assessment and human-review presentation.
- [ ] Run all six current-guidance GLM max baselines.
- [ ] Run GPT high/xhigh baseline sentinels.
- [ ] Run selected medium/max effort comparisons.
- [ ] Confirm a baseline failure before changing each guidance concept.
- [ ] Add the shortest evidence-backed requirement-minimality wording.
- [ ] Add the shortest evidence-backed decomposition wording.
- [ ] Synchronize canonical and bundled guidance.
- [ ] Rerun paired candidate cases without changing test pressure.
- [ ] Run deterministic tests and parity checks.
- [ ] Run the final justified model/effort matrix.
- [ ] Record requirement and task-count findings.
- [ ] Prepare final human-review artifacts.
- [ ] Update requirement evidence and completion notes.
- [ ] Explicitly offer the optional post-completion expansion areas.

### Requirement verification

| Requirement group | Acceptance evidence |
|---|---|
| Minimum sufficient requirements | Three single-task scenarios preserve the exact scenario-owned parent outcome count; structured assessment reports no unmatched required outcomes or optional work promoted to scope. |
| Proportionate task choice | Direct and planned cases create one task or a task directory according to the scenario contract rather than model preference for more files. |
| Subtask quality | Every child maps to parent requirements and is classified as a working iteration or isolated responsibility; no generic phase-only child owns implementation, tests, documentation, review, or deployment for another slice. |
| Dependencies | Declared dependency graphs are acyclic and match actual contract, component, compatibility, or iteration blockers; independent siblings remain parallel. |
| Planning-stage behavior | Compiled request and response evidence proves the selected TASKS guidance was present before requirements and task boundaries were proposed. |
| Baseline-first causality | Exact current-guidance artifacts demonstrate the targeted failure before candidate wording; paired runs preserve repository, prompt, fixture, assertions, model, and effort. |
| Reasoning effort | Artifacts record effort and selected medium/high/xhigh/max comparisons show whether expansion changes with effort without altering scenario pressure. |
| Guidance delivery | Canonical and bundled files match mechanically and contain only wording justified by paired evidence. |
| Evidence separation | Deterministic findings, structured model assessment, and human review remain separate; model assessment does not mark human verification complete. |
| Optional expansion boundary | Core completion contains no implementation, requirements, or scenario plan for the three deferred areas and explicitly offers them to the user for a separate approval decision. |

### Additional implementation verification

- Verify a candidate task-creation continuation never reuses a baseline-guidance
  planning snapshot.
- Verify guidance and reasoning-effort changes invalidate only the appropriate
  planning/continuation cache layers, not the reusable factual investigation.
- Verify task-directory assertions normalize renamed files without accepting
  additional unapproved subtasks.
- Verify semantic assessment receives no unrelated repository context or raw
  event stream.
- Verify existing retain-plan, omit-plan, and approved-task scenarios still
  pass after migration and guidance refinement.
- Report skipped provider/model cases as not run.