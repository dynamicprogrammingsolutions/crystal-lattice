Parent Task: tasks/20260728-package-local-documentation-standard/000-main.md

Depends On:

- `tasks/20260728-package-local-documentation-standard/010-documentation-standard-and-agent-guidance.md`
- `tasks/20260728-package-local-documentation-standard/015-agent-evaluation-framework.md`

Related Tasks:

- `tasks/20260728-package-local-documentation-standard/068-task-guidance-specification-alignment.md`
- `tasks/20260728-package-local-documentation-standard/069-task-guidance-scope-and-decomposition.md`

Specification:
`maintainer/docs/development/specifications/crystal-lattice-guidance-integration/index.md`

Requirement IDs:
`DOCGUIDE-005`–`DOCGUIDE-006`, `DOCVAL-010`–`DOCVAL-011`,
`AEVAL-017`, `AEVAL-022`

# Requirement Quality Model-Effort Baseline

Establish a model/effort baseline for requirements produced across three
different small software projects: a public website, a public REST API with a
performance concern, and a full-stack web application. Interpret the initial
21-run minimal-guidance baseline directly, then use the accepted interpretation
to evaluate current documentation guidance, current task-file guidance, and
testing-plan scope before any guidance rewrite.

## Requirements checklist

- [x] Three compact pinned-project fixtures represent materially different task
  types: Eleventy website archive pagination, FastAPI public REST pagination,
  and Flask/Vue full-stack book filtering.
- [x] Each scenario has a natural task prompt and an evaluator-only semantic
  target identifying the minimum sufficient required outcomes,
  acceptable grouping, compatibility constraints, supporting details,
  optional adjacent work, and genuine unresolved questions without prescribing
  exact wording or implementation.
- [x] Scenario documentation explains the actual evaluated project's purpose,
  users, architecture, current behavior, pinned source revision, and relevant
  source files without requiring Crystal Lattice product context.
- [x] The three targets use the user-approved proposals as the starting
  baseline and are versioned and hashed before producer execution.
- [x] The producer matrix contains exactly three scenarios across seven
  profiles: `glm-5.3-flash:cloud` at low/high/max and `gpt-5.6-luna` through
  ChatGPT login at medium/high/xhigh/max.
- [x] Producer runs start from fresh equivalent fixtures, receive one
  requirement-minimal guidance variant, omit `TASKS-v7`, and differ only by
  scenario, model, and reasoning effort.
- [x] Requirement quality is not accepted through keyword, exact-row-count,
  exact-heading, exact-file-shape, or prohibited-token assertions.
- [x] Deterministic checks cover only run integrity, allowed mutations,
  expected output presence, exact prompt/guidance/fixture/model/effort
  provenance, and complete matrix coverage.
- [x] The implementing agent interprets all 21 outputs semantically against
  their targets and identifies completeness, missing behavior, optional scope
  promoted to requirements, implementation activity promoted to requirements,
  duplication, unsupported design choices, and model/effort expansion trends.
- [x] Human review receives a concise interpreted baseline organized first by
  cross-model findings and then by one compact row per run, with generated
  requirements and raw evidence available only as optional detail.
- [x] Existing Test 22 and its September 12 results remain unchanged as
  preliminary robustness evidence for translating already-classified scope.
- [x] The existing batch-enqueue, timeout, and report-output scenarios remain
  optional same-family controls and are cut or retained only after comparing
  their likely diagnostic value with the diverse baseline.
- [x] The user reviewed and accepted the initial baseline interpretation,
  including its distinction among valid decomposition, useful supporting
  detail, unsupported behavior, implementation constraints, and
  verification/documentation/task-scope material promoted to requirements.
- [x] The accepted semantic findings, online research basis, and exact proposed
  future requirement-writing guidance are preserved in this task so a later
  rewrite does not have to reconstruct them.
- [x] A structured semantic evaluator reproduces the accepted interpretation of
  the initial 21 runs closely enough to identify required-outcome coverage,
  valid grouping or decomposition, necessary derived behavior, approved design
  or quality decisions, unsupported public behavior, implementation
  constraints, role contamination, and human review burden.
- [x] A new 21-run task-file matrix uses the same scenarios, semantic targets,
  producer profiles, fixtures, and requirement-quality assertions while asking
  the agent to create one task file with a Draft execution plan and receiving
  the maintained current general documentation guidance plus the effective
  current task-file guidance in its developer message.
- [x] The task-file runs are also assessed for testing-plan quality without a
  separate producer matrix, including required-outcome coverage, appropriate
  test layer and public-boundary crossings, unnecessary duplication,
  implementation coupling, combinatorial inflation, and decisive verification
  focus.
- [x] The comparison report distinguishes the initial specification baseline
  from current-guidance task-file behavior and compares requirement expansion
  with testing-plan expansion by project, model, and effort without claiming
  that output format, documentation guidance, and task guidance were isolated
  independently.
- [x] No maintained documentation, task-file, or testing guidance is changed
  until the evaluator and current-guidance task-file matrix are complete, the
  useful comparisons are presented to the user, and a separate rewrite plan is
  approved.
- [x] Model-driven semantic assertions, repeated samples, candidate guidance,
  and paired candidate runs remained outside the initial baseline until its
  direct interpretation was reviewed and accepted.

## Scope

The completed initial phase measures requirement quality while writing
specifications for three different kinds of small software project. It does
not measure task-file decomposition and does not inject `TASKS-v7`.

The approved follow-up scope adds one producer dataset while retaining the
initial 21 records:

| Dataset | Output request | Guidance | Producer runs | Semantic assessment |
|---|---|---|---:|---|
| A: initial baseline | Specification and requirements | Requirement-minimal evaluation variant; no `TASKS-v7` | 21 complete | Requirements |
| B: current task-file | One task file with a Draft execution plan | Maintained current general documentation guidance plus the effective current `TASKS-v7` developer-message content | 21 planned | Requirements and testing plan from the same output |

Dataset B uses the same pinned fixtures, scenario descriptions, hidden targets,
model/effort profiles, and requirement-quality evaluator as Dataset A.
The task-file prompt changes only the requested record type and explicitly
requests one task file with a Draft plan so task shape is deterministic and no
format clarification blocks the run.

The testing-plan expansion does not add producer calls. Its assertions consume
Dataset B's execution plans.

The comparison intentionally measures behavior in the real current task-file
context rather than attributing every difference to one instruction layer. If
the results cannot distinguish an output-format effect from a guidance effect,
a separate current-documentation-only replay may be proposed after review; it
is not part of this Draft plan.

The 21 producer runs are:

| Producer | Efforts | Runs across three scenarios |
|---|---|---:|
| `glm-5.3-flash:cloud` | low, high, max | 9 |
| `gpt-5.6-luna` through ChatGPT login | medium, high, xhigh, max | 12 |
| Total | seven profiles | 21 |

Primary scenarios:

| Scenario | Pinned source | Task type |
|---|---|---|
| Eleventy Base Blog archive pagination | `11ty/eleventy-base-blog@26b26106d7fbb30b7b40d9ef52589d10ddbcb462` | Public static website, accessibility, URL continuity, and bounded archive output |
| FastAPI notes pagination | `testdrivenio/fastapi-crud-async@4fa7ae952ece61e228135285de1b6a5ff65a1dc8` | Public REST API extension motivated by large-response performance |
| Flask/Vue book filtering | `testdrivenio/flask-vue-crud@be91da59a10d07384537c2f76f4505eb344d1682` | User-facing full-stack behavior crossing Vue and Flask |

The fixtures retain only the source and project context needed to understand
each task, plus upstream attribution. Producing agents do not need network
access or the full upstream history.

Subtask 068 may proceed independently with canonical/bundled task-guidance
alignment. This subtask holds task shape fixed at one task file and measures
requirement and testing-plan quality as evidence. Subtask 069 owns changes to
the task-guidance requirement-minimality wording and the decision between one
task and a task directory; it must consume this evidence before adding
overlapping guidance.

## Supporting details

### Why existing Test 22 is insufficient

Test 22 is useful but strongly prepared:

- its task explicitly labels future ideas as unapproved;
- a guidance-neutral seed response first classifies approved and unapproved
  scope;
- the requirement-writing continuation inherits that classification;
- mechanical assertions require specific keywords, a Markdown requirements
  table, and four to seven rows;
- only GLM low, high, and max branches were compared;
- previous and rewritten guidance passed all three efforts.

It therefore shows that a model can translate already-classified scope. It
does not establish how models derive a minimum sufficient requirement set from
an ordinary small task.

The first three replacement scenarios also used closely related package/API
tasks. The user approved retaining them as optional controls but rejected them
as the primary matrix because they did not represent different project and task
types.

### Requirement-minimal guidance

The baseline uses an evaluation-only guidance snapshot derived from a pinned
repository revision. It retains:

- specification target versus current behavior;
- requirements as necessary outcomes and live state;
- package placement and generated-source boundaries.

It removes detailed requirement-writing rules, negative examples, the sample
requirements table, evidence-cell guidance, and explicit scope-restraint
language. The repository's maintained guidance is not edited to create this
variant.

### Semantic target

Each target is hidden from producing agents and records:

- required outcomes;
- compatibility constraints;
- acceptable grouping and design latitude;
- supporting facts that need not be requirements;
- plausible optional additions;
- unresolved questions that would require human choice.

The target is a semantic completion contract, not an expected file or wording
template.

### Baseline interpretation

The implementing agent reviews the generated specification and requirements
directly against the scenario target. The interpretation records:

- target coverage;
- important missing outcomes;
- material additional requirements;
- implementation/test/documentation activity promoted to completion;
- duplicated or fragmented outcomes;
- unsupported product or implementation decisions;
- whether increasing reasoning effort changes completeness or scope.

The user receives aggregate findings and one compact row per run. Complete
generated files, prompts, events, and raw evidence remain optional detail.
This baseline is interpreted before any automated semantic judge or guidance
calibration is designed.

### Accepted semantic findings

The user reviewed and accepted the September 14 interpretation. Requirement
count is only descriptive because one semantic outcome may be split into
several rows or several completion obligations may be packed into one row. The
evaluator and later guidance must distinguish:

1. **Valid decomposition:** independently meaningful outcomes that can usefully
   be implemented, verified, accepted, deferred, documented, or tracked
   separately.
2. **Fragmentation:** variants, actions, boundaries, protected surfaces, or
   test cases split into separate requirements even though one outcome with
   acceptance cases would be clearer.
3. **Useful specification detail:** concrete examples or approved design
   closure that make the target implementable without independently enlarging
   completion.
4. **Necessary derived behavior:** an outcome that follows from the requested
   behavior and would leave the target incomplete if omitted.
5. **Unsupported public behavior:** a new observable contract or edge-case
   decision that was neither requested nor approved.
6. **Quality requirement:** a required, assessable quality such as
   accessibility, performance, security, reliability, compatibility, or
   portability.
7. **Implementation constraint:** a mandated technology, architecture,
   algorithm, query shape, or internal approach.
8. **Wrong record role:** implementation work, tests, verification procedure,
   documentation work, or task mutation boundaries promoted into product
   requirements.

The accepted project-specific interpretation is:

- Eleventy produced the largest visible row growth, but much of it was
  fragmentation of one compatibility outcome into home, tag, feed, sitemap,
  post-navigation, and post-URL requirements. Material expansion included
  unapproved empty-archive behavior and exact accessibility mechanisms.
- FastAPI produced fewer extra rows but more consequential public-contract and
  implementation expansion: conflicting defaults for a request that supplies
  only one pagination parameter, empty-page behavior, exact validation-body
  guarantees, and a mandatory database-side slice plus separate count query.
- Flask/Vue mixed valid cross-layer decomposition with repeated splitting by
  UI choice and CRUD operation. Material expansion included conflicting
  behavior for unsupported `read` values, exact existing-field/rendering
  guarantees, internal boolean-parsing behavior, and testing/documentation
  work made normative.
- GLM low generally grouped related outcomes and stayed closest to the target.
  Higher GLM effort increasingly resolved ambiguity and made details
  normative. GPT expanded more at every project level, but effort was not
  monotonic: xhigh most often explored and promoted hidden failure modes,
  while max sometimes regrouped product outcomes but added stronger
  implementation or process requirements.

### Research basis

The future rewrite direction is supported by:

- [ISO/IEC/IEEE 29148 requirements engineering terminology and
  processes](https://www.iso.org/obp/ui?_escaped_fragment_=iso%3Astd%3Aiso-iec-ieee%3A29148%3Aed-2%3Av1%3Aen),
  including necessity, traceability, validation, and verification.
- [NASA Systems Engineering
  Handbook](https://www.nasa.gov/wp-content/uploads/2018/09/nasa_systems_engineering_handbook_0.pdf),
  including necessary, singular, feasible, verifiable, traceable, and
  implementation-free requirements plus rationale for mandated methods.
- [IREB requirements engineering
  glossary](https://cpre.ireb.org/en/downloads-and-resources/glossary) and
  [Foundation Level
  Handbook](https://cockpit-v1.ireb.org/media/pages/downloads/cpre-foundation-level-handbook/2e6dfb2912-1733311662/cpre_foundationlevel_handbook_en_v1.2.pdf),
  including functional requirements, quality requirements, constraints, and
  quantitative quality representation where practical.
- [GitHub Spec Kit agentic SDD
  workflow](https://github.com/github/spec-kit/blob/main/docs/reference/agentic-sdd.md)
  and [existing-project
  guidance](https://github.com/github/spec-kit/blob/main/docs/guides/existing-projects.md/),
  including specification/clarification/planning/task boundaries and bounded
  specification of changes in existing systems.
- [Kiro requirements-first
  guidance](https://kiro.dev/docs/specs/feature-specs/requirements-first/),
  including structured requirements, edge-case analysis, and the requirement
  for humans to validate completeness and intent.
- [Easy Approach to Requirements Syntax
  paper](https://ccy05327.github.io/SDD/08-PDF/Easy%20Approach%20to%20Requirements%20Syntax%20%28EARS%29.pdf),
  which helps phrase selected requirements clearly but does not decide whether
  a proposed obligation belongs in scope.

The research adds five durable conclusions:

- necessity and semantic traceability should be evaluated before completeness;
- singularity means one independently meaningful outcome, not one row per
  variant or test case;
- quality requirements and implementation constraints should be distinguished
  instead of grouped under an unrestricted “non-functional” category;
- ambiguity in a public contract should trigger a question or an explicitly
  authorized design decision rather than silent invention;
- edge-case discovery is useful, but “consider this” must not automatically
  become “completion requires this.”

### Approved future guidance rewrite direction

The following proposed wording is preserved verbatim as the approved direction
for a later guidance rewrite. It is not maintained guidance yet and must not be
applied before the current-guidance comparison is reviewed.

#### 1. What belongs in requirements?

A requirement must be necessary and traceable to:

- an explicit requested outcome;
- an explicitly preserved existing contract;
- a necessary consequence of the target;
- an applicable approved policy or standard;
- or an approved design or quality decision.

#### 2. What kinds of requirement are there?

- Behavioral outcome.
- Quality requirement.
- Approved constraint.

Project, process, testing, documentation, and implementation work are tracked
elsewhere.

#### 3. How much should be separated?

Use one requirement per independently meaningful outcome. Keep variants,
operations, boundaries, and examples as acceptance criteria unless independent
tracking or acceptance adds value.

#### 4. What happens to discovered uncertainty?

- Public behavior uncertainty → open question.
- Tentative interpretation → explicit assumption.
- Technical option → design decision.
- Risk or edge case → acceptance example, question, or testing consideration.
- Do not silently make it normative.

#### 5. How should requirements be written?

Each requirement should be:

- necessary;
- appropriate to its abstraction level;
- clear and unambiguous;
- sufficiently complete;
- singular without being mechanically atomized;
- feasible;
- verifiable;
- traceable to its reason.

The future rewrite should also preserve these exact rules:

> A requirement should pass this counterfactual:
>
> If this requirement were removed, would an explicit user need, approved
> quality target, preserved contract, or necessary consequence of the target
> remain unsatisfied?

> A requirement states one independently meaningful completion outcome.
> Variants, examples, boundary values, and test cases belong beneath it unless
> they need independent implementation, acceptance, deferral, or status
> tracking.

> Do not silently turn an ambiguous public-contract choice into a requirement.
> Record it as an open question unless the task author has authorized the agent
> to make that class of design decision.

> Inspect enough of the existing system to identify the requested behavior and
> relevant compatibility boundaries. Do not turn every discovered
> implementation detail or existing behavior into a requirement.

> Consider relevant edge cases and risks, but classify each one. An edge case
> becomes a requirement only when it changes an independently necessary
> outcome. Otherwise place it under acceptance examples, testing strategy,
> assumptions, or open questions.

> A model may discover many relevant considerations. Only necessary,
> traceable, and approved outcomes or constraints become requirements.

### Planned semantic evaluator

The evaluator must assess semantic obligations rather than headings, keywords,
row count, or exact wording. It should first extract the candidate's normative
requirements and then return structured JSON containing:

- coverage of each hidden required outcome with exact candidate evidence;
- candidate requirements or normative clauses mapped to their likely source;
- grouping and decomposition findings;
- missing or partially covered outcomes;
- added obligations classified as:
  - valid decomposition;
  - necessary derived behavior;
  - approved or permissible design closure;
  - approved quality requirement;
  - unsupported public behavior;
  - implementation constraint;
  - acceptance example promoted to a requirement;
  - implementation, testing, verification, documentation, or task-scope
    material in the wrong record;
- severity and human review impact;
- a concise overall interpretation.

Semantic assertions should cover:

1. every required outcome is complete or any omission is reported;
2. unsupported public behavior is absent;
3. implementation constraints are absent unless explicitly authorized by the
   target;
4. task, testing, verification, and documentation work is not counted as a
   product requirement;
5. grouping remains proportionate, without requiring an exact item count;
6. unresolved public-contract choices are surfaced instead of silently made
   normative;
7. the result remains readily reviewable by a human.

The accepted direct interpretation of Dataset A is the evaluator calibration
reference. Calibration must reproduce the important distinctions already
accepted by the user, including:

- Eleventy compatibility fragmentation versus material additions;
- conflicting FastAPI missing-parameter defaults;
- FastAPI database-query implementation constraints;
- conflicting Flask unknown-`read` behavior;
- task/testing/documentation obligations promoted into requirements;
- the absence of major required-outcome omissions.

The recommended primary semantic evaluator is
`glm-5.3-flash:cloud` at max effort, following the user's earlier direction to
try GLM for independent semantic assessment. Its output is accepted only
through schema validation and agreement with the approved Dataset A anchor
findings. If that model cannot reproduce those distinctions, stop and present
the disagreements rather than weakening the target or silently choosing a
different judge.

The evaluator is not blind and does not hide producer identity. The result
report may compare judge findings by producer model and effort, but producer
identity must not change the semantic target.

### Current-guidance comparison

Dataset B uses the exact maintained project-independent documentation guidance
that applies to the three external-style fixtures. It does not inject the
Crystal Lattice repository addendum into those projects. It also adds the exact
effective `TASKS-v7` content delivered through the developer message when
task-file guidance is active. Because subtask 068 has not yet established
canonical/bundled ownership, the evaluation records the documentation-guidance
source, task-guidance source, file hashes, and compiled effective developer
message instead of assuming one task-guidance file is canonical.

Each Dataset B prompt preserves the scenario's product request and adds only:

> Create one task file with a Draft execution plan for this change. Do not
> implement the change.

The prompt does not request a testing strategy separately. The effective
current task guidance already requires `Requirement verification` and optional
`Additional implementation verification`, so testing-plan quality is observed
from the plan structure the standing guidance naturally produces.

The task-file evaluator reads the task requirements and plan but does not score
subtask decomposition. The prompt explicitly requests one task so this
evaluation remains owned by requirement and testing-plan quality. Subtask 069
retains ownership of deciding one task versus a task directory and evaluating
subtask boundaries.

### Testing-plan semantic target

Testing-plan assertions operate on Dataset B's existing producer output; no
separate testing-plan prompt or model run is allowed.

The general target is:

- each planned test or manual check maps to an approved requirement, material
  risk, or necessary implementation boundary;
- the plan chooses the cheapest reliable layer that can prove the behavior;
- at least one realistic public-boundary or production-adapter crossing is
  planned when behavior spans layers;
- lower-level tests remain focused and do not duplicate every public test;
- assertions target required public, persisted, interoperability, security, or
  otherwise approved behavior instead of incidental implementation values,
  structures, call sequences, or formatting;
- examples, boundary values, and operations are sampled proportionately rather
  than expanded into exhaustive combinations without a risk reason;
- framework behavior is not retested when ordinary framework validation is
  sufficient;
- tests do not mandate an unapproved implementation;
- automated, manual, static, and human review evidence remain distinct;
- the plan foregrounds decisive requirement verification rather than routine
  formatting, lint, or build bookkeeping.

Scenario-specific expectations are:

- **Eleventy:** use a real site build to verify page size, route continuity,
  order and exactly-once coverage, navigation boundaries, static output, and
  protected generated surfaces. Avoid exact HTML snapshots or exact ARIA/CSS
  assertions unless the specification made them contractual.
- **FastAPI:** exercise the public HTTP route for unparameterized
  compatibility, pagination, bounds, normal validation, ordering, array body,
  total header, and unchanged endpoints. Avoid requiring exact framework error
  payloads, ORM calls, or SQL/query structure unless separately approved.
- **Flask/Vue:** combine focused Flask API tests and Vue component behavior
  tests with a realistic frontend/backend or production-adapter crossing for
  the filter flow. Cover representative CRUD refresh persistence without
  multiplying every operation by every filter and state when smaller coverage
  proves the same behavior.

## Execution plan

Status: Approved

The user approved and completed review of the original diverse-project
baseline on September 14, 2026. Steps 1–6 below were approved and executed.
The user approved the adjusted evaluator, current-guidance task-file matrix,
and comparison in Steps 7–10 on September 14, 2026. No maintained guidance
change is authorized by this plan.

### 1. Record the approved evaluation target

1. Create this subtask and add it to the parent task.
2. Add a stable documentation-standard validation requirement.
3. Reclassify original Test 22 as preliminary robustness evidence rather than
   complete verification of requirement quality.
4. Record the relation with subtasks 068 and 069.

### 2. Establish the diverse project scenarios

1. Replace the same-family primary set with pinned, compact fixtures derived
   from Eleventy Base Blog, FastAPI CRUD Async, and Flask-Vue CRUD.
2. Preserve project purpose, users, architecture, public behavior, relevant
   source, upstream revision, and attribution in each fixture and scenario.
3. Create semantic targets for archive pagination, public notes pagination,
   and full-stack read-status filtering.
4. Retain Tests 30–32 and their target-review history only as optional
   same-family controls.
5. Add deterministic target, fixture, attribution, and project-context checks.

### 3. Freeze the requirement-minimal baseline

1. Add an evaluation-only guidance source containing only documentation
   placement, specification-target, current-documentation, and minimal
   requirements-role context.
2. Exclude detailed requirement-minimality rules, negative examples, sample
   requirement tables, evidence guidance, and `TASKS-v7`.
3. Add fresh-scenario execution without a model-generated seed.
4. Record exact target, guidance, prompt, fixture, model, effort, and profile
   hashes.
5. Add only run-integrity and mutation-boundary assertions.

### 4. Run the 21 producer baseline

1. Preflight `glm-5.3-flash:cloud` and its low/high/max efforts.
2. Run the three scenarios for all GLM efforts.
3. Preflight `gpt-5.6-luna` through ChatGPT login and its
   medium/high/xhigh/max efforts.
4. Run the three scenarios for all GPT efforts.
5. Preserve every generated specification, requirements file, response,
   changed path, and raw request/session record.
6. Report provider or effort failures without silently substituting a profile.

### 5. Interpret the baseline directly

1. Compare every generated requirement set with its semantic target.
2. Map missing and partially covered target outcomes.
3. Classify additional requirements as necessary constraints, supporting
   detail, implementation/testing/documentation work, optional improvement,
   unsupported design, duplication, or unrelated expansion.
4. Compare requirement count and semantic outcome count without treating
   either count as a verdict.
5. Identify scenario-specific, model-specific, and effort-related expansion or
   omission patterns.
6. Record uncertain judgments and link the exact generated text.

### 6. Prepare the human baseline review and stop

1. Begin with the cross-scenario and cross-model conclusions.
2. Explain each actual project and task sufficiently for the findings to stand
   alone.
3. Show one compact row per run with target coverage, material omissions,
   material additions, requirement count, and interpretation.
4. Put complete generated requirements, specifications, responses, and raw
   evidence behind optional links.
5. Present which controls could be cut or retained.
6. Stop for user review before designing model-driven assertions, changing
   guidance, repeating cells, or running a candidate matrix.

### 7. Freeze the accepted semantic interpretation

1. Preserve the accepted September 14 report as Dataset A's human calibration
   reference.
2. Add a structured interpretation record for its agreed project-level and
   model/effort findings without turning exact requirement counts into targets.
3. Version and hash the requirement-quality taxonomy, scenario targets, and
   evaluator prompt before evaluator execution.
4. Keep original producer records immutable.

### 8. Implement and calibrate the semantic evaluator

1. Extract normative requirements and required sections from each candidate
   without assuming filenames, headings, tables, or checklist syntax.
2. Implement the structured semantic judge response and deterministic schema,
   provenance, and completeness validation.
3. Run the recommended GLM max evaluator against Dataset A.
4. Compare its findings with the accepted anchors for all three projects and
   representative low/high-expansion runs.
5. Refine evaluator instructions or structure only when the accepted semantic
   distinction is unchanged.
6. Stop and report material disagreement if the evaluator cannot reliably
   distinguish valid decomposition from unsupported behavior, implementation
   constraints, or wrong-record material.
7. Once calibrated, evaluate all 21 Dataset A records and preserve per-run
   structured findings.

### 9. Run the current task-file-guidance matrix

1. Build Dataset B from the same fixtures, product requests, hidden targets,
   producer profiles, and efforts.
2. Request one task file with a Draft execution plan, relying on the effective
   current task guidance to elicit requirement and additional implementation
   verification without repeating that instruction in the prompt.
3. Inject the exact maintained current general documentation guidance plus the
   exact effective current task-file developer-message guidance.
4. Capture the task-guidance source, compiled developer message, hashes, and
   model/effort provenance.
5. Run all 21 producer cells once with fresh equivalent workspaces.
6. Apply the calibrated requirement-quality evaluator to the task
   requirements.
7. Apply the testing-plan semantic assertions to the same task-file output,
   using the same evaluator call when the structured response remains clear
   and reviewable.
8. Do not score task-directory decomposition; record any attempted unrequested
   task split as a scope/mutation finding and leave decomposition calibration
   to subtask 069.

### 10. Compare current guidance and stop before rewriting

1. Compare Dataset A with B to show how requirement derivation changes between
   specification output under minimal guidance and task-file planning under
   the real current documentation-plus-task-guidance context.
2. Avoid attributing a difference solely to documentation guidance,
   `TASKS-v7`, or output format because those dimensions intentionally change
   together in the requested real-context comparison.
3. Compare requirement expansion with testing-plan expansion by project,
   producer model, and effort.
4. Distinguish target coverage, valid decomposition, unsupported behavior,
   implementation constraints, wrong-record material, test-layer gaps,
   unnecessary tests, and review burden.
5. Present aggregate findings first and concise per-run results second, with
   complete records optional.
6. State which findings support, contradict, or refine the preserved future
   guidance wording.
7. If a material result cannot be interpreted without isolating the
   documentation layer, recommend a later documentation-only replay rather
   than adding it automatically.
8. Stop for user review. Do not edit maintained documentation guidance,
   `TASKS-v7`, or testing guidance and do not run candidate guidance until a
   separate rewrite plan is approved.

### Implementation decisions and open questions

- **Approved:** preserve Test 22 and add new scenario IDs instead of
  overwriting its historical evidence.
- **Approved:** run one minimal-guidance baseline first; a candidate comparison
  would be an additional separately approved 21-run matrix.
- **Approved:** the primary scenarios use three different public-project
  shapes rather than three package/API variants.
- **Approved:** Eleventy archive pagination, FastAPI public notes pagination,
  and Flask/Vue full-stack book filtering are approved starting targets.
- **Approved:** no additional target review is required before producer
  execution.
- **Approved:** the implementing agent may inspect model and effort identity
  while interpreting the baseline and should identify expansion trends
  directly.
- **Approved:** the user reviews the interpreted baseline rather than
  reconstructing every semantic mapping or receiving a separate reviewer-model
  matrix.
- **Approved:** content quality is semantic; mechanical checks cover only run
  integrity and provenance.
- **Approved:** target changes after producer execution create a new target
  version and invalidate affected runs.
- **Approved:** subtask 069 consumes the findings but retains ownership of
  task decomposition.
- **Approved:** automated semantic judges and further independent target
  reviews were not part of the initial baseline.
- **Approved:** the user accepts the September 14 direct semantic
  interpretation and its distinction among necessity, decomposition,
  fragmentation, design closure, quality requirements, implementation
  constraints, unsupported behavior, and wrong-record material.
- **Approved scope:** the follow-up compares the immutable initial baseline
  with one current-guidance task-file matrix before any guide change.
- **Approved scope:** testing-plan evaluation consumes the task-file producer
  outputs and adds semantic assertions rather than a third producer matrix.
- **Approved scope:** Dataset B requests one task file, so this task measures
  requirement derivation and testing plans without taking over subtask 069's
  task-directory decomposition responsibility.
- **Approved:** use
  `glm-5.3-flash:cloud` at max effort as the primary semantic evaluator and
  require agreement with the accepted Dataset A anchor findings before using
  its assertions on new runs.
- **Approved:** Dataset B receives the exact
  maintained project-independent documentation guidance plus the exact
  effective task-file developer message.
- **Approved:** run 21 new Dataset B producer
  calls, with no repeated samples before reviewing the first comparison.
- **Approved:** the task-file producer prompt does not separately ask for a
  testing strategy; testing-plan assessment uses the verification sections
  naturally required by the effective current task guidance.
- **Approved boundary:** no maintained documentation, task-file, or testing
  guidance changes and no candidate matrix before the two-dataset comparison
  is reviewed.
- Exact fixture filenames, target JSON keys, result-table presentation, and
  interpretation helpers are local choices if they preserve these boundaries.

### Documentation

- This task and the parent task
- Documentation-standard requirements
- Agent-behavior verification index
- Three diverse scenario pages and structured target files
- Requirement-minimal guidance variant
- Producer-run instructions
- Interpreted baseline report with optional detailed evidence
- Accepted semantic interpretation and exact future-guidance wording in this
  task
- Structured semantic evaluator schema, prompt, assertions, and calibration
  records
- Current-guidance task-file producer records
- Two-dataset requirement and testing-plan comparison report

### Task checklist

- [x] Create the task and parent/dependency relations.
- [x] Record the new validation requirement and preliminary Test 22 status.
- [x] Add the three diverse pinned-project scenarios and targets.
- [x] Reclassify Tests 30–32 as optional same-family controls.
- [x] Remove active target-review and separate reviewer-model machinery.
- [x] Add deterministic diverse-target, fixture, project-context, and
  attribution checks.
- [x] Freeze approved targets and the minimal-guidance baseline.
- [x] Implement the fresh 21-case producer matrix.
- [x] Run the 21 producer cases.
- [x] Interpret requirement quality and model/effort expansion directly.
- [x] Prepare the compact human baseline review with optional detail.
- [x] Present baseline findings and stop before calibration.
- [x] Record user acceptance of the interpretation.
- [x] Preserve the research findings and exact future-guidance wording.
- [x] Freeze structured Dataset A interpretation anchors.
- [x] Implement the semantic evaluator and deterministic schema checks.
- [x] Calibrate the evaluator against Dataset A.
- [x] Run and evaluate the 21-cell current-task-file-guidance matrix.
- [x] Apply testing-plan assertions to the same task-file outputs.
- [x] Prepare the concise two-dataset comparison.
- [x] Present the comparison and stop before guide rewriting.

### Requirement verification

| Requirement group | Acceptance evidence |
|---|---|
| Scenario and target quality | Three structured targets cover a public website, public REST API/performance concern, and full-stack application; fixtures preserve pinned source context and attribution and pass deterministic checks. |
| Producer matrix | Canonical run evidence contains exactly three scenarios for each of seven model/effort profiles with identical scenario inputs and requirement-minimal guidance. |
| Semantic quality | The interpreted baseline maps generated requirements to approved target outcomes and classifies material omissions, additions, implementation prescriptions, duplication, ambiguity, and expansion without literal token matching. |
| Focused human review | The main review explains each project, foregrounds aggregate model/effort findings, and shows one concise row per run while keeping complete evidence optional. |
| Semantic evaluator | Structured evaluator results reproduce the accepted Dataset A distinctions, identify exact candidate evidence and target mappings, and report disagreement instead of changing the target. |
| Current task-file guidance | Dataset B contains 21 complete single-task-file runs with maintained general documentation guidance and effective task guidance captured in the developer message, using the same requirement-quality target as Dataset A. |
| Testing-plan quality | Dataset B results identify decisive requirement coverage, appropriate layers and crossings, missing important evidence, unnecessary or duplicated tests, implementation coupling, and routine verification noise without an additional producer matrix. |
| Focused comparison | Human review can compare A versus B by project/model/effort and inspect exact records only when needed. |
| Guidance-change boundary | Git and task inspection show no maintained documentation, task, or testing guidance changed before the two-dataset comparison is reviewed and a rewrite plan is approved. |

### Additional implementation verification

- Validate target JSON schemas and scenario/target ID parity.
- Verify fixture attribution and pinned upstream revisions.
- Verify producer prompts do not contain the hidden target or review rubric.
- Verify guidance/model/effort/target changes invalidate only the intended
  cache layers.
- Verify GPT producer requests use ChatGPT login and the requested effort.
- Verify the baseline summary links every optional detailed record.
- Verify Dataset A records are unchanged and remain addressable by their
  original target/guidance/model/effort hashes.
- Verify evaluator JSON schema, evidence paths, target mappings, category
  values, and judge model/effort provenance.
- Verify evaluator instructions and targets are hidden from producers.
- Verify Dataset B preserves Dataset A's scenarios, targets, fixtures,
  models, and efforts while changing only the declared output mode and current
  guidance context.
- Verify the effective `TASKS-v7` developer message is captured exactly for
  Dataset B.
- Verify testing-plan assertions read Dataset B output without triggering a
  second producer request.
- Verify reports foreground material requirement and testing evidence instead
  of routine run counts.
- Run deterministic agent-evaluation tests, Ruff, Python compilation, and
  `git diff --check`.

## Implementation Notes

- September 14, 2026: The user approved the staged task and authorized
  execution. The first execution boundary is target drafting, independent
  ChatGPT review, and human approval; producer runs remain blocked until that
  approval.
- Local configuration contains `codex-openai` with `gpt-5.6-sol` and saved
  ChatGPT authentication. No local `gpt-6-astra` configuration was found, so
  target review uses `gpt-5.6-sol`; result review retains the approved Astra
  preflight option.
- Added three five-outcome target drafts and matching synthetic fixtures for
  batch enqueue, a per-request timeout, and an optional CLI report destination.
  Seven deterministic target/fixture/workspace tests pass.
- Added six gated independent target-review cases using `gpt-5.6-sol` through
  ChatGPT authentication at high and max effort. The first high-effort review
  completed and identified a real fixed-versus-configurable batch-limit
  ambiguity.
- The first review exposed two harness-only issues after successful model
  completion. The review workspace now initializes its own Git repository so
  cache restoration cannot target the source worktree, and auth assertions use
  the configured ChatGPT mode while preserving redaction in canonical
  evidence. Regression coverage verifies the isolated Git root.
- The complete six-review command ran in the background as PID `36375`; its
  log is `/tmp/task-067-target-reviews.log`.
- The complete target-review matrix passed: six ChatGPT-authenticated
  `gpt-5.6-sol` cases at high/max effort completed in 517.09 seconds. Batch
  reviews exposed the configurable-versus-fixed maximum as the only material
  unresolved product choice. Timeout and report-output reviews approved the
  behavioral core with concise refinements.
- Prepared and sent a self-contained target-review document for the first
  same-family scenario set. The user reviewed it and approved the individual
  requirement targets but replaced that set as the primary baseline; the
  superseded active review file was then removed.
- Expanded the target review at the user's request so it stands alone. It now
  explains Crystal Lattice's specification/requirements/task model, why Test
  22 is insufficient, the planned seven-profile matrix, the information used
  to construct targets, the human approval boundary, and the complete existing
  implementation for each synthetic package. No external research is required
  for these deliberately self-contained scenarios.
- September 14, 2026: The user approved immediate producer execution but
  replaced the primary scenarios with three diverse public-project tasks:
  Eleventy archive pagination, FastAPI public notes pagination, and Flask/Vue
  full-stack book filtering. The earlier SDK-style scenarios remain optional
  controls.
- The same approval removed target-review and separate reviewer-model
  requirements. The implementing agent now interprets the 21-run baseline
  directly with model/effort identity visible, and the user reviews that
  concise interpreted baseline before any calibration, semantic judge,
  repetition, candidate guidance, or paired candidate matrix.
- The previous six ChatGPT target reviews and Kindle bundle are retained only
  as implementation history. They are not acceptance evidence or an active
  execution dependency.
- The superseded target-review prompt, gated reviewer test, and active review
  document were removed after the user approved direct baseline execution.
- Added pinned, attributed project fixtures and targets for Eleventy archive
  pagination, FastAPI public notes pagination, and Flask/Vue full-stack book
  filtering. The producer suite now collects exactly 21 cases over seven
  model/effort profiles.
- Added an explicit requirement-minimal guidance variant, fresh seedless
  scenario execution, flexible specification/requirements presence checks,
  mutation-boundary assertions, and complete semantic-input records.
- Final pre-run verification passes 78 deterministic tests, Ruff, Python
  compilation, scenario indexing, and `git diff --check`.
- Completed all 21 producer calls: nine GLM runs in 690.09 seconds and twelve
  GPT ChatGPT-account runs in 2,091.06 seconds. Every request completed,
  produced specification/requirements content, preserved mutation scope, and
  recorded the selected model and effort.
- The original pytest processes reported three GLM and twelve GPT failures
  because they loaded the initial output-presence matcher before its flexible
  filename/heading calibration. Offline application of the corrected matcher
  accepts all 21 preserved records; no model rerun was performed.
- GLM max on the Flask/Vue task issued malformed shell commands, recovered,
  completed the requested documentation, and reported no provider error. The
  tool misuse remains part of the raw behavioral evidence.
- Added
  `maintainer/docs/evaluations/documentation-guidance/20260914-requirement-quality-baseline-results.md`
  with aggregate model/effort findings, one concise row per run, and optional
  links to every complete local record. Calibration remains unplanned pending
  user review.
- September 14, 2026: The user accepted the direct semantic interpretation and
  asked to preserve the research-backed future-guidance wording. The task now
  records necessity, semantic traceability, proportionate singularity,
  behavioral versus quality versus constraint roles, clarification instead of
  silent public-contract choices, and edge-case classification as the approved
  future rewrite direction.
- The user expanded the requested evaluation scope to current task-file
  guidance and testing plans. A Draft follow-up plan now proposes one new
  21-cell task-file matrix; its outputs receive both requirement-quality and
  testing-plan assertions, so no additional testing or documentation-only
  producer matrix is planned. Maintained guide changes remain blocked until
  the comparison is reviewed.
- Frozen the 21 accepted Dataset A outputs as a durable, source-hashed fixture
  and recorded separate user-accepted coverage, expansion-severity, and
  semantic-signal anchors that are hidden from the evaluator prompt.
- Implemented one-call-per-project semantic evaluation with structured
  requirement coverage, added-obligation classifications, grouping findings,
  known semantic signals, expansion severity, review burden, and optional
  testing-plan assessment. Deterministic preflight passes 81 tests and the
  real suites collect 21 task producers plus three project-batched judge cases.
- September 15, 2026: Initial evaluator prompt v1 found the substantive
  accepted patterns but underweighted cumulative minor additions and treated
  independently regressible surfaces as automatically valid decomposition.
  Prompt v2 clarified cumulative severity, proportionate separation,
  unresolved public behavior, exact-mechanism scope, and the distinction
  between legitimate task-plan implementation detail and product requirements.
- V2 calibration passed all three project batches against the user-accepted
  Dataset A anchors. Adjacent severity bands and semantically equivalent
  task/documentation and testing/verification role-contamination signals are
  accepted where the underlying finding remains unchanged.
- Completed Dataset B producer execution on September 15, 2026. GPT completed
  all twelve task-file cells with structural/mutation checks passing. GLM
  completed all nine cells; after correcting two exact-heading parser false
  negatives, three genuine task-guidance failures remain: Eleventy high left
  generated `_site` files, FastAPI low omitted the required closing decisions
  section, and FastAPI high added premature Implementation Notes.
- The task-file prompt did not mention a testing strategy or test plan. All 21
  tasks nevertheless contained requirement-verification planning from the
  standing task guidance.
- Completed three project-batched Dataset B semantic/testing evaluations. The
  Flask/Vue response omitted one candidate-closing JSON brace; a narrow,
  recorded structural repair restored the schema without changing semantic
  text or rerunning the judge.
- Frozen all 21 task-file records, exact current guidance metadata, and all six
  calibrated Dataset A/B semantic batches as durable fixtures.
- Added
  `maintainer/docs/evaluations/documentation-guidance/20260915-requirement-task-testing-comparison.md`.
  It records complete requirement coverage, the shift from 5 high/12 medium
  expansion results to 0 high/5 medium, 12 complete and 9 partial testing
  plans, 20/21 important crossings, three genuine GLM structure/mutation
  failures, and the future guidance implications. Maintained guidance remains
  unchanged pending user review.

## Completion Notes

- Outcome: completed the three-project, seven-profile requirement-quality
  baseline; calibrated a semantic evaluator against the accepted human
  interpretation; reused the same projects and profiles for current task-file
  guidance; and assessed requirement and testing-plan quality from the same 21
  task outputs without prompting for a testing strategy.
- Primary evidence: commit `73a2f4bf`; the September 14 direct baseline report;
  the September 15 requirement/task/testing comparison; frozen Dataset A,
  Dataset B, and six semantic result batches under
  `maintainer/agent-evaluation/suites/documentation_standard/fixtures/`.
- Verification: 83 deterministic tests, Ruff, Python compilation, JSON schema
  and link validation, exact model/effort provenance, 21 current task-file
  producer calls, and six project-batched semantic evaluator calls. Evaluator
  v2 passes all accepted Dataset A anchors.
- Findings: current task guidance preserves complete product coverage and
  reduces high/medium requirement expansion substantially, especially for GPT.
  Remaining issues concern public-contract ambiguity, compatibility
  fragmentation, incomplete or mocked-away testing boundaries, tests for
  invented behavior, and three genuine GLM task-structure/mutation failures.
- Plan deviations: the proposed separate current-documentation-only replay was
  removed as unnecessary; testing-plan assessment reused task-file runs; two
  heading-parser false negatives and one missing JSON candidate brace were
  corrected without replacement producer or judge calls.
- Follow-up ownership: subtask 010 owns the general requirements/testing guide
  rewrite, subtask 068 owns canonical and bundled `TASKS-v7`, and subtask 069
  owns the exact paired candidate matrix plus later task-decomposition
  calibration. No maintained guide was changed by this completed subtask.