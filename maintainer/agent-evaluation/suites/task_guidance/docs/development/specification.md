# Task-guidance evaluation suite specification

## Purpose

Evaluate task files as durable, approval-aware handoffs rather than isolated
Markdown outputs. The suite tests whether an agent can turn reviewed scope and
repository facts into an appropriate task shape and whether another agent can
prepare a correct plan without the original conversation or broad
rediscovery.

## Target behavior

The suite evaluates five boundaries:

1. reviewed plan or request to task-file handoff;
2. coherent decomposition of substantial work without phase or layer
   fragmentation;
3. retained-plan versus omit-plan preservation;
4. same-agent versus fresh-agent plan continuation;
5. task handoff quality versus investigation effort.

Task quality is judged against reviewed scenario outcomes and plans, not exact
wording, filename preference, or raw checkbox totals.

## Stage model

### Independent stages

The primary matrices use one reviewed canonical input for each stage:

- task creation receives the same reviewed request, project facts, and approved
  plan or scope;
- plan preparation receives the same reviewed task handoff;
- later implementation or completion stages remain out of the initial suite.

Every subject for a stage receives the same workspace revision, conversation
prefix, guidance, model/effort, and current-stage prompt. A tested subject's
variable output is not silently used as another subject's prerequisite.

### Continuity chains

Focused chains complement stage isolation:

```text
initial investigation
→ task creation
→ same-agent plan preparation
```

and:

```text
initial investigation
→ task creation
→ fresh-agent plan preparation
```

These chains test whether actual generated handoffs preserve enough durable
context.

## Task handoff contract

A useful handoff preserves:

- approved requirements and protected contracts;
- verified repository facts and source pointers;
- material decisions and their rationale;
- unresolved requirement questions and design decisions;
- exclusions and deferred work;
- important testing boundaries and unavailable evidence;
- task and subtask dependencies;
- the approval and plan status.

It omits chronology, raw logs, replaceable inventories, hidden conversation
references, and unselected speculation.

### Retained plan

A retained plan may be reorganized for clarity but preserves its material
approach, decisions, questions, dependencies, verification, documentation,
risks, and exclusions.

### Omitted plan

An omitted-plan handoff preserves facts and constraints needed to prepare a new
plan but excludes implementation direction, planned task steps, and planned
verification/documentation work. The later planning agent may inspect
remaining uncertainties; it should not repeat the first agent's broad
investigation.

## Task decomposition contract

Use one task by default.

A task directory is appropriate when approved outcomes form:

- a working iteration that leaves a usable, tested, independently reviewable
  improvement; or
- an isolated component, contract, decision, migration boundary, or other
  responsibility that can be accepted separately.

Every child identifies the parent outcomes it advances, owns the
implementation, focused tests, documentation, and evidence for its slice, and
declares only real blocking dependencies. Implementation, testing,
documentation, review, and deployment do not become horizontal phase-only
children unless their result is independently required.

The parent owns the complete contract and integrated acceptance. An important
crossing must have a clear owner after decomposition.

The primary decomposition tests use substantial work with approximately four
reviewed coherent deliverables and enough technical surface to tempt ten or
more implementation-, layer-, testing-, documentation-, and review-shaped
children.

For each produced subtask, assessment asks:

> When this subtask is complete, what approved result is independently usable,
> acceptable, deferable, owned, or reviewable?

A technical layer is not automatically a good or bad boundary. Server, client,
SDK, platform, or package work may be separate when it has independent
consumers, ownership, compatibility, deployment, or acceptance. It is
fragmentation when several layer or phase tasks must all finish before any
approved outcome exists and could be merged without losing independent value.

Complex targets define:

- reviewed coherent deliverables;
- acceptable alternative partitions;
- required and optional dependencies;
- important crossings;
- examples of mergeable fragmentation;
- examples of overpacked work;
- conditions that justify an additional child.

## Semantic assessment

Structured assessment records:

- required-outcome coverage and omissions;
- added or wrong-record obligations;
- preserved decisions and questions;
- task count and topology;
- semantic deliverable count;
- actual-subtask-to-deliverable mapping;
- mergeable subtask groups;
- fragmentation ratio as a descriptive signal;
- overpacked deliverables and unmatched subtasks;
- working iterations and isolated responsibilities;
- valid and invalid technical-layer boundaries;
- horizontal phase tasks;
- parent/child mappings;
- unnecessary or missing dependencies;
- important crossing ownership;
- retained or omitted plan fidelity;
- fresh-agent reconstructed-plan quality;
- unsupported public or internal decisions.

It also classifies six task-creation quality dimensions:

- overall fragmentation;
- phase-only implementation, test, documentation, deployment, cleanup, or
  review children;
- technical-layer splits without independent users, ownership,
  compatibility, acceptance, or complete product value;
- final evidence or documentation children that re-own work from delivery
  tasks;
- dependency graphs that permit broken intermediate states or unnecessarily
  serialize independent work;
- required production connections proved only by separate or mocked checks.

Fragmentation uses `none`, `low`, `medium`, or `high`, mapped
deterministically to 100, 67, 33, or 0. Other dimensions use `none`,
`partial`, or `present`, mapped to 100, 50, or 0. The evaluator records
concrete occurrences but does not choose numeric scores. An assessment's
success percentage is the equal-weight average of the six scores.

Results aggregate each score, affected-assessment count, and occurrence count
for the complete cohort, each provider, and each provider/effort combination.

Mechanical findings and semantic assessment remain separate.

## Investigation-efficiency evidence

Efficiency is interpreted only for plans that meet the semantic target.

Record, within the same model and effort:

- total and investigation-specific tool calls;
- unique repository files read;
- broad listings and searches;
- repeated reads;
- diagnostic commands;
- mutations;
- calls before the first substantive plan.

The expected ordering is a hypothesis to calibrate:

```text
same-agent continuation
    <= fresh agent with retained plan
    < fresh agent with complete omit-plan handoff
    < original broad investigation
```

An intentionally incomplete handoff may be used as a negative control.
Thresholds are selected after
[Stage B0 — Current-guidance baseline](../../../../../docs/evaluations/task-guidance/test-plan.md#stage-b0--current-guidance-baseline)
establishes variance.

## Baselines and candidates

### Stage B0 — Current-guidance baseline

Current guidance runs unchanged against the approved new scenarios. Quality
failures are valid baseline evidence when execution and capture are valid.

### Stage B1 — Task-mechanics candidate

The shortest evidence-backed task mechanics improve handoff and decomposition
without redistributing generic Requirements or Testing guidance. The
task-mechanics candidate becomes the placement-comparison baseline only after
existing task-guidance behavior does not materially regress.

### Stage B2 — Guidance-placement confirmation

The descriptive placement designs use the same semantic rule set:

- concise task reinforcement keeps short Requirements and Testing reminders in
  task guidance;
- centralized root guidance owns the generic semantics in compiled root
  guidance;
- routed extended explanation keeps an essential compiled core and places
  longer examples on shared pages.

Focused evidence precedes a full matrix.

## Evidence and review

Each run preserves exact guidance and stage-input hashes, project revision,
model/effort, effective instruction delivery, task files, plans, tool
telemetry, changed paths, deterministic findings, and structured assessment.

Human review receives concise scenario summaries, differences, validity
failures, semantic anomalies, and optional detailed paths. AI assessment does
not complete human verification.

## Non-goals

- Evaluating general coding intelligence or optimal architecture.
- Requiring exact task filenames, task counts outside scenario targets, or
  exact plan prose.
- Running every subject's output through every downstream model.
- Interpreting fewer tool calls as success without plan quality.
- Moving essential guidance exclusively into ordinary workspace pages.
- Implementing code or completion-stage workflows in the initial suite.