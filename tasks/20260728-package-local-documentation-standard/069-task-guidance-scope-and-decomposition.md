Parent Task: tasks/20260728-package-local-documentation-standard/000-main.md

Depends On:

- `tasks/20260728-package-local-documentation-standard/068-task-guidance-specification-alignment.md`
- `tasks/20260728-package-local-documentation-standard/067-requirement-quality-model-effort-baseline.md`

Related Existing Task:

- `tasks/20260721-task-guidance-evaluation-workflow.md`

Related Requirement-Quality Baseline:

- `tasks/20260728-package-local-documentation-standard/067-requirement-quality-model-effort-baseline.md`

Related Specifications:

- `maintainer/specifications/documentation-and-specification-standard/index.md`
- `maintainer/specifications/agent-evaluation-framework/index.md`

Requirement IDs:

- Requirement/testing candidate: `DOCGUIDE-005`–`DOCGUIDE-006`,
  `DOCFLOW-002`–`DOCFLOW-004`, `DOCVAL-012`
- Root guidance integration: `DOCAGENT-001`, `DOCAGENT-003`–`DOCAGENT-004`,
  `DOCVAL-013`.
- Add stable decomposition IDs only after the six-case baseline confirms the
  exact independently required behavior.

# Task Guidance Scope and Decomposition

Refine task guidance so agents derive the minimum sufficient requirements,
choose one task by default, and create subtasks only as independently
reviewable working iterations or isolated responsibilities. First verify the
evidence-backed requirement and testing rewrite through the exact 21-cell
subtask 067 matrix, then verify decomposition through six baseline-first
real-model scenarios on the migrated programmatic agent-evaluation framework.

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
  a usable, reviewable, tested improvement or an isolated component, contract,
  decision, migration, or other responsibility that can be completed and
  verified separately. Task guidance uses a subtask rather than an internal
  stage when completing the iteration produces such a deliverable improvement;
  internal stages remain appropriate for partial implementation or
  execution/review checkpoints that cannot be accepted independently.
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
- [ ] The first candidate comparison reuses subtask 067's exact three
  projects, seven model/effort profiles, product targets, prompts, fixtures,
  requirement assertions, and testing-plan assertions without rerunning or
  reconstructing the current-guidance baseline.
- [ ] Candidate task prompts continue to request one Draft task file without
  mentioning a testing strategy; standing task guidance must elicit
  requirement verification.
- [ ] The candidate preserves complete product-outcome coverage, removes
  material unsupported public decisions and wrong-record requirements, and
  improves decisive testing evidence without introducing material duplication
  or combinatorial test expansion.
- [ ] Public API, persisted-data, compatibility, security, privacy, and
  user-visible ambiguities remain questions unless the request or approved task
  grants the relevant decision authority.
- [ ] Planning-only task creation leaves only authorized task-file changes and
  contains no premature implementation or completion notes.
- [ ] Canonical and bundled TASKS-v7 guidance remain mechanically synchronized.
- [ ] Deterministic assertions, structured semantic assessment, and human
  review remain distinct evidence sources.
- [ ] The completion handoff explicitly offers the recorded optional
  post-completion expansion areas without exploring, planning, or making them
  prerequisites of this task.
- [ ] The completed Core documentation migration and root-guidance follow-up
  branches are merged and reconciled before further requirement/testing
  calibration, preserving package-local Core routes, one concise root
  documentation policy, current v3 task guidance, and current commit
  authorization.
- [ ] Root `AGENTS.md` has a dedicated concise Requirements section containing
  the always-applicable minimum-outcome, traceability, grouping, public-choice,
  state, and evidence rules.
- [ ] Root `AGENTS.md` has a shorter, focused Testing section that foregrounds
  requirement evidence, the lowest reliable boundary, real crossings,
  non-decisive mocks, focused existing coverage, unresolved behavior, and
  implementation-coupling restraint.
- [ ] Package- or runtime-specific testing rules move to the nearest applicable
  package guidance when that preserves discoverability, while repository-wide
  test realism, gating, and successful-run rules remain in root guidance.
- [ ] Root-guidance evaluation separates requirements-only, testing-only, and
  combined candidates and exercises both normal always-loaded guidance and
  task-file work with `TASKS-v7` enabled.
- [ ] The incomplete destination-vocabulary branch is not merged into the
  public guidance; only independently useful wording outside its main policy is
  reconsidered after the integrated root guidance is established.

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

### Evidence from subtask 067

The committed September 14–15 baseline provides the current-guidance failure
gate required by this task:

- all 21 current-guidance task files cover the approved product outcomes;
- semantic expansion improves from 5 high/12 medium/4 low in the
  requirement-minimal specification baseline to 0 high/5 medium/11 low/5 none
  in the current task-file baseline;
- GPT improves from 5 high/7 medium to 4 none/7 low/1 medium;
- GLM improves less and all three Flask/Vue efforts silently choose public
  behavior for unsupported `read` values;
- FastAPI tasks often raise missing companion-parameter defaults as questions
  but several plans partly assume a recommended answer;
- 12 of 21 testing plans contain complete decisive evidence and 9 are partial;
- 20 of 21 plans include the important production crossing;
- no plan has material test duplication or combinatorial expansion;
- FastAPI plans commonly use a mocked boundary that cannot prove database
  ordering/count behavior, omit valid boundary cases, or rely on nonexistent
  CRUD regression tests;
- three genuine GLM task-guidance adherence failures remain: generated site
  files left by planning, a missing required closing section, and premature
  Implementation Notes.

The accepted interpretation and exact evidence are in:

- `tasks/20260728-package-local-documentation-standard/067-requirement-quality-model-effort-baseline.md`;
- `maintainer/specifications/documentation-and-specification-standard/agent-behavior-verification/20260915-requirement-task-testing-comparison.md`.

This evidence authorizes a candidate for requirement authority, proportional
grouping, verification boundaries, and planning cleanliness. It does not by
itself authorize decomposition wording; the six decomposition scenarios retain
their separate baseline-first gate.

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

Subtask 068 owns the exact concise `TASKS-v7` replacements. The key
requirement-scope candidate is:

> Derive the minimum approved outcomes and constraints needed for completion.
> Add a requirement only when it is traceable to the request, an explicitly
> preserved contract, a necessary consequence, an applicable approved policy,
> or an approved design or quality decision. Use one requirement per
> independently meaningful outcome; keep variants, operations, boundary values,
> and examples beneath it unless independent acceptance, deferral, ownership,
> evidence, or status tracking adds value.

The same replacement keeps implementation, testing, documentation,
refactoring, and verification work in the plan unless its resulting outcome is
independently required.

The rule must not hide real blockers, safety constraints, compatibility needs,
or dependencies required to deliver the approved outcome.

### Public decisions, verification, and planning cleanliness

The requirement/testing candidate also adds:

> Resolve local, reversible implementation choices without separate approval.
> Public APIs, persisted data, compatibility, security, privacy, and
> user-visible behavior are material rather than local choices; ask unless the
> user or approved task has authorized that class of decision.

> Planning may use safe diagnostics, but task creation must leave only the
> requested task-file changes. Remove generated output and restore other
> incidental workspace changes before handing off the plan.

> Requirement verification maps each requirement, or coherent requirement
> group, to the smallest reliable acceptance evidence at the user-relevant or
> public boundary containing the claimed behavior. A mocked or lower-level test
> is not sufficient when it bypasses that behavior. Use representative
> boundary and regression cases; do not plan tests for unresolved or
> unapproved behavior.

Additional implementation verification remains limited to lower-level tests,
internal invariants, or robustness checks covering a distinct material risk.
Routine checks remain supporting evidence.

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

> Use one task by default. Split when the approved requirements form
> independently reviewable slices: a working iteration that leaves a usable,
> tested improvement, or an isolated component, contract, decision, migration,
> or other responsibility with clear acceptance. Use a subtask rather than an
> internal stage when completing the iteration produces a deliverable
> improvement. Keep partial implementation and execution or review checkpoints
> inside one task. Each subtask identifies the parent requirements it advances
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
- is represented as a separate subtask rather than an internal stage when the
  completed iteration is an independently deliverable improvement;
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

## Decomposition baseline-first approval gate

Subtask 067 already satisfies the requirement/testing baseline gate. The six
decomposition scenario contracts and assertions are completed before adding or
changing decomposition wording.

Run the exact accepted requirement/testing candidate guidance first. Require at
least one demonstrated horizontal, excessive, or dependency-invalid
decomposition before changing the decomposition rule.

If all representative baseline runs pass:

- do not change guidance;
- keep passing cases as robustness evidence;
- refine or replace a scenario without embedding the expected requirements or
  decomposition in the prompt;
- rerun the accepted guidance before proposing decomposition wording.

Prompts, fixtures, assertions, model profiles, and reasoning effort stay
unchanged between a failing baseline and its candidate comparison.

## Reasoning-effort coverage

Requirement/testing candidate comparison:

- `glm-5.3-flash:cloud` at low, high, and max across all three subtask 067
  projects;
- `gpt-5.6-luna` through ChatGPT login at medium, high, xhigh, and max across
  the same projects.

Decomposition discovery:

- `glm-5.3-flash:cloud` at max across all six decomposition cases;
- GPT high/xhigh sentinels covering at least one single-task and two
  task-directory cases;
- medium/max comparisons only when needed to explain observed effort variance.

Every candidate run reuses the exact baseline model and effort profile.

## Optional post-completion expansion

Status: Not planned and not authorized by this execution plan.

After the core task is completed, the completing agent must explicitly offer
the following remaining possible expansions to the user. It must not investigate them,
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

Status: Approved

### 1. Consume the committed requirement/testing baseline

1. Use commit `73a2f4bf` and the frozen Dataset B records from subtask 067 as
   the current-guidance baseline.
2. Do not rerun the 21 current-guidance producer cells.
3. Preserve the exact three projects, task prompts, fixtures, product targets,
   seven producer model/effort profiles, calibrated semantic evaluator, and
   testing-plan assertions.
4. Treat the committed comparison as the requirement/testing failure gate.
5. Keep the six decomposition scenarios and their separate baseline gate
   unchanged until the requirement/testing candidate is reviewed.

### 2. Prepare the synchronized candidate guidance

1. Wait for subtask 068 to establish `agents/TASKS-v7.md` as the canonical
   source and provide deterministic bundled-copy synchronization.
2. Update the governing specification and requirements before changing either
   guide.
3. Apply the exact requirements and testing replacements from subtask 010.
4. Apply the five exact task-guidance replacements from subtask 068.
5. Regenerate the bundled `TASKS_v7.md` and verify exact parity.
6. Record the candidate documentation-guidance hash, task-guidance hash,
   effective compiled developer-message hash, and source commit.

### 3. Run the exact 21-cell candidate matrix

1. Run Eleventy, FastAPI, and Flask/Vue with
   `glm-5.3-flash:cloud` at low/high/max.
2. Run the same projects with `gpt-5.6-luna` through ChatGPT login at
   medium/high/xhigh/max.
3. Ask only for one task file with a Draft execution plan; do not mention a
   testing strategy or expected requirements.
4. Start each cell from a fresh equivalent fixture.
5. Apply the same structural, mutation, provenance, requirement, and
   testing-plan assertions as Dataset B.
6. Preserve every task file, response, changed path, compiled instruction,
   semantic result, parser repair, and provider error.

### 4. Compare requirement and testing behavior

1. Require complete target coverage in every candidate.
2. Identify material unsupported public behavior, unresolved choices made
   operative, implementation constraints, wrong-record requirements, and
   disproportionate grouping.
3. Confirm the GLM Flask/Vue candidates raise unsupported `read` behavior as a
   question rather than silently selecting it.
4. Confirm FastAPI missing companion-parameter behavior remains a question
   until approved and is not assumed by implementation or tests.
5. Confirm no candidate promotes documentation, testing, verification, or task
   mutation boundaries into product requirements.
6. Evaluate testing completeness, selected layer, important crossing,
   duplication, combinatorial expansion, implementation coupling, and
   verification focus from the same task output.
7. Specifically check:
   - Eleventy: all seven plans include complete build/output evidence;
   - FastAPI: plans include valid boundary cases and evidence at the
     ordering/count boundary or record the unavailable integration as a gap;
   - Flask/Vue: all plans commit to a real client-to-Flask crossing;
   - no plan tests unresolved or unapproved behavior.
8. Recompute task structure with the corrected exact-heading parser and require
   task-only planning to leave no generated output.

### 5. Adjust only demonstrated candidate failures

1. If a candidate fails semantically, map the failure to one exact replacement
   block before changing wording.
2. Prefer reducing ambiguity or improving placement over adding examples.
3. Rerun only the failed exact model/effort cells while calibrating wording.
4. After a wording change passes focused cells, rerun the affected three-project
   matrix slice; run the full 21 cells only when more than one general rule
   changes.
5. Do not weaken product targets, testing expectations, or evaluator
   classifications to make candidate guidance pass.
6. Present the paired current/candidate comparison for human review before
   accepting the requirement/testing rewrite.

### 6. Reconcile completed documentation branches

1. Merge `task/20260728-core-python-documentation-migration` first so the
   package-local Core files and canonical routes exist before root guidance is
   rewritten.
2. Resolve its overlapping root guidance manually:
   - take the Core package docs, `core/python/AGENTS.md`, README/index routes,
     examples destination, and generated-reference ownership;
   - retain current commit authorization, v3 requirement/testing principles,
     the two current development-guide routes, and the package-neutral
     documentation design;
   - reject the older long documentation policy, `unit first` testing rule,
     retired standards/repository routes, generic umbrella-word prohibition,
     and duplicated documentation-update section.
3. Merge `task/20260914-guidance-follow-up-rewrites` second.
4. Take its one-hub repository map, one root documentation policy, removal of
   duplicated site commands and documentation triggers, full-read routing,
   long-running-work rules, heading cleanup, and deterministic protections.
5. Reconcile its old Core paths against the completed migration and preserve
   the current v3 guide and canonical/bundled task guidance.
6. Reconcile the substantial-specification paragraph using the follow-up
   report's stronger direct-request distinction rather than treating its
   initially ineffective candidate as verified.
7. Merge requirement ledgers, parent/subtask status, and evaluator support by
   meaning; do not choose one branch's whole overlapping file.
8. Keep `task/20260914-destination-vocabulary-guidance` unmerged. Preserve its
   existing committed and uncommitted work for later rebase.

### 7. Establish the integrated baseline

1. Record the merged revision and hashes of root `AGENTS.md`,
   `docs/development/documentation.md`, canonical `TASKS-v7`, and the bundled
   task guidance.
2. Verify the root has:
   - one documentation routing/policy section;
   - current Core package routes;
   - no duplicate documentation command catalog or update-policy section;
   - no restored `unit first` default;
   - unchanged v3 requirements/testing documentation and task guidance.
3. Run the completed Core migration's focused quickstart, Core documentation,
   example-generator, link, preparation, and build checks.
4. Run the follow-up branch's deterministic root-structure checks and one
   integrated Test 27 with the merged guidance hash.
5. Run canonical/bundled task-guidance parity and compiled-message integration.
6. Freeze this state as the root-guidance behavioral baseline without
   overwriting the committed v3 documentation/TASKS records.

### 8. Test dedicated root Requirements and focused Testing guidance

1. Update the governing specification and add stable live requirements before
   editing root guidance.
2. Create a requirements-only candidate:
   - minimum approved completed-state outcomes and constraints;
   - traceability to request, preserved contract, necessary consequence, or
     approved policy/decision;
   - proportional grouping;
   - plan/supporting-detail ownership of implementation, tests, documentation,
     refactors, risks, and optional work;
   - unapproved public/persisted/compatibility/security/privacy/user-visible
     behavior remains a question, with recommendations non-normative;
   - separate implementation, verification, and documentation states with
     direct evidence and explicit human confirmation.
3. Create a testing-only candidate that replaces the current strategy section
   rather than appending to it:
   - map requirements to the smallest reliable evidence;
   - choose the lowest-cost boundary containing the failure;
   - require a real crossing when behavior depends on components interacting;
   - reject a mock that supplies or bypasses the claimed behavior as decisive;
   - use existing coverage only when it proves the behavior;
   - avoid unresolved behavior, unapproved contracts, brittle implementation
     assertions, duplicate layers, and unnecessary combinations;
   - separate acceptance evidence, robustness checks, and routine quality
     checks.
4. Audit the remaining root testing rules. Keep repository-wide test realism,
   gated-run, boundary-label, successful-exit, and shared-harness rules; move
   Core-, plugin-, and React-Native-specific rules to their nearest guidance
   only when the merged package guidance provides a discoverable home.
5. Create the combined candidate only after requirements-only and testing-only
   evidence is preserved.
6. Exercise two delivery modes:
   - root guidance without task guidance, using a planning request that does
     not create a task file;
   - root guidance plus `TASKS-v7`, using the existing task-file prompts.
7. Record the exact compiled instructions and prove which root and task
   guidance reached each producer.
8. Run the previous sensitive requirement/testing cells first. Run the full
   21-cell matrix only if the focused comparison improves without losing
   product coverage or task structure.
9. Keep `docs/development/documentation.md` and `TASKS-v7` fixed while
   calibrating root guidance so causality remains interpretable.
10. Preserve the four public-decision and two missing-crossing v3 failures as
    sentinels; do not add fixture-specific wording.
11. Present the integrated baseline and requirements-only, testing-only, and
    combined comparisons for human review before decomposition work.

### 9. Specify the six decomposition scenarios

1. After the requirement/testing candidate is accepted, select or adapt pinned
   repository commits for the three single-task and three task-directory cases
   already described in this task.
2. Keep natural prompts free of expected requirement counts and subtask shapes.
3. Record derivable parent outcomes, valid task shape, dependencies, mutation
   allowlists, and semantic review questions.
4. Reuse the migrated evaluator and exact accepted candidate guidance as the
   new decomposition baseline.

### 10. Implement decomposition evidence and run its baseline

1. Cache narrow factual investigation independently of guidance.
2. Support direct creation, guidance-bearing planning followed by task
   creation, and existing-task planning.
3. Record task trees, requirement mappings, unique semantic outcomes,
   horizontal phases, working iterations, isolated responsibilities, and
   dependency graphs.
4. Run all six cases with GLM max and the focused GPT high/xhigh sentinels.
5. Add medium/max comparisons only where observed variance justifies them.
6. Require a demonstrated decomposition failure before changing decomposition
   wording.

### 11. Test the shortest decomposition candidate and hand off

1. Add only the decomposition wording supported by the six-case baseline.
2. Synchronize canonical and bundled guidance through subtask 068's mechanism.
3. Rerun the exact failed cells and then the justified final sentinel matrix.
4. Run deterministic package, synchronization, cache, and parser tests.
5. Preserve concise canonical evidence and complete raw records separately.
6. Update requirements without marking human review complete automatically.
7. Summarize requirement/testing and decomposition evidence separately.
8. Complete the task, then offer only the remaining high-risk and
   non-development optional expansions without planning or starting them.

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
- Approved: subtask 067's committed 21-cell current-guidance matrix satisfies
  the baseline failure gate for requirement authority and testing evidence;
  decomposition wording retains a separate six-case baseline gate.
- Approved: requirement count is descriptive rather than a verdict. Structured
  target coverage, added obligations, grouping, wrong-record material, and
  review burden are the primary requirement-quality evidence.
- Approved: task-directory cases require working iterations or isolated
  responsibilities rather than horizontal phase subtasks.
- Approved: use a subtask rather than an internal stage when an iteration
  leaves a usable, tested, independently deliverable improvement; keep partial
  implementation and execution or review checkpoints inside one task.
- Approved: exact expected task/subtask counts are scenario-specific, not a
  universal preference for fewer files.
- Approved: the first candidate uses the exact full seven-profile matrix from
  subtask 067. Later decomposition coverage uses GLM max and GPT high/xhigh
  sentinels plus only variance-justified effort comparisons.
- Approved: the task-file prompt does not request a testing strategy. Standing
  task guidance must produce requirement verification.
- Approved: requirement-verification semantics are core scope after the
  September 15 user direction and Dataset B evidence; only high-risk behavior
  and non-development task forms remain optional post-completion offers.
- Approved September 17, 2026: reconcile the completed Core migration and
  root-guidance follow-up before further testing; merge Core first, then the
  follow-up branch, and resolve overlapping guidance semantically.
- Approved September 17, 2026: root `AGENTS.md` needs a dedicated Requirements
  section because it is always loaded, while `TASKS-v7` applies the same
  invariants specifically to task-file structure.
- Approved September 17, 2026: replace the current root testing strategy with a
  shorter focused section and route lower-priority package/runtime details to
  nearer guidance when possible.
- Approved September 17, 2026: isolate root-guidance effects through
  requirements-only, testing-only, and combined candidates in both root-only
  and root-plus-TASKS delivery modes.
- Approved September 17, 2026: do not merge the incomplete
  destination-vocabulary guidance. Reconsider only concise independent wording
  after the integrated root candidate is established.
- Proposed acceptance: candidate requirement behavior keeps all 21 outcomes
  complete, has no material unsupported public behavior or wrong-record
  requirements, and does not introduce high expansion.
- Proposed acceptance: candidate testing behavior has no material duplication
  or combinatorial expansion, includes every important crossing, and either
  supplies decisive evidence or records an honest gap at the required boundary.
- Proposed acceptance: task-only planning leaves one task-file mutation and no
  premature implementation/completion notes.
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
- Root `AGENTS.md`
- Core package README, `AGENTS.md`, and documentation routes from the completed
  migration
- Integrated root-guidance baseline and candidate comparison

No product-user documentation is required because this is repository
maintainer guidance and evaluation infrastructure.

### Task checklist

- [x] Confirm subtask 068 canonical guidance state; evaluator migration remains
  independently open in subtask 068.
- [x] Confirm stable requirement IDs and update the governing target.
- [x] Apply the exact subtask 010 requirements/testing replacements.
- [x] Apply and synchronize the exact subtask 068 task-guidance replacements.
- [x] Run the exact 21-cell paired candidate matrix for v1 and v2.
- [x] Run the three project-batched calibrated semantic/testing evaluations for
  v1 and v2.
- [x] Compare current and candidate requirement expansion.
- [x] Compare current and candidate testing completeness and layer choice.
- [ ] Verify public ambiguities remain questions and planning leaves a clean
  workspace.
- [x] Refine only failed wording and rerun the smallest affected slice.
- [x] Present the requirement/testing candidate comparison for human review.
- [x] Apply the approved selective v3 requirement/testing ablation.
- [x] Run and semantically assess the known-sensitive v3 cells.
- [x] Run the full 21-cell v3 producer matrix after the focused comparison
  improved.
- [x] Present the v3 comparison for final guidance acceptance.
- [x] Merge and reconcile the completed Core documentation migration.
- [x] Merge and reconcile the completed root-guidance follow-up.
- [x] Preserve the incomplete destination-vocabulary branch without merging
  its main guidance.
- [x] Run integrated Core migration and root-guidance baseline checks.
- [x] Record integrated guidance hashes and effective instruction provenance.
- [x] Add stable requirements for the root Requirements and Testing sections.
- [ ] Test the requirements-only root candidate.
- [ ] Test the testing-only root candidate.
- [ ] Test the combined root candidate.
- [ ] Exercise both root-only and root-plus-TASKS delivery modes.
- [ ] Present the root-guidance comparison for human review.
- [ ] Specify three single-task scenarios.
- [ ] Specify three task-directory scenarios.
- [ ] Implement guidance-bearing planning branches.
- [ ] Implement direct-creation and existing-task branches.
- [ ] Add semantic unique-outcome and unmatched-outcome evidence.
- [ ] Add task-tree, mapping, and dependency evidence.
- [ ] Add structured semantic assessment and human-review presentation.
- [ ] Run all six decomposition-baseline GLM max cases.
- [ ] Run GPT high/xhigh baseline sentinels.
- [ ] Run selected medium/max effort comparisons.
- [ ] Confirm a decomposition baseline failure before changing decomposition
  wording.
- [ ] Add the shortest evidence-backed decomposition wording.
- [ ] Synchronize canonical and bundled guidance.
- [ ] Rerun paired candidate cases without changing test pressure.
- [x] Run deterministic tests and parity checks for the requirement/testing
  candidate work.
- [ ] Run the final justified model/effort matrix.
- [x] Record requirement and task-count findings.
- [x] Prepare focused human-review results.
- [ ] Update requirement evidence and completion notes.
- [ ] Explicitly offer the optional post-completion expansion areas.

### Requirement verification

| Requirement group | Acceptance evidence |
|---|---|
| Minimum sufficient requirements | Three single-task scenarios preserve the exact scenario-owned parent outcome count; structured assessment reports no unmatched required outcomes or optional work promoted to scope. |
| Paired requirement candidate | The exact 21-cell current/candidate comparison preserves complete product coverage and reports no material unsupported public behavior, implementation constraint, wrong-record requirement, or high expansion introduced by the candidate. |
| Paired testing candidate | The same 21 task outputs provide complete or honestly deferred decisive evidence at the required boundary, retain every important crossing, and avoid material duplication, combinatorial expansion, unresolved-behavior tests, and implementation coupling. |
| Planning cleanliness | Corrected deterministic assertions show task-only planning leaves only the requested task file and has no premature implementation/completion notes. |
| Proportionate task choice | Direct and planned cases create one task or a task directory according to the scenario contract rather than model preference for more files. |
| Subtask quality | Every child maps to parent requirements and is classified as a working iteration or isolated responsibility; deliverable iterations use subtasks, partial implementation remains an internal stage, and no generic phase-only child owns implementation, tests, documentation, review, or deployment for another slice. |
| Dependencies | Declared dependency graphs are acyclic and match actual contract, component, compatibility, or iteration blockers; independent siblings remain parallel. |
| Planning-stage behavior | Compiled request and response evidence proves the selected TASKS guidance was present before requirements and task boundaries were proposed. |
| Baseline-first causality | Exact current-guidance artifacts demonstrate the targeted failure before candidate wording; paired runs preserve repository, prompt, fixture, assertions, model, and effort. |
| Reasoning effort | Artifacts record effort and selected medium/high/xhigh/max comparisons show whether expansion changes with effort without altering scenario pressure. |
| Guidance delivery | Canonical and bundled files match mechanically and contain only wording justified by paired evidence. |
| Evidence separation | Deterministic findings, structured model assessment, and human review remain separate; model assessment does not mark human verification complete. |
| Optional expansion boundary | Core completion contains no implementation, requirements, or scenario plan for the remaining deferred areas and explicitly offers them to the user for a separate approval decision. |
| Completed-branch reconciliation | The merged tree contains the package-local Core documentation and package guidance, one concise root documentation policy, current paths, current v3 guide/TASKS behavior, and no restored superseded root rules. |
| Root Requirements guidance | Root-only and root-plus-TASKS outputs retain complete approved outcomes, reduce normative public-choice mistakes, and avoid wrong-record or optional requirements relative to the integrated baseline. |
| Root Testing guidance | Root-only and root-plus-TASKS outputs improve decisive evidence and layer choice without reducing important crossings or adding material duplication, combinations, unresolved-behavior tests, or implementation coupling. |
| Guidance delivery isolation | Compiled-message evidence identifies the exact root and task guidance present in every baseline and candidate run, allowing requirements-only, testing-only, and combined effects to be compared. |

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

## Implementation Notes

- September 15, 2026: Consumed the committed current-guidance baseline at
  `73a2f4bf` without rerunning it. Candidate v1 ran the exact 21 producer cells
  and three semantic batches, then was frozen before refinement.
- September 15, 2026: Candidate v1 improved requirement restraint but produced
  only 18 complete requirement sets, 7 complete testing plans, and 18
  structurally valid task-only plans. One GLM-max producer twice failed to
  produce a task; two low-effort plans misordered final sections.
- September 15, 2026: Candidate v2 added only evidence-backed wording for
  preserving grouped conditions, unspecified input behavior, bounded planning
  inspection, exact final headings, test boundaries, actual existing coverage,
  and missing harnesses. Corrected one task parser false positive that treated
  an inline future-heading mention as a premature notes section.
- September 15, 2026: Candidate v2 produced 21/21 complete requirement sets and
  21/21 structurally valid task-only plans. Testing regressed to 5 complete and
  16 partial plans, with only 11 appropriate primary-layer assessments.
  Requirement expansion was 2 none, 14 low, and 5 medium, with no high
  expansion.
- September 15, 2026: The calibrated judge needed two previously supported
  missing-brace repairs, one retry after a 2,217-character truncated response,
  and a validator correction allowing optional empty coverage notes. No
  semantic content was repaired or replaced.
- September 15, 2026: Added
  `agent-behavior-verification/20260915-requirement-testing-candidate-results.md`
  with current/v1/v2 comparisons and a proposed shorter testing ablation.
  Human review is required before another wording candidate or the six
  decomposition scenarios begin.
- September 15, 2026: The user approved all four review decisions: retain v2
  task-creation structure, retain and refine the complete-coverage requirement
  direction, treat approval-gated recommendations as expansion only when they
  become normative, and run the shorter testing ablation before decomposition.
- September 15, 2026: Committed the approved current/v1/v2 checkpoint as
  `5dda344e`, then applied candidate v3. V3 retains all v2 task-structure rules,
  makes approval-gated recommendations non-normative, removes recurring
  accepted/rejected-boundary and missing-harness instructions, and keeps only
  mock-bypass and actual-existing-coverage testing refinements. The combined
  documentation/TASKS guidance hash is
  `5c81cf48b78b999d8754276ab6d8805ffb8b1fed48559ed6d465993eaf9c846e`.
- September 15, 2026: All ten sensitive v3 producers passed task-only
  structure and mutation checks. Against those same cells, v3 improved over v2
  from 1 to 3 complete testing plans, 3 to 5 appropriate primary layers, and
  one poor layer to none. Important crossings remained 8/10. Requirement
  expansion was 2 none, 5 low, and 3 medium; all ten requirement sets were
  complete. This satisfies the approved improvement gate for running the
  remaining eleven producer cells without changing guidance.
- September 15, 2026: The remaining eleven v3 producers also passed, completing
  a 21/21 structurally valid task-only matrix. Every record uses guidance-source
  hash `e774becd184a8154dacd50bfc82c05132b444937c3cb687a4b9ae599ba720bef`
  and leaves exactly one task-file mutation.
- September 15, 2026: Full v3 semantic evaluation reports 21/21 complete
  requirement sets with 7 none, 10 low, and 4 medium expansion assessments.
  Testing improves to 13 complete and 8 partial plans, with 16 appropriate and
  5 mixed primary layers, 19/21 important crossings, no poor layers, and
  21/21 focused or mixed-but-bounded verification. Frozen records and the
  final acceptance recommendation are in
  `agent-behavior-verification/20260915-requirement-testing-v3-results.md`.
  Final human acceptance remains pending; decomposition work has not started.
- September 17, 2026: The user approved reconciling the completed Core
  documentation migration and root-guidance follow-up before further
  calibration. The approved follow-up adds dedicated always-loaded Requirements
  guidance, replaces the root Testing strategy with a shorter boundary-focused
  section, isolates root-only from root-plus-TASKS behavior, and leaves the
  incomplete destination-vocabulary branch unmerged. No decomposition work
  begins until this integrated comparison is reviewed.
- September 17, 2026: Merged the completed Core migration as `8c26812e` and
  root-guidance follow-up as `9c30e16c`, resolving root guidance, requirements,
  and task-ledger overlaps by ownership. The incomplete vocabulary branch
  remains unmerged.
- September 17, 2026: The integrated baseline uses root `AGENTS.md` hash
  `a56c068e7ea8357f7ef7f045e5a36c15194dc8d271517434ef74dc2bb8b1c54f`,
  documentation-guide hash
  `0dc4d6265c13ad606d447bb9f9ee2387961dad6d4a6329d9ea8f52fa43ee0e35`,
  and matching canonical/bundled TASKS hash
  `191fc888e8bc987e0a76b631ab362386157ed58e04fa4e56140767f3b2ab1d6c`.
  Core, examples, generator determinism, 89 maintainer evaluator tests, 31
  root-guidance tests, 15 assembly tests, parity, compiled-message integration,
  links, preparation, build, and integrated Test 27 all pass. The dated
  baseline report records exact evidence and the Test 27 accuracy caveat.
- September 17, 2026: Added `DOCAGENT-003`, `DOCAGENT-004`, and `DOCVAL-013`
  before changing root guidance. `DOCAGENT-002` is left available to the
  incomplete destination-vocabulary workstream.
- September 17, 2026: Added deterministic synthesis for integrated baseline,
  Requirements-only, Testing-only, and combined root `AGENTS.md` candidates.
  Root-only mode injects only `AGENTS.md`; task mode injects `AGENTS.md` plus
  canonical `TASKS-v7`. The current documentation pages remain byte-fixed in
  the workspace without direct injection. One GLM-low FastAPI baseline smoke
  completed without mutation; semantic review found complete requirements with
  one minor testing-as-requirement row, partial testing, mixed layers, and
  internal CRUD-return-shape coupling.