# Task-file quality coverage

Parent Task:
tasks/20260728-package-local-documentation-standard/000-main.md

Depends On:

- `tasks/20260728-package-local-documentation-standard/090-task-guidance-handoff-baseline-and-placement.md`
  (owns task-guidance wording, scoring, and promotion; this subtask adds the
  quality coverage its remaining checklist item requires)
- `tasks/20260728-package-local-documentation-standard/100-task-guidance-suite-restructure.md`
  (completed: the suite's stage catalog, scenario/effort configuration,
  per-subject assessment machinery, and result packages used here)

Coordinates with:

- `tasks/20260728-package-local-documentation-standard/110-run-exact-freeze-collect.md`
  (owns the run-model and freeze layers any new stage records flow through)

## Description

Six real-world task-file quality gaps are not covered by the current
task-guidance evaluation: execution plans that degenerate into work steps,
task files that are hard for humans to read, files that drop material
detail from the conversation plan, ambiguous section placement, execution
plans invented without planning, and non-development tasks forced through
development-shaped sections. This subtask adds coverage for all six:
semantic dimensions that assert positive completeness properties, a few
deterministic profile metrics that report structure without banning shapes,
new scenario kinds, and a fresh-agent-from-generated-task stage that
measures whether model-written files preserve enough context for a new
agent.

## Requirements checklist

- [ ] Task-file quality is assessed per subject with semantic dimensions
  phrased as positive completeness checks — design completeness of the
  execution plan, durable-context preservation from the conversation,
  findability for a human reviewer, section appropriateness, plan
  justification (no invented plans), and task-kind fit — each with a few
  ordered grades, not mechanical bans.
- [ ] The assessment prompt stays identity-blind for the producing model
  and effort, matching the existing per-subject assessments.
- [ ] A deterministic structure profile is computed for every produced task
  file (heading depth, subheading density, list-item lengths, paragraph
  lengths, plan prose-to-checklist shape, file-versus-conversation plan
  size ratio) and lands in the frozen dataset and result packages as
  reported metrics with no pass/fail gates of their own.
- [ ] Profile thresholds, if any are turned into assertions later, are
  selected only after baseline variance is observed across the committed
  baseline and candidate packages.
- [ ] A fresh-agent planning stage runs from generated task files (not
  canonical handoffs) for at least the planning-scenario cells, judged by
  the existing handoff rubric so dropped detail surfaces as lost facts,
  plan-coverage gaps, or broad rediscovery.
- [ ] New scenario kinds cover a task file requested without a planning
  request, a documentation task, an operations/deployment task, and a
  content/copywriting task, each with a reviewed target declaring its
  applicable sections and the acceptance evidence appropriate to its kind.
- [ ] The no-planning scenario asserts that an execution plan is either
  absent or explicitly marked as not-yet-made with what remains unresolved.
- [ ] Every new scenario runs through the standard producer validity
  checks and the per-subject assessment path used by the existing matrix.
- [ ] Guidance wording addressing the six gaps is drafted as a candidate
  extending the promoted practical baseline once promotion lands, not
  directly into current guidance.
- [ ] The suite's deterministic tests cover the new analyzer, the new
  stage wiring, and the new scenario configuration.

## Supporting details

Gap-to-dimension mapping (each gap needs at least one semantic dimension;
deterministic metrics support but never replace them):

1. Steps-instead-of-design → `plan_design_completeness` (already partially
   addressed by the v3 design-visibility rule; the dimension scores it).
2. Poor readability → `findability` (already defined by task 090's
   human-readability acceptance row; never scored until now).
3. Dropped detail → `durable_context_preservation` on the producer side,
   plus the fresh-agent-from-generated-task stage as behavioral proof.
4. Placement ambiguity → `section_appropriateness` (outcomes in
   requirements, rationale and learned facts in supporting details,
   direction in the plan, unresolved items in questions).
5. Invented plans → `plan_justification` with the fabricated grade, plus
   the no-planning scenario's deterministic absence-or-draft assertion.
6. Forced development shape → `task_kind_fit` with the three new
   non-development scenario kinds.

Design constraints inherited from the suite restructure: stages are
declared in the stage catalog and configuration manifest; tests and
fixtures carry no candidate or target names; env vars only select
directories and connections; the matrix command set stays unchanged.

## Implementation Notes

- September 26, 2026: the deterministic structure profile
  (`suites/task_guidance/structure.py`) is implemented with unit tests on
  synthetic files exhibiting each failure mode (7 tests). Calibration over
  the committed packages (18 producer cells each; per-file ranges):
  - baseline: 8 of 72 files without an execution plan, 8 without any
    subsection, paragraphs up to 296 words, sections up to 633 words —
    the prose-wall and missing-plan failure modes are real in the baseline.
  - candidates: every task-mechanics file carries a plan and subsections;
    the largest paragraph shrinks to 105–210 words — the v3
    design-visibility rule visibly reshaped plan structure.
  - open signals even under v3: `plan_prose_share` still reaches 0 in
    checklist-only plans, and tables are nearly absent (v2: zero table
    rows across 53 files; v3: 2 of 50 files use any).
  These ranges are facts, not gates; nothing asserts them yet.
- September 26, 2026 (continued): the task-quality-assessment stage is
  wired end-to-end — identity-blind per-subject prompt
  (`suites/task_guidance/quality.py`, six positive dimensions), stage
  catalog and configuration entries, matrix cases, the live driver, the
  freeze dataset (`quality_records`, `quality_summary`, status), and
  package collection (sessions, results pages, template export,
  assessment details with grades; no numeric scores are derived).
- The generated-plan stage is wired end-to-end: a fresh fixture-project
  workspace rebuilt from one producer run's written task files
  (`GeneratedTaskWorkspaceFactory`), a fresh-session planning turn whose
  cache identity includes the producing run's identity, a live driver
  that re-produces the parent first, freeze integration
  (`generated_plan_records` + status), and judgment by the existing
  handoff rubric through a new `generated-file` handoff subject variant.
  Matrix collection grows to 104 cases (6 generated-plan, 18 quality
  assessment); the deterministic suite is 173 tests, green.
- Note: until the new scenarios land, the generated-plan stage runs for
  the three handoff-category scenarios (6 cells); decomposition
  scenarios can join by declaring the stage in their category.

## Execution plan

Status: Approved

Approved by the user on September 26, 2026 together with the direction
"start the implementation".

1. Build the deterministic task-file structure profile module plus unit
   tests (synthetic files exhibiting each failure mode; committed packages
   as calibration corpus).
2. Run the profile over the committed baseline, v2, and v3 packages and
   record observed ranges as supporting facts (no gates).
3. Add the task-file quality assessment stage: identity-blind per-subject
   prompt with the six dimensions, wired like the existing task-creation
   assessment (stage catalog, evaluation driver, records, freeze, package
   collection, matrix views).
4. Add the fresh-agent-from-generated-task stage: reuse the handoff plan
   machinery with the generated task file as input; judge with the
   existing handoff rubric; wire it for the planning scenarios.
5. Add the four new scenarios (no-planning, documentation, ops/deployment,
   copywriting) with reviewed targets, and the no-planning deterministic
   assertion in its producer validity checks.
6. Extend the suite's deterministic tests: analyzer unit tests, stage
   wiring tests, scenario configuration tests, and package-view tests.
7. Draft the guidance candidate addressing the six gaps (extends the
   promoted practical baseline; wording drafted, compiled, and
   compile-checked only — running the new coverage happens after
   promotion, on the next candidate cycle).
8. Update the task-guidance test-plan and test-cases documentation for the
   new stages and scenario kinds.

### Implementation decisions and open questions

- The quality assessment is a separate stage rather than extra dimensions
  on the decomposition assessor, so each prompt keeps a single judgment
  task and the existing matrices stay comparable.
- The fresh-agent stage targets the planning scenarios first (tg01–tg03
  style single-task scenarios); decomposition scenarios can be added later
  by feeding the parent task file.
- Non-development scenarios use two model cells (GLM max, GPT high) to
  keep the added cost negligible.
- Open: whether `plan_design_completeness` replaces or joins the existing
  `piecewise_crossing_evidence` view of plans — resolved while writing the
  rubric; initial decision: separate dimension, joined only in reporting.

### Documentation

- Suite test-plan and test-cases pages gain the new stages and scenario
  kinds.
- The task-guidance evaluations index gains the quality-coverage direction
  when the first results land.
- This task file records implementation and completion notes.

### Task checklist

- [x] Structure-profile module with unit tests
- [x] Calibration run over committed packages recorded
- [x] Quality-assessment stage wired end-to-end
- [x] Fresh-agent-from-generated-task stage wired end-to-end
- [ ] Four new scenarios with reviewed targets
- [x] Deterministic suite tests for all of the above
- [x] Live coverage results generated and packaged (September 26, 2026:
  18 quality subjects, 6 generated-file plans all valid, 6 generated-file
  handoff subjects — see the
  [coverage results](../../maintainer/docs/evaluations/task-guidance/20260926-task-quality-coverage-results.md);
  two fabricated plans and two missing-acceptance flags, both in
  book-discovery GPT cells)
- [ ] Guidance candidate drafted and compile-checked
- [ ] Suite documentation updated

### Requirement verification

- Semantic dimensions: per-subject assessment records in a frozen dataset
  and a collected result package render with all six dimensions and
  identity-blind inputs.
- Deterministic profile: unit tests on synthetic files plus a recorded
  calibration range across the committed packages.
- Fresh-agent stage: at least one scenario's generated-task plan runs and
  is judged by the existing rubric through the public matrix command.
- New scenarios: producer runs valid through the standard matrix command
  with the no-planning assertion enforced.
- Guidance candidate: compile check passes; no promotion performed here.

### Additional implementation verification

- Full deterministic suite tests pass; ruff/black clean on touched files.
