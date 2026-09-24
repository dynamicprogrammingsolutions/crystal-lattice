Parent Task:
tasks/20260728-package-local-documentation-standard/000-main.md

Depends On:

- `tasks/20260728-package-local-documentation-standard/015-agent-evaluation-framework.md`
- `tasks/20260728-package-local-documentation-standard/067-requirement-quality-model-effort-baseline.md`
- `tasks/20260728-package-local-documentation-standard/071-guidance-source-compilation-migration.md`
- `tasks/20260728-package-local-documentation-standard/080-maintainer-documentation-ownership-migration.md`

Scope split from:

- `tasks/20260728-package-local-documentation-standard/068-task-guidance-specification-alignment.md`
- `tasks/20260728-package-local-documentation-standard/069-task-guidance-scope-and-decomposition.md`

Specifications:

- `maintainer/agent-evaluation/suites/task_guidance/docs/development/specification.md`
- `maintainer/docs/development/specifications/crystal-lattice-guidance-integration/index.md`

Requirement IDs:

- Crystal Lattice guidance behavior: `DOCFLOW-007`–`DOCFLOW-009`
- Behavioral validation: `DOCVAL-014`
- Task-guidance evaluation suite: `TGEVAL-001`–`TGEVAL-011`

Human evaluation documentation:

- [Test plan](../../maintainer/docs/evaluations/task-guidance/test-plan.md)
- [Test cases](../../maintainer/docs/evaluations/task-guidance/test-cases.md)
- [Current-guidance baseline results](../../maintainer/docs/evaluations/task-guidance/20260919-current-guidance-baseline-results.md)
- [Task-mechanics candidate results](../../maintainer/docs/evaluations/task-guidance/20260919-task-mechanics-b1-results.md)
- [Reproducing and inspecting results](../../maintainer/docs/evaluations/task-guidance/reproducing-and-inspecting-results.md)

# Task-Guidance Handoff Baseline and Guidance Placement

Establish a reviewed task-handoff and decomposition baseline before deciding
where generic Requirements and Testing guidance belongs. Add staged
task-creation and continuation evidence, accept a safe task-workflow baseline,
then compare slight deduplication, system-message centralization, and an
optional routed-page design without changing guidance before baseline evidence
and explicit approval.

## Requirements checklist

- [ ] Task-file evaluation separates three bounded handoff scenarios from three
  substantially larger decomposition scenarios. The complex scenarios are
  broad enough to tempt ten or more phase- or layer-shaped subtasks but have a
  reviewed target of approximately four coherent deliverables.
- [ ] Each scenario defines a natural user request, approved outcomes,
  material decisions and questions, important test crossing, canonical plan,
  acceptable task topology, and retain-plan and omit-plan expectations before
  real-model execution.
- [ ] Independent stage matrices give every subject for one stage the same
  reviewed workspace, conversation prefix, task or plan input, current-stage
  prompt, guidance, model profile, and reasoning effort.
- [ ] Focused continuity tests separately cover same-agent planning and a
  fresh agent planning from task files without access to the first
  conversation.
- [ ] Fresh-agent evidence determines whether task files preserve the verified
  facts, source pointers, requirements, decisions, unresolved questions,
  exclusions, testing boundaries, and dependencies needed for a correct plan
  without broad rediscovery.
- [ ] Retain-plan handoffs preserve the approved plan semantically, while
  omit-plan handoffs preserve enough factual and decision context to support
  replanning without retaining implementation direction.
- [ ] A retained plan preserves the approved implementation design, rationale,
  component responsibilities, interfaces or data flow, dependency and
  compatibility states, material decisions and questions, and verification
  strategy rather than reducing the plan to ordered steps.
- [ ] Nontrivial execution plans make the implementation design recognizable
  to a human reviewer and a later agent. Ordered steps alone are not treated
  as a complete design, and plan depth remains proportionate to the work.
- [ ] Fresh-agent evidence includes planning from agent-generated task files,
  not only reviewed canonical handoffs, so the first conversation cannot hide
  missing durable design context.
- [ ] Task decomposition defaults to one task and uses a task directory only
  for independently reviewable working iterations or isolated
  responsibilities with real dependencies and explicit parent-requirement
  mappings.
- [ ] Complex decomposition evidence maps every produced subtask to a reviewed
  deliverable, identifies mergeable fragments, reports unmatched and overpacked
  work, and distinguishes actual subtask count from semantic deliverable
  count.
- [ ] Technical-layer boundaries are neither automatically accepted nor
  rejected. A frontend, backend, SDK, service, or package slice is separate
  only when completion leaves an independently usable, acceptable, deferable,
  owned, or reviewable result.
- [ ] Each complex target documents acceptable alternative partitions and why
  additional children would or would not add independent acceptance value;
  exact task count alone is not the quality judgment.
- [ ] Every important behavior crossing has a clear owner after decomposition;
  generic implementation, testing, documentation, review, and deployment
  phases do not become subtasks unless their result is independently required.
- [ ] Investigation-efficiency evidence records comparable tool calls, unique
  repository reads, broad searches, repeated reads, diagnostics, and
  mutations, and is interpreted only after plan quality passes.
- [ ] Efficiency thresholds are selected only after baseline variance is
  observed; a deliberately incomplete handoff may be used as a negative
  control.
- [x]
  [Stage B0 — Current-guidance baseline](../../maintainer/docs/evaluations/task-guidance/test-plan.md#stage-b0--current-guidance-baseline)
  records current behavior against the approved test cases before any
  task-guidance wording changes.
- [x]
  [Stage B1 — Task-mechanics candidate](../../maintainer/docs/evaluations/task-guidance/test-plan.md#stage-b1--task-mechanics-candidate)
  adds only evidence-backed task mechanics, handoff preservation, and
  decomposition rules, without redistributing generic Requirements or Testing
  guidance.
- [ ] The task-mechanics candidate materially improves the new
  handoff/decomposition behavior without materially reducing existing
  requirement completeness, important crossings, planning cleanliness,
  synchronization, or deterministic coverage.
- [ ] The practical task-mechanics baseline combines the demonstrated
  decomposition gains with concise plan-preservation, implementation-design,
  parent/child information-ownership, technical-layer, dependency, and
  production-connection clarifications, then receives focused confirmation
  before promotion.
- [ ] Root Requirements owns generic requirement derivation, traceability,
  grouping, approval, and record-role rules; root Testing owns generic
  evidence selection and boundary rules; TASKS owns task-file mechanics,
  approval, lifecycle, handoff, decomposition, and mapping those rules into
  the task requirement checklist and verification sections.
- [ ] Task guidance is self-contained for task-file mechanics. It may rely on
  generic Requirements and Testing guidance only when compilation/runtime
  verification proves those sections are present in the same effective
  instruction context.
- [ ] Placement candidates use the same semantic rule set so comparisons
  isolate placement and reinforcement rather than unrelated wording changes.
- [ ] The slight-correction candidate keeps concise completeness and evidence
  anchors in TASKS while removing avoidable repetition.
- [ ] The centralized candidate makes root Requirements and Testing the sole
  generic owners and leaves TASKS with short section-mapping reinforcement.
- [ ] An optional routed-page candidate retains essential rules in the
  effective system/developer message and uses shared pages only for examples,
  explanations, and extended guidance.
- [ ] Candidate evaluation starts with the sensitive requirement,
  decomposition, handoff, and crossing cases and expands to the full
  effort-aware matrix only after focused evidence passes.
- [ ] Deterministic findings, structured semantic assessment, empirical
  efficiency, pairwise review, and human acceptance remain separate evidence
  sources.
- [x] Semantic assessment separately scores fragmentation, phase-only
  children, unjustified layer splits, evidence re-ownership, unsafe
  dependencies, and piecewise production-connection evidence, with occurrence
  counts and aggregated success percentages by provider and effort.
- [ ] Current guidance is not replaced and current-status documentation is not
  updated until a candidate is explicitly approved.

## Scope and ownership

This task owns:

- the new task-guidance suite target and scenario contracts;
- three bounded handoff scenarios and three complex decomposition scenarios;
- the current-guidance baseline and task-mechanics candidate;
- fresh-agent and same-agent plan-continuation evidence;
- retain-plan and omit-plan preservation;
- quality-gated investigation-efficiency evidence;
- [Stage B2 — Guidance-placement confirmation](../../maintainer/docs/evaluations/task-guidance/test-plan.md#stage-b2--guidance-placement-confirmation),
  comparing concise task reinforcement, centralized root guidance, and
  optional routed extended explanation;
- the final recommendation and human-review package.

Subtask 068 retains canonical/bundled TASKS synchronization, specification/task
relationship history, and completed deterministic guidance work. Subtask 069
retains the completed requirement/testing candidate history and corrected
default-runner matrix. Their remaining staged-workflow and decomposition scope
is split into this task.

The task does not own implementation or completion-stage agent workflows until
task creation and planning handoffs are stable. It does not make detailed
guidance pages mandatory or select a final placement architecture before
evidence.

## Approved supporting facts

### Current guidance interaction

- The current portable root Requirements section is empty.
- The current root Testing section is approximately 142 words.
- Combined-v2 adds approximately 203 words of Requirements guidance and
  expands Testing to approximately 311 words.
- Current TASKS guidance is approximately 1,461 words and repeats generic
  requirement and verification rules alongside task-specific mechanics.
- Combined-v2 requirement completeness improves from 15/21 without TASKS to
  20/21 with TASKS.
- Combined-v2 scope score improves from 52.3 without TASKS to 81.0 with TASKS.
- Combined-v2 pairwise preference is 20–1 without TASKS and 14–7 with TASKS.
- TASKS therefore provides material completeness reinforcement while also
  introducing overlap and possible high-effort interaction.

Detailed evidence:

- `maintainer/docs/evaluations/documentation-guidance/20260918-default-runner-results.md`
- `maintainer/agent-evaluation/suites/documentation_standard/fixtures/results/compiled_guidance_default_runner_20260918_results.json`
- `maintainer/agent-evaluation/suites/documentation_standard/fixtures/results/compiled_guidance_default_runner_20260918_analysis.json`

### Baseline sequence

```text
Committed corrected evaluator
→ Stage B0 — Current-guidance baseline
→ Stage B1 — Task-mechanics candidate
→ Stage B2 — Guidance-placement confirmation
→ full confirmation for the selected candidate
```

The current-guidance baseline may expose quality failures but must produce
structurally valid, interpretable evidence. The task-mechanics candidate does
not aim for perfect behavior; it establishes a safe, reviewable baseline for
task handoff and decomposition before generic guidance ownership changes.

### Guidance placement hypotheses

All candidates share one approved semantic rule set.

- **Concise task reinforcement:** root Requirements and Testing contain the full
  generic rules; TASKS retains concise reminders to preserve every approved
  condition and map task requirements to decisive evidence.
- **Centralized root guidance:** root Requirements and Testing are the sole generic
  owners; TASKS maps those rules into `## Requirements checklist`,
  `### Requirement verification`, and optional additional verification.
- **Routed extended explanation:** essential rules remain in the effective
  instruction, while root and TASKS guidance route nontrivial work to shared
  requirement/testing pages containing examples and extended explanation.

Centralized root guidance is the recommended target architecture if concise
task reinforcement proves that reminders can be reduced safely. Routed
extended explanation remains optional and must not move essential rules
exclusively into ordinary workspace pages.

## Decisions and open questions

Approved:

- Use one coordinating subtask rather than a new nested task directory.
- Reuse the three pinned projects for bounded handoff cases and derive or
  select richer, fixed project states for the complex decomposition cases.
- Test decomposition quality as coherent partitioning of large work rather
  than primarily as a one-task-versus-directory choice.
- Include one vertical full-stack scenario where automatic frontend/backend
  splitting is fragmentation, one multi-consumer scenario where component or
  layer boundaries are independently deliverable, and one compatibility
  migration organized around working states.
- Use independent stage matrices plus focused continuity chains rather than a
  full cross-product of variable upstream outputs.
- Compare efficiency only within the same model and effort and only after
  semantic plan quality passes.
- Preserve current guidance in the current-guidance baseline before accepting
  the task-mechanics candidate.
- Treat the three descriptive placement designs as controlled variants in
  guidance-placement confirmation.
- Treat task-mechanics candidate v1 as strong positive decomposition evidence,
  not as a wording set that must be either promoted verbatim or discarded.
- Replace the earlier all-or-nothing nondegradation interpretation with a
  risk-weighted practical-baseline decision: the absence of decomposition
  guidance on `develop` is a major known defect, while narrow, understood
  production-connection or handoff variation can remain tracked follow-up
  work when approved outcomes and task validity remain complete.
- Before promotion, add concise guidance that preserves implementation design
  through plan-to-task handoff, distinguishes a design from an ordered step
  list, assigns shared design to the parent and local design to children, and
  clarifies that testability alone does not make a technical layer an
  independent delivery.

Open during baseline execution:

- Exact acceptable alternative partitions after the complex fixtures and
  reviewed canonical plans are finalized.
- Exact task-mechanics candidate wording after the current-guidance baseline
  exposes current behavior.
- The first model/effort cohort and which sensitive cases receive GPT xhigh.
- The efficiency threshold after the current-guidance baseline establishes
  variance.
- Whether routed extended explanation is justified after the two compiled
  instruction designs are compared.
- Final destinations and compiler ownership for optional detailed pages.
- Exact practical-baseline wording and whether one focused confirmation pass
  exposes a failure requiring another small correction.

## Execution plan

Status: Draft

### 1. Establish durable targets and scenario contracts

Finalize the suite specification, requirements, testing strategy, three
bounded handoff contracts, and three complex decomposition contracts. Complex
targets define coherent deliverables, acceptable alternative partitions,
mergeable fragmentation, crossings, and when a technical layer is or is not
independently deliverable.

### 2. Migrate and normalize the task-guidance evaluator

Move the existing human-operated task-guidance evaluation from
`test/task_guidance/` into the package-owned suite while preserving real-model
execution, deterministic assertions, empirical review, provenance, imported
sessions, review bundles, and canonical/raw evidence boundaries. Reuse
`agent_eval` for workspace, cache, continuation, and artifact behavior.

### 3. Implement independent stage and continuity evidence

Add canonical task-creation and plan-preparation stage inputs. Add focused
same-agent and fresh-agent continuations, retain/omit plan variants, task-tree
normalization, semantic target coverage, deliverable mapping, mergeability and
fragmentation evidence, dependency checks, crossing ownership, and
investigation-efficiency telemetry.

### 4. Run Stage B0 — Current-guidance baseline

Run current guidance unchanged. Preserve exact guidance, project, prompt,
model, effort, stage input, and output hashes. Calibrate validity checks,
semantic targets, and descriptive efficiency evidence without changing
guidance to make failures pass.

### 5. Define and verify Stage B1 — Task-mechanics candidate

Use current-guidance baseline failures to add the shortest task-specific
handoff and decomposition rules. Preserve candidate v1 as completed evidence,
then create a practical-baseline revision that keeps its decomposition gains
and adds only the focused corrections established by review:

- a retained plan preserves the actual implementation design and rationale;
- a nontrivial execution plan explains component responsibilities,
  interfaces or flow, compatibility and dependency states, material
  decisions, and verification strategy before execution checkboxes;
- the parent owns shared end-to-end design and crossing evidence while
  children own local design and evidence without duplicating shared context;
- testability or reviewability alone does not make a technical layer an
  independent delivery;
- separate side-specific tests do not prove a required production connection;
- every dependency-permitted intermediate state remains usable and
  compatible.

Add focused evidence for generated-task-to-fresh-agent continuation,
plan-to-task design preservation, implementation-design visibility, and
human-readable findability. Run a bounded confirmation set before promotion;
do not require another full calibration matrix unless the focused evidence
finds a material uncertainty.

### 6. Run Stage B2 — Guidance-placement confirmation

Compile concise task reinforcement, centralized root guidance, and, if
justified, routed extended explanation from the same semantic rule set. Run
focused sensitive cases first. Preserve paired provenance and grow wording
only when a demonstrated failure requires it.

### 7. Confirm and present

Run the full justified effort-aware matrix for the selected candidate. Freeze
producer, semantic, pairwise, efficiency, and human-review evidence. Present a
concise acceptance package and wait for explicit approval before promoting
guidance.

### Implementation decisions and open questions

- The user approved this plan and the revised complex-decomposition direction
  on September 19, 2026.
- The current-guidance baseline is observational; new quality assertions may
  fail without invalidating it.
- Candidate v1 is preserved as evidence and is not promoted verbatim. The
  revised practical-baseline plan is Draft and no additional model work starts
  until the user authorizes it.
- A producer or evaluator record is valid only when execution, capture,
  instruction delivery, and structured-output checks pass. Behavioral quality
  failures remain evidence.
- Efficiency is a secondary comparison after quality. No candidate may pass by
  omitting investigation or plan content.
- The three placement designs share semantics; placement is the tested
  variable.
- A detailed-page candidate keeps essential rules in the compiled instruction.

### Documentation

- Task-guidance suite docs and specification
- Crystal Lattice guidance-integration specification and requirements
- Three bounded handoff and three complex decomposition contracts with
  reviewed semantic targets
- Running and calibration guide
- current-guidance baseline, task-mechanics candidate, placement, and final
  dated evaluation reports when evidence exists
- Current-guidance status only after an accepted promotion

### Task checklist

- [x] Approve the execution plan and complex-decomposition direction.
- [x] Finalize the six scenario contracts and acceptable partitions.
- [x] Finalize `TGEVAL-*`, `DOCFLOW-*`, and `DOCVAL-014` mappings.
- [x] Migrate the existing task-guidance evaluator into the package-owned suite.
- [x] Implement canonical independent stage inputs.
- [x] Implement fresh-agent and same-agent continuations.
- [x] Implement retain-plan and omit-plan stage fixtures and capture.
- [x] Implement task topology, coherent-deliverable mapping, mergeability,
  fragmentation, parent mapping, dependency, and crossing evidence.
- [x] Implement quality-gated efficiency evidence and negative control.
- [x] Run and freeze the GLM portion of the current-guidance baseline.
- [x] Complete the GPT current-guidance baseline cells after the account limit
  cleared, retaining one explicit invalid same-agent upstream.
- [x] Publish the dated combined current-guidance baseline interpretation and
  preserved evidence.
- [x] Approve the shortest task-mechanics candidate direction.
- [x] Add the explicit semantic issue metrics and rescore current guidance.
- [x] Compile and inspect task-mechanics candidate v1.
- [x] Run task-mechanics candidate v1 across the complete producer, handoff,
  continuation, negative-control, and semantic matrix.
- [x] Review the generated task files and evaluator boundaries rather than
  relying only on aggregate scores.
- [x] Revise the candidate decision: preserve v1 as strong decomposition
  evidence, do not promote it verbatim, and use it as the basis of a practical
  baseline instead of leaving `develop` without decomposition guidance.
- [ ] Draft the practical-baseline wording for plan preservation,
  implementation-design visibility, parent/child information ownership,
  technical-layer independence, safe dependencies, and decisive crossings.
- [ ] Add the focused generated-task fresh-agent, plan-preservation,
  implementation-design, and human-readability assessments.
- [ ] Run the focused practical-baseline confirmation and inspect the actual
  generated task files and reconstructed plans.
- [ ] Freeze and promote the practical task-mechanics baseline after explicit
  approval.
- [ ] Compile and inspect concise task reinforcement and centralized root
  guidance; compile routed extended explanation only if justified.
- [ ] Run focused placement comparisons.
- [ ] Select one candidate for full confirmation.
- [ ] Run the final model/effort matrix.
- [ ] Prepare concise human review and request promotion approval.
- [ ] Update requirement evidence and append completion notes only after
  acceptance.

### Requirement verification

| Requirement group | Acceptance evidence |
|---|---|
| Scenario and target quality | Approved contracts define natural prompts, outcomes, plans, crossings, and handoff expectations without teaching the partition; complex targets define approximately four coherent deliverables plus acceptable alternatives and fragmentation examples. |
| Independent stage comparability | Every subject for a stage receives the same hashed stage input; output from one tested subject is not silently used as another subject's prerequisite. |
| Fresh-agent handoff | A fresh agent reconstructs a semantically complete plan from task files alone, preserves decisions/questions/exclusions, and avoids broad rediscovery. |
| Same-agent continuation | Continued planning reuses prior investigation and meets the same semantic target with no more investigation than the comparable fresh-agent handoff. |
| Retain/omit plan behavior | Retained plans preserve approved implementation direction; omitted plans preserve facts and constraints without retaining plan steps. |
| Plan design preservation | A reviewed implementation design remains recognizable after task creation: component responsibilities, interfaces or flow, compatibility/dependency states, decisions, and verification strategy are not collapsed into an ordered checklist. |
| Generated-task handoff | A fresh agent receives an agent-generated task without the first conversation and can present the same essential design without broad rediscovery or invented decisions. |
| Human readability | A reviewer can find the outcome, planned design, responsibility boundaries, dependencies, open questions, and decisive evidence from the parent and owning children without following duplicated or scattered context. |
| Task topology | Bounded cases preserve proportionate handoffs; complex cases map actual children to coherent deliverables, expose mergeable phase/layer fragments, preserve parent mappings and acyclic real dependencies, and accept layer-shaped children only when independently deliverable. |
| Crossing ownership | Eleventy build/output, FastAPI route/storage, and Flask/Vue client/transport/server crossings remain owned and verifiable after task decomposition. |
| Efficiency | Quality-passing continuation runs record and compare normalized investigation effort; thresholds are derived from the current-guidance baseline rather than selected in advance. |
| Safe baseline | The task-mechanics candidate improves new handoff/decomposition behavior without material regression in existing requirement completeness, important crossings, synchronization, or deterministic verification. |
| Placement comparison | Concise task reinforcement, centralized root guidance, and optional routed extended explanation share the same semantic rules and differ only in placement/reinforcement; paired evidence identifies effects in root-only and task modes. |
| Promotion | No guidance source changes until complete focused/full evidence and explicit human approval support one candidate. |

### Additional implementation verification

- Run task-guidance parity and compiler checks after every candidate change.
- Run the common Crystal Lattice message/tool preflight for every model-family
  profile used by the suite.
- Preserve old CLI artifact readability or provide an explicit migration path.
- Keep credentials and authentication state out of run artifacts.
- Verify frozen evidence regenerates deterministically.
- Keep current documentation/status pages unchanged until promotion.

## Implementation Notes

- September 19, 2026: Committed the approved plan and six revised scenario
  contracts in `094cf20f`. The scenario set now contains three bounded handoff
  cases and three complex decomposition cases targeting approximately four
  coherent deliverables rather than a one-versus-two task decision.
- Migrated the existing task-guidance CLI, harness, assertions, review tooling,
  tests, and Codex fixture from root `test/` into the package-owned suite.
  The original migrated boundary passed 32 deterministic tests; the expanded
  suite subsequently added machine-readable targets, compact project
  fixtures, production-path runner preflights, task-tree capture, semantic
  assessment, canonical handoffs, continuation, and consolidation tooling.
- The first parallel provider sentinel exposed a path-plugin wheel-build race
  because GPT and GLM tried to build the same source package concurrently.
  A serialized GLM retry passed the plugin boundary. Provider caches must be
  warmed serially before parallel model work.
- GPT reached the production ChatGPT provider path with correct Codex tools,
  one compiled fixture `AGENTS.md`, and one TASKS copy, but the account returned
  `usage_limit_reached` (`429`). That record is invalid setup evidence and is
  excluded from semantic scoring.
- The first successful GLM sentinel produced a valid task but found missing
  FastAPI fixture infrastructure. The fixture omitted app assembly, database
  definitions, and CRUD routes that the prompt said must remain compatible.
  Fixture version `v2` adds the claimed runnable architecture across all three
  project families. The sentinel is retained as runner validation but excluded
  from the canonical current-guidance baseline.
- Six GLM-max fixture-v2 current-guidance baseline producer processes started
  in parallel under run
  attempt `b0-r1`. Full GPT evidence remains blocked by account usage limits;
  any interim GLM-only semantic report must be explicitly labeled partial.
- Calibration completed compact project fixtures through suite version `v5`.
  Pre-final runs exposed missing FastAPI lifecycle/CRUD infrastructure,
  incomplete Flask/Vue harnesses, and missing Eleventy collection/layout
  wiring. Those outputs remain calibration evidence and are excluded from the
  frozen baseline by fixture hash and attempt identity.
- The final producer and handoff attempt is `b0-v5-r1`. Six GLM-max producer
  cells, six fresh-agent retain/omit plans, three same-agent continuations, and
  one incomplete-handoff negative control are valid.
- Semantic calibration removed one hidden target condition, excluded
  coordinating `000-main.md` files from implementation-task counts, required
  named checks through exact production crossings, and compared the negative
  control with complete handoffs. Semantic schema version 2 rescored the
  combined GLM/GPT baseline under attempt `b0-metrics1`.
- Eight-way semantic execution exposed recursive artifact scanning through
  transient workspaces. Record discovery now reads only targeted
  `profile/runs/run-id/records/` paths; the two affected cells were rerun
  successfully.
- The rescored current-guidance baseline has 18/18 approved-outcome coverage
  and a 67.4% aggregate task-quality score. The six dimension scores are:
  fragmentation 68.5%, phase-only children 50.0%, unjustified layer splits
  72.2%, evidence re-ownership 58.3%, dependency safety 75.0%, and
  production-connection evidence 80.6%.
- Retained plans reduce fresh-agent calls in
  [Scenario TG-02 — FastAPI notes pagination as one task](../../maintainer/docs/evaluations/task-guidance/test-cases.md#scenario-tg-02--fastapi-notes-pagination-as-one-task)
  and the selected-filter case but not
  [Scenario TG-01 — Eleventy archive pagination as one task](../../maintainer/docs/evaluations/task-guidance/test-cases.md#scenario-tg-01--eleventy-archive-pagination-as-one-task).
  Same-agent planning uses two calls in every case. The notes-pagination
  incomplete
  handoff uses nearly the same calls as a complete omit handoff while losing
  an approval question, confirming that efficiency must remain quality-gated
  and that no numeric threshold is yet justified.
- The production ChatGPT-login sentinel initially delivered the normal Codex
  system/tool/task context and returned `429 usage_limit_reached`. The later
  retry cleared the account limit and completed all planned GPT producer and
  fresh-agent cells.
- One GPT-max producer initially returned no task files and passed a focused
  retry under the same canonical attempt. One semantic evaluator response
  omitted a subject and passed a focused retry.
- Same-agent continuation now rejects an invalid parent before planning. GPT
  archive and notes-pagination chains are valid; the GPT selected-filter chain
  repeatedly produced no parent task file and remains an explicit invalid
  upstream record rather than being retried away.
- The complete matrix contains 18 valid task-creation cells, 12 valid
  fresh-agent plans, five valid same-agent continuations, one invalid
  same-agent upstream, six task semantic batches, and three handoff semantic
  batches. Approved-outcome coverage is 18/18; important production-connection
  evidence is complete in 13/18 producer assessments.
- September 20, 2026: task-mechanics candidate v1 was compiled as an overlay
  that changes only task guidance. Its complete matrix is frozen under
  producer and handoff attempt `b1-v1-r1` and semantic attempt
  `b1-metrics1`.
- Candidate v1 improves aggregate task quality from 67.4% to 87.0%, eliminates
  all phase-only and evidence-reownership findings, and reduces fragmentation
  occurrences from 19 to 6. The initial interpretation withheld acceptance
  because production-connection evidence scored 80.6% to 75.0%, several
  handoff semantic scores regressed, and the GPT selected-filter same-agent
  failure remained.
- September 20, 2026: manual review revised that decision threshold. The
  production-connection affected-assessment and occurrence counts both remain
  five, all 18 candidate task sets preserve approved outcomes, and the
  fresh-agent comparison uses reviewed canonical handoffs rather than
  candidate-generated task files. Candidate v1 therefore provides strong
  evidence for urgently adding decomposition guidance, while its crossing and
  handoff findings remain targeted correction work rather than justification
  for keeping the current guidance unchanged.
- The next proposed deliverable is a practical baseline, not a search for a
  perfect candidate. It retains the v1 decomposition rules, clarifies
  technical-layer independence, dependencies, and connected evidence, and
  adds concise rules for preserving implementation design, keeping shared
  architecture in the parent, avoiding parent/child duplication, and making a
  nontrivial plan more than an ordered step list. No implementation or model
  run has started for this revision.
- Durable interpretation:
  `maintainer/docs/evaluations/task-guidance/20260919-current-guidance-baseline-results.md`.
  Candidate interpretation:
  `maintainer/docs/evaluations/task-guidance/20260919-task-mechanics-b1-results.md`.
  Durable result packages (the frozen dataset copies under suite fixtures
  were removed by task 095 after parity was proven):
  `maintainer/docs/evaluations/task-guidance/results/20260919-current-guidance-b0/`
  and
  `maintainer/docs/evaluations/task-guidance/results/20260919-task-mechanics-b1/`.