# Task-guidance evaluation plan

This plan tests whether task files preserve approved scope, support a later
agent, decompose substantial work coherently, and assign decisive evidence to
important product boundaries.

The same [six test cases](test-cases.md) are reused across three stages so
changes can be compared against stable requests and reviewed targets.

## Stage B0 — Current-guidance baseline

The current-guidance baseline runs the adopted guidance without changing its
wording. It establishes how agents currently:

- choose one task versus a task directory;
- preserve requirements, facts, decisions, questions, and exclusions;
- retain or omit an implementation plan;
- continue as the same agent or hand work to a fresh agent;
- split complex work into independently useful deliverables;
- assign tests to important production connections;
- trade investigation effort against plan quality.

Quality failures are valid baseline evidence when execution, instruction
delivery, capture, and structured records are valid.

Completion requires:

- all planned model and effort cells are valid or explicitly blocked;
- task-creation, fresh-agent, and same-agent evidence is captured;
- semantic assessment covers all six test cases;
- provider or infrastructure failures are separated from behavior findings;
- a dated result report interprets the evidence.

## Stage B1 — Task-mechanics candidate

The task-mechanics candidate adds only the shortest rules supported by the
current-guidance baseline. It may improve:

- the independent-value test for creating a child task;
- vertical versus layer-shaped decomposition;
- dependency safety between working states;
- ownership of production-boundary evidence;
- preservation of unresolved approval questions.

This stage does not redistribute generic Requirements or Testing guidance.
It uses the same test cases, targets, model profiles, and evidence schema as
the current-guidance baseline.

Candidate v1 is completed evidence rather than an all-or-nothing wording set.
Its demonstrated decomposition gains are retained while a practical-baseline
revision adds concise rules for:

- preserving implementation design and rationale when a plan becomes a task;
- making component responsibilities, interfaces or flow, compatibility and
  dependency states, decisions, and verification strategy easy to find;
- keeping shared end-to-end design in the parent and local design in children
  without repeating the same context throughout the task tree;
- clarifying that testability or reviewability alone does not make a
  technical layer independently deliverable;
- naming decisive evidence through a required production connection;
- keeping every dependency-permitted intermediate state usable and
  compatible.

The practical baseline is acceptable when it materially improves the major
known handoff or decomposition failures without a material loss in:

- approved-outcome completeness;
- scope restraint;
- important-boundary evidence;
- plan readability;
- task-guidance compilation and synchronization;
- deterministic evaluator coverage.

No single aggregate-score regression is automatically decisive. Acceptance
considers its severity and recurrence, whether affected counts actually
increase, whether approved outcomes disappear, whether the finding is caused
by the candidate-generated task or an unchanged canonical input, and the cost
of leaving a major known guidance gap unresolved.

## Stage B2 — Guidance-placement confirmation

The guidance-placement confirmation compares where the approved semantic rules
should live after the task-mechanics candidate is stable.

The candidate designs are described by purpose rather than opaque version
numbers:

- **Concise task reinforcement:** root Requirements and Testing contain the
  generic rules, while task guidance keeps short completeness and evidence
  reminders.
- **Centralized root guidance:** root Requirements and Testing are the sole
  generic owners; task guidance maps them into task-file sections.
- **Routed extended explanation:** essential rules remain in compiled
  instructions, while examples and longer explanations live in shared pages.

Focused sensitive cases run first. A full model and effort matrix is run only
for the selected design. Promotion requires explicit human approval and a
dated confirmation report.

## Test flow

### Task creation

An agent receives a fixed project, the natural user request, normal repository
guidance, and task guidance. It creates the appropriate task file or task
directory without implementing the product change.

Evidence includes task files, topology, requirements, dependencies, decisions,
questions, tool use, and effective instruction delivery.

### Fresh-agent planning

A new session receives a canonical task handoff but none of the first agent's
conversation. Two variants are compared:

- **Retained plan:** the task includes the Draft execution plan.
- **Omitted plan:** the task keeps requirements and supporting context but
  omits implementation direction and planned verification.

The fresh agent presents a plan without modifying files.

### Generated-task fresh-agent planning

A new session receives the exact task files produced by a task-creation run,
but none of that producer's conversation. It presents the implementation plan
without modifying files.

The assessment checks whether the generated task preserves:

- approved outcomes and constraints;
- implementation design and rationale;
- component responsibilities and important interfaces or data flow;
- dependencies, compatibility states, decisions, and unresolved questions;
- decisive testing and documentation boundaries;
- enough verified context to avoid broad rediscovery.

This evidence is required before claiming that agent-generated task files are
durable handoffs. Same-agent continuation cannot establish it because the
session still has the original conversation.

### Plan-to-task design preservation

For selected cases, the producer first presents a reviewed implementation
plan and then creates a retained-plan task. Semantic comparison checks whether
the task keeps the plan's architecture, boundaries, decisions, rationale,
dependency states, verification strategy, and exclusions rather than
collapsing them into ordered steps.

### Same-agent continuation

The task-creation session continues into plan presentation. This checks whether
the agent reuses its investigation and whether the durable task still contains
enough information to make the continuation reviewable.

### Incomplete-handoff negative control

One deliberately thin task omits supporting facts and unresolved questions.
It tests whether raw tool-call counts can look acceptable while the handoff
still loses material context or silently resolves public behavior.

## Evidence types

Evidence is kept separate:

- deterministic validity checks execution, instruction delivery, file capture,
  topology, dependencies, and structured record shape;
- semantic assessment judges outcome coverage, added scope, fragmentation,
  crossing ownership, handoff quality, design preservation, implementation
  design visibility, human-readable findability, duplication, and unsupported
  decisions;
- investigation metrics record reads, searches, diagnostics, mutations, and
  total tool calls;
- human review approves the test targets, candidate wording, interpretation,
  and promotion.

Fewer calls never compensate for an incomplete or incorrect plan.

## Model and effort matrix

Task creation uses:

- GLM-5.3-flash at max effort for all six test cases;
- GPT-5.6-luna at high effort for all six test cases;
- GPT-5.6-luna at xhigh and max effort for the three complex-decomposition
  test cases.

Fresh-agent and same-agent planning use:

- GLM-5.3-flash at max effort for the three bounded handoff cases;
- GPT-5.6-luna at high effort for the same three cases.

Semantic assessment uses one fixed high-quality evaluator prompt and the
reviewed target for each test case. A test case is not accepted by task count
alone.

The practical-baseline confirmation starts with a focused set:

- GPT high notes pagination, to ensure the implementation/test/documentation
  phase split remains eliminated;
- GLM max and GPT high book discovery, to compare vertical capability
  decomposition with the recurring server/client split;
- one high-effort author migration, to verify safe compatibility states;
- one reviewed plan-to-task chain followed by a fresh agent planning from the
  generated task.

Archive pagination and the multi-consumer case provide compact
nonregression coverage. Expand to the full matrix only if the focused set
leaves a material decision unresolved.

## Result reports

Every dated result report must:

- link this plan and the [test-case catalog](test-cases.md);
- use full linked stage and scenario names;
- state models, efforts, missing cells, retries, and invalid records;
- distinguish evaluator calibration from guidance behavior;
- report fragmentation, phase-only children, unjustified layer splits,
  evidence re-ownership, unsafe dependencies, and piecewise
  production-connection evidence separately;
- distinguish canonical-handoff, same-agent generated-task, and fresh-agent
  generated-task evidence;
- report implementation-design preservation, design visibility, and
  human-readable findability when those assessments are available;
- show score, affected-assessment count, and occurrence count, plus aggregate
  success for all records, each provider, and each provider/effort cohort;
- summarize useful passing outputs as well as failures;
- state what decision the evidence supports and what remains unproven.

Commands, result identities, raw-record locations, report generation, and
cell-level inspection are documented in
[Reproducing and inspecting results](reproducing-and-inspecting-results.md).