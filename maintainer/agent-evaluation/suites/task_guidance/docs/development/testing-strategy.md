# Task-guidance evaluation testing strategy

> **Not implemented:** This strategy defines the approved test target for task
> 090. Commands and executable markers will be added only with the suite.

## Risks

The suite targets these failure classes:

- approved outcomes disappear or multiply when a plan becomes a task;
- implementation, tests, documentation, or evidence become product
  requirements;
- substantial work becomes ten or more implementation, technical-layer, test,
  documentation, and review fragments instead of a few coherent deliverables;
- layer boundaries are rejected even when a service, SDK, platform, or
  consumer is independently usable or owned;
- independent slices are forced into one unreviewable task;
- dependencies follow numbering rather than real blockers;
- no child or parent owns an important integrated crossing;
- retained plans lose material decisions or verification;
- omitted plans retain disguised implementation direction or discard facts;
- a fresh agent must repeat broad investigation because the handoff is thin;
- fewer tool calls mask an incomplete plan;
- high reasoning effort expands scope or decomposition.

## Scenario coverage

Use the six contracts under `scenarios/`:

- three bounded handoff cases for retain/omit plans, continuation, and
  investigation reuse;
- three complex decomposition cases: vertical full-stack slices,
  independently deliverable component boundaries, and compatibility migration
  states;
- production crossings through generated output, HTTP/storage, and
  client/transport/server behavior.

Prompts remain natural prose. Targets and canonical plans are evaluator inputs,
not content copied into user prompts.

## Stage matrices

### Task creation

Inputs:

- reviewed request and approved outcomes;
- reviewed project facts or canonical investigation;
- optional reviewed plan according to the scenario;
- current guidance and exact delivery provenance.

Evidence:

- task files and changed paths;
- parent and child requirements;
- topology and dependency graph;
- preserved decisions/questions;
- retained/omitted plan content;
- tool telemetry.

### Fresh-agent plan preparation

A new session receives the reviewed task handoff and no first-agent
conversation. It is asked to present a plan without modifying files.

Evidence compares the plan with:

- approved outcomes;
- canonical plan semantics;
- task requirements and supporting facts;
- material decisions and questions;
- important crossings and unavailable evidence.

### Same-agent continuation

Continue the task-creation session into plan preparation. Use the same semantic
target as the fresh-agent stage and compare investigation effort only after
both plans pass.

## Continuity variants

For reviewed scenarios, compare:

1. retained-plan task;
2. complete omit-plan task;
3. optional incomplete-handoff negative control.

Do not use every variable producer output as every later subject's input. One
reviewed linear reference flow supplies canonical stage fixtures; focused
generated-output chains test continuity.

## Deterministic validity

Validate before semantic assessment:

- expected files exist and are captured after workspace cleanup;
- only authorized paths change;
- guidance, runner, project, model, effort, prompt, and stage-input hashes
  match;
- task Markdown parses;
- parent links and declared dependencies resolve;
- dependency graph is acyclic;
- continuation provenance identifies the correct parent;
- required structured evaluator records validate.

Behavioral quality findings do not make a structurally valid record unusable.

## Semantic quality

Assess:

- outcome completeness and added obligations;
- requirement grouping and record roles;
- plan preservation or omission;
- decision/question preservation;
- task and subtask rationale;
- coherent deliverable count and actual-subtask mapping;
- mergeable fragments and descriptive fragmentation ratio;
- overpacked or unmatched work;
- working iterations and isolated responsibilities;
- valid versus automatic technical-layer boundaries;
- unnecessary dependencies;
- crossing ownership;
- reconstructed-plan completeness;
- unsupported public or implementation choices.

Use reviewed semantic targets. Do not require exact wording.

## Efficiency

Record tool use by category. Compare only identical model/effort profiles and
semantically passing plans.

Initial B0 reporting is descriptive. After variance is reviewed, task 090 may
propose a threshold such as a median 30–50% reduction in investigation calls.
The threshold requires explicit approval before becoming an assertion.

Duration and token counts are supporting signals, not primary acceptance,
because provider latency and output length vary.

## Model and effort cohort

Initial baseline recommendation:

- GLM max for all six task-creation and plan-preparation contracts;
- GPT high for all six;
- GPT xhigh for the most sensitive completeness, decomposition, and handoff
  cases;
- repeated runs only for efficiency comparisons or observed variance.

Expand the cohort only after B0/B1 review justifies the cost.

## Nondegradation

B1 and later candidates must preserve:

- task-guidance source/bundled parity;
- default-runner message and tool preflights;
- deterministic agent-evaluation tests;
- existing requirement completeness and important-crossing behavior within
  observed variance;
- current guidance until explicit promotion approval.

When only TASKS mechanics change, focus compatibility reruns on task mode rather
than repeating unaffected root-only cells.

## Human review

The review package should show:

- the scenario and canonical target;
- task topology and outcome mapping;
- fresh/same-agent plan summaries;
- missing or added material;
- normalized investigation metrics;
- candidate deltas and anomalies;
- optional links to complete records.

Humans approve scenario targets, B1, efficiency thresholds, candidate
selection, and final promotion.