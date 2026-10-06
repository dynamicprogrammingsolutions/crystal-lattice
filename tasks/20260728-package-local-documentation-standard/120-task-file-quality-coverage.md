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
- [x] Guidance wording addressing the six gaps is drafted as a candidate
  extending the promoted practical baseline once promotion lands, not
  directly into current guidance. (DONE September 27, 2026: candidate
  `task-mechanics-b1v4`, see Implementation Notes.)
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
- Note: the generated-plan stage runs for the three handoff-category
  scenarios (6 cells); decomposition and kind scenarios can join by
  declaring the stage in their categories.
- September 26, 2026 (follow-up A+B executed): the result-package
  export was reorganized around producer cells and every number moved
  next to its evidence. Producer and stage runs export one directory
  per sample (`<cell>/s<N>/`, `<cell>/<stage>/s<N>/`); sample
  directories come from the run model's own sample index, with valid
  records claiming their index first and invalid re-runs filling free
  indexes so judgments stay beside the evidence they judge. Invalid
  samples export `invalid.md` (category — validity vs provider
  failure, run label, recorded reasons, response excerpt); the
  generated-plan stage finally exports its sessions and task files in
  the cell subtree. Per-subject assessments moved under the judged
  cell (`<cell>/assessment/<stage>/…`), each judged sample gained
  `assessment.md` (all stages' grades for that subject, linked both
  ways), each scenario gained `results.md` (producer samples with
  task-creation overall + quality grades; plan stages with handoff
  scores; invalid links), and `matrix.md` gained the task-file-quality
  cohort and per-judgment detail tables plus a split of invalid
  records into validity failures vs provider failures. Frozen datasets
  predating later scenarios now collect only the scenarios they hold.
  Both current evidence packages were re-collected with the new
  layout and pass the package check; the older historical packages
  (b0, b1, b1v2, b1v3) keep their committed layout as historical
  record. Deterministic suite: 175 tests green (two new tests cover
  the invalid-sample export and the quality-judgment co-location).
- September 26, 2026 (kind baseline): the four scenarios' first v3 run
  caught two flaky producer failures — the content task triggered a new
  ask-and-stop about *whether to include an execution plan* (tg10 GPT,
  1/3 samples) and the tracking task produced a filled plan despite an
  explicit deferral (tg07 GLM, 1/3, rejected by the new assertion).
  Both point at the same missing wording: the execution plan is
  conditional. All valid subjects fit their kind (10/10) and judged
  plans `justified` or `not_applicable`; assessments use valid samples
  only, invalid samples stay as producer-side variance evidence.

- September 27, 2026 (guidance candidate b1v4 drafted): the candidate
  extends the promoted v3 baseline with nine wording changes mapped to
  the six gaps, the Layer 1 plan-content findings, and the September 27
  amendment directions: `- September 27, 2026 (infrastructure item 1 DONE — provider switch +
  minimal configs): `fixtures/runtime/glm.json` shrank 24.6KB→3.6KB and
  `gpt.json` 24.6KB→5.4KB; both now carry exactly the used providers
  (glm: ollama+zai; gpt: openai), the referenced mixins, the exact plugin
  lists, and a minimal application config (env_file + provider_env_keys)
  — all unused providers, gemini/grok/kimi/qwen/cloud mixins, MCP
  defaults (inlined as agent flags), and the cloud-agent/notification
  application sections are gone. GLM defaults to zai
  (`https://api.z.ai/api/coding/paas/v4`, model `glm-5.3-flash`); the
  provider connection is SELECTABLE per `agent_config_file`:
  `TASK_GUIDANCE_GLM_PROVIDER` (zai|ollama) picks the provider + its
  per-provider model from configuration.json's new `providers` map,
  `TASK_GUIDANCE_GLM_MODEL` overrides the model, and
  `ZAI_OPENAI_BASE_URL`/`OLLAMA_OPENAI_BASE_URL` override base URLs.
  Verified by real end-to-end smokes through the suite environment
  machinery: zai default (`provider=zai model=glm-5.3-flash
  response='OK'`) and ollama selection (`provider=ollama
  model=glm-5.3-flash:cloud response='OK'`). 219 deterministic tests
  green (6 new selection tests). Diagnosis note: a smoke that sends
  via `send_request` without a user message yields z.ai 400/1214 —
  the production entry is `context.request(messages=...)`.

- September 27, 2026 (infrastructure item 3 DONE — interleaved-thinking
  plugin): new first-party plugin `plugins/interleaved-thinking`
  (provider extension, tagged `provider:openai_compatible`) strips
  previous-turn thinking from outgoing requests in both forms —
  `<think>...</think>` segments from assistant content (inline form,
  e.g. Ollama) and `reasoning`/`reasoning_content` fields (separate-field
  form, e.g. Z.ai GLM) — including multipart text parts and trailing
  unterminated blocks. Session history is untouched; only the request
  payload changes. Plugin present = prior thinking omitted (switch off);
  absent = provider default (switch on; note the reference provider
  already drops field-based reasoning when building requests, so on zai
  the two positions differ only for content-embedded thinking — the
  D-arm pruning rule covers any no-variance case). 9 unit tests; real
  two-turn zai e2e with the plugin loaded passed (both turns completed,
  final response correct). plugins/docs/index.md lists the plugin.

- September 27, 2026 (infrastructure items 2+4 DONE — shared recipes +
  parallel runner): all ten live-test case recipes moved verbatim into
  `evaluation/execution.py` (producers, dependent stages, and the five
  assessments, uniform `(harness_factory, run_label, options, case)`
  signature; assessments raise `CaseSkipped` instead of pytest.skip);
  every parametrized live test is now a thin wrapper over the same
  function, so the pytest path and the CLI path share one recipe. New
  CLI `python -m suites.task_guidance.run`: one command for the whole
  evaluation or any slice (--stages/--scenarios/--agents,
  dependency-ordered stage groups: producers → dependent stages →
  assessments), per-agent maximum parallelism from a JSON config
  (`--parallelism`, default serial per agent with cross-agent
  concurrency), live per-case outcomes (. ok, s skipped, F failed),
  non-zero exit on any failure, and --dry-run. Verified: the CLI
  enumerates exactly the same 179 cases as the pytest live matrix;
  228 deterministic tests green (9 new runner tests cover stage
  ordering, slicing, parallelism config validation, and
  skip/fail outcome reporting); ruff+black clean. The runner is
  documented in the reproducing-and-inspecting results page. All four
  prerequisite infrastructure items are now DONE (provider switch +
  minimal configs, interleaved-thinking plugin, shared recipes +
  parallel runner); the remaining gate before evaluation runs is the
  candidate review/promotion decision plus the D-stage build.

- September 27, 2026 (D started — subtask created): the non-lossy
  two-stage pipeline now has its own subtask file
  `tasks/20260728-package-local-documentation-standard/125-two-stage-pipeline.md`
  with the full concrete plan. Favorable mechanics verified while
  scoping: fixture guidance targets compile AGENTS.md with NO tasks
  slot, so the tasks guidance reaches the agent only through the
  per-request `include_tasks` flag (already used by assessments) — the
  guided/unguided arms reduce to that flag, the writing turn always
  compiles with it on, and preserve-thinking is the
  interleaved-thinking plugin in an agent-config variant. GPT
  limitation recorded: the plugin requires the openai-compatible
  provider, so preserve-thinking variants are GLM-only.

- September 29, 2026 (run scope approved): b1v4 is approved FOR
  EVALUATION ONLY — do not promote it over `current` (b1v3) yet. After
  the new tests (subtask 125 D stages) and all infrastructure changes
  are complete, retest ONLY the currently promoted b1v3 plus b1v4
  through the parallel runner; do not re-run b0 or earlier candidates.

- October 5, 2026 (model switch + run scope): the suite's GPT pin
  moved from `gpt-5.6-luna` (tool-loop streaming broken server-side)
  to `gpt-6-luna`, verified by a live tool-loop probe; all gpt cache
  identities rotate automatically (model is an identity component).
  The b1v3 baseline retest runs under the new model with
  `--max-concurrent 1` (runtime env overlay allows one live workspace
  root per process). b1v4 remains approved for evaluation only.

- October 5, 2026 (baseline retest launched): full-matrix b1v3
  retest under gpt-6-luna running in the background, label
  `b1v3-gpt6-r1`, command `python -m suites.task_guidance.run --label
  b1v3-gpt6-r1 --max-concurrent 1` from `maintainer/agent-evaluation`
  with the repo-root `.env` sourced, log at `/tmp/b1v3-gpt6-r1.log`,
  started 15:03 UTC October 5 (pid 80257). Serialized execution makes
  this a multi-hour run (229 cases; producer cases alone run 10–30
  minutes each). First case (tg01 glm-max task-creation) still in
  progress at 15:32 UTC — normal for max-effort agentic runs. Monitor
  with `grep -E '^[.sF] |cases:' /tmp/b1v3-gpt6-r1.log`; the run exits
  non-zero only on case failures. After completion: b1v4 evaluation
  (approved, evaluation only) under the same invocation pattern.

- October 6, 2026 (baseline retest result + gating): `b1v3-gpt6-r1`
  finished after ~9 h: 225 ok, 8 failed, 9 skipped (skips are
  dependents of failed producers). Three failure classes:
  (1) two gpt task-creation producers (tg08/tg10, high effort)
  produced no task files — a genuine gpt-6-luna behavioral finding on
  2/6 gpt producer cells, all gpt identities re-executed fresh under
  the new model; (2) all three tg01 omit-plan from-plan cases failed
  the instructed-omission check although the same cells passed in
  `d-trial-tg01-r4` hours earlier — the children ran with
  `cache_hit: false`, so from-plan child results are NOT stable in the
  cross-process cache (candidates: child identity embedding an
  execution-specific parent artifact path, or publish/lookup
  asymmetry); needs a dedicated fix before from-plan cells are
  comparable across runs; (3) three assessment runs failed with
  `JSONDecodeError` on the judge's raw output (tg02 fidelity glm-max,
  tg04 fidelity + readability gpt-xhigh) — judge responses with
  malformed JSON currently fail the case (the parse path has only a
  brace-extraction fallback, `file_quality.py:_parse_json_object`, no
  retry). USER DECISION (October 6, 2026): malformed judge JSON must
  retry up to 2 times (re-request within the same logical run) before
  the case is allowed to fail. No further evaluation run (including approved b1v4) until
  task 150 (runtime env isolation) lands per the user's October 6
  direction; the from-plan cache instability and judge-JSON
  robustness items should be triaged alongside it.

## Execution plan` renamed to
  `## Implementation plan` everywhere (the section carries a decided
  design, not a step list); conditional plan inclusion decided by the
  author by default (explicit retain/omit followed, requirements-only
  files valid, never invent — replaces the "ask" rule behind the two
  producer failures); risks-and-way-back plus order logic as first-class
  plan content with a complete-restatement duty (GENERIC-6 18%,
  GENERIC-7 23%, retained 0/6, tg04 fabrication); per-section
  readability with formatting elements as examples (27 partial
  sections); self-containedness of files and presented summaries
  (GENERIC-9); an eight-row placement taxonomy including the
  notes-family sections; verification wording naming what it
  deliberately does not cover and fitting evidence to the task kind
  (GENERIC-5 55%); depth-follows-decisions conciseness (GENERIC-10);
  and the lifecycle collapse decided after review (September 27, 2026):
  `## Implementation Notes`, immutable `## Completion Notes`, and
  `## Post-completion follow-up` merge into ONE append-only
  `## Implementation notes` (entries as they happen, a clearly marked
  completion entry, corrections as new entries, earlier entries never
  rewritten). Follow-ups are ADDITIVE and may stay in the same file: a
  `## Follow-up plan: <title> (<YYYYMMDD>)` section appends below
  earlier plans with the full plan format, added requirements append to
  the Requirements checklist as unchecked items (or live in the
  follow-up plan itself), and execution records append to the notes; a
  separate task file remains an option (ask when the choice is
  material). Existing requirements are never modified silently: when a
  follow-up invalidates or alters an approved requirement — outcome,
  constraint, or completion evidence — asking is mandatory and the
  update lands only after user approval (Status tracking bullet + step
  7 + taxonomy rows). Compile-checked against the crystal-lattice target
  (output hash equals the source section). Suite compatibility:
  `assert_draft_execution_plan` accepts both headings (new unit test),
  tg07 acceptance wording and tg08–tg10 `applicable_sections` name the
  new heading, scenarios export regenerated. 213 deterministic tests
  green. The candidate is NOT promoted; promotion follows review and
  the re-measurement ordering (candidate + infrastructure before any
  run).

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
- [x] Four new scenarios with reviewed targets (September 26, 2026:
  tg07 tracking, tg08 documentation, tg09 operations, tg10 content — kind
  category with task-creation and both assessments; tg07 carries the
  deterministic absent-or-draft plan assertion; baseline run on v3 in
  [task-kind baseline results](../../maintainer/docs/evaluations/task-guidance/20260926-task-kind-baseline-results.md))
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

## Follow-up plan

Status: Draft (direction discussed and approved as direction on
September 26, 2026; open decisions listed below). When execution
starts, this section should be promoted into its own subtask file with
its own requirements checklist unless the user prefers executing it
here.

REQUIRED EXECUTION ORDER (approved September 26, 2026):

1. DONE — promote the current guidance and commit first, so the branch
   can be merged into develop at any time (executed: commit `4fb5f6a6`,
   see task 090's promotion note).
2. DONE — A + B refinements (package layout and matrix export), with
   new tests and test adjustments after the refinements; both current
   packages re-collected under the new layout (see Implementation
   Notes).
3. Layer 1 — presented-plan CONTENT coverage (corrected September 27,
   2026): plan content requirements declared in the reviewed targets,
   judged semantically over the committed plan sessions; no
   deterministic element assertions.
4. C — assessment semantics rework (re-judge only). Layer-style plan
   approved September 27, 2026 with recommendations: two new stages
   (`file-fidelity-assessment`, `file-readability-assessment`;
   `task-quality-assessment` retires after the re-judge lands,
   history preserved); readability grades EVERY top-level section
   present; b0 leniency check on a 12-file contrast subset;
   plan-content stays separate (presented plan vs file). See the
   Theme C execution plan section.
5. D — two-stage pipeline (own subtask when it starts).

Observed while inspecting
[the kind-baseline package](../../maintainer/docs/evaluations/task-guidance/results/20260926-task-kind-baseline/matrix.md)
(2026-09-26 review session); every item below was verified in the
package or the suite code before being recorded here.

### A. Package layout and navigation (export-only, no new runs)

- Per-subject assessments move under the producer cell they judge:
  `scenarios/<id>/<profile>/assessment/<stage>/sN/…` instead of
  `scenarios/<id>/assessment/<stage>/<profile>/sN/…`; judgments of a
  cell's plans (handoff assessments) sit in the same cell subtree.
- Every sample becomes a directory: producer cells gain
  `s0/`,`s1/,…` (run, session, task files) like assessments already
  have; invalid samples export `invalid.md` (recorded invalid reasons +
  response excerpt) so failures such as tg07/tg10's 1-of-3 producer
  failures are inspectable in place instead of only in the matrix list.
- Numbers live next to evidence: each judged subject directory gains
  `assessment.md` (the grades for that subject); each scenario root
  gains `results.md` (every cell × stage: grades, scores, statuses,
  links down); `index.md` and `matrix.md` link into `results.md`, and
  evidence pages link back — both directions must be one hop.
- Freeze/provider-failure records (for example the September 401
  outage entries frozen from `b1v3-r4` into the kind baseline) are
  marked distinctly or excluded at freeze with a note, so provider
  history does not read as candidate defects.

### B. Matrix export for the quality dimensions (export-only)

- `matrix.md` gains a task-file-quality cohort table (All/GLM/GPT and
  effort cohorts; top-grade share per dimension) and a per-judgment
  detail table with links to the subject's `assessment.md`, mirroring
  the existing task-creation semantic tables.

### C. Assessment semantics rework (re-judge only; producers untouched)

- Replace the ambiguous `occurrences` field (a term inherited from the
  mistake-oriented decomposition rubric, defined for one dimension and
  then reused for all) with `findings`: concrete `{where, quote, why}`
  items backing every grade; a non-top grade with empty findings is an
  invalid judgment (enforceable in validation).
- Add a mistake-harvesting response block so the judge's search is
  defect-oriented while grades stay completeness-oriented:
  `"mistakes": [{where, quote, why}]` — dropped facts, invented
  decisions, dense unreadable stretches, misplaced content, missing
  acceptance evidence. Rationale recorded from the review session:
  asked "how good is this", judges explain how good it is; asked to
  find specific mistakes, they find them.
- Split whole-file `findability` into per-section readability
  (`section_readability`, graded per key section — requirements,
  supporting details, execution plan) because the whole-file grade
  ceilings at complete whenever the governed file format is followed;
  the real problem is prose walls inside sections, especially the
  execution plan.
- Feed the deterministic structure metrics into the prompt as measured
  facts (longest paragraph, longest list item, table rows, plan prose
  share) so the judge anchors on numbers; deterministic floor +
  semantic judgment, no mechanical bans.
- Build a quality-assessment-specific target excerpt (approved
  outcomes, open questions, task summary, task kind, applicable
  sections, acceptance evidence, acceptable alternatives) instead of
  injecting the decomposition target wholesale (partition sizes,
  coherent deliverables, crossings, handoff plans are noise here).
- Open decision (see Assessment organization below): whether some
  dimensions move into the task-creation assessment and readability
  becomes its own assessment.

### D. Two-stage creation pipeline (material change; direction approved
### September 26, 2026 — replaces the one-shot producer)

- New stage pair modeling the real-world sequence: a `planning-session`
  (fresh workspace WITHOUT the tasks guidance — planning happens under
  normal repo guidance only) followed by a `task-creation-from-plan`
  turn continuing that session, with the tasks guidance delivered
  between the turns (committed into the workspace before the writing
  turn; the delivery check verifies presence for the writing turn).
- Approved direction: the one-shot producer is generally REMOVED —
  planning first is always better. Expect trial-and-error during
  rollout.
- Approved design sketch: plan ONCE per scenario at the top reasoning
  effort (for example gpt-max), verify the plan is good, then reuse
  that single planning conversation as the continuation prefix for the
  task-creation cells across the producer matrix (other models and
  effort levels create the files from the same plan).
- DECIDED plan verification (September 26, 2026): define a reviewed
  PLAN TARGET per scenario (what a good plan must contain, analogous to
  the decomposition target) and verify the generated plan with an
  assessment against it. The plan itself stays dynamic and
  model-dependent — regenerated per candidate cycle, cached while
  working on that candidate, NOT committed to the repo. Only if this
  proves too brittle or shows too much variance do we later decide to
  pin a committed plan.
- Remaining open implementation points: whether the planning transcript
  stays identity-blind for judges (planner model must not leak into
  subject material); whether retain/omit variants apply at the creation
  turn; migration order (trial on one scenario first, then
  matrix-wide).
- DECIDED committed-vs-generated boundary (September 26, 2026):
  committed sessions and task files are REPLACED with generated ones at
  the first possible opportunity — no maintenance rule for refreshing
  committed fixtures. Only what is unlikely to change stays committed:
  the reviewed targets, which pin a specific repo revision and a fixed
  task and may fix task-specific generic elements the plan and task
  file must contain (approved outcomes, plan target, element
  expectations, acceptance evidence form). Targets are the committed
  authority used to review dynamically generated plans and task files;
  generated artifacts (planning conversations, task files, presented
  plans, implementation states) are model-made, assessment-gated
  against the committed target, and cached per candidate — never
  committed. Concretely: the committed canonical handoff fixtures
  (`fixtures/handoffs/`) and their retain/omit stages are replaced by
  generated setups gated this way as soon as the gates exist; until
  then they remain a temporary bridge, not a maintained layer.
- Why: `plan_justification` and `plan_design_completeness` need a real
  planning antecedent to judge against; today planning and file-writing
  are fused in one guided session, and the guidance is present during
  planning, which real use does not do. The single-plan design also
  removes planner variance from the producer matrix: differences
  between cells measure file creation, not planning luck.
- Cost estimate: one planning session per scenario (top effort) plus
  ~26 creation turns (≈$0.30–0.50 GPT) plus GLM judging; comparability
  with b0/B1 baselines breaks for producer cells — the kind baseline
  and quality-coverage packages remain the one-shot-era reference.

### Assessment organization study (decided September 26, 2026)

Cost premise from the review session: two 5K-in/5K-out assessments cost
the same as one 10K-in/10K-out assessment, so splitting is not expensive.
Approved three-way split by question:

1. Task-creation assessment (existing): is this the right decomposition
   of the request — structure choice, crossings, deliverable mapping,
   requirement placement relative to deliverables. Unchanged.
2. Durable-context and plan-fidelity assessment: plan design
   completeness, durable-context preservation, section appropriateness,
   plan justification, task-kind fit (gaps 1, 3, 4, 5, 6).
3. Human-readability assessment (new, split out): per-section
   readability anchored on deterministic structure facts, mistake
   harvesting for presentation defects (gap 2) — a focused judge with a
   narrow rubric instead of one dimension among six.
- `section_appropriateness` stays with the file-artifact assessment
  (2): it judges placement within the file, not the work decomposition.
  Nothing folds into the decomposition assessor.

### Judge input format (decided September 26, 2026)

- No tool calls for judges for now.
- Task files and the conversation are embedded in the prompt in their
  natural rendered format (fenced markdown with path headers), not as a
  JSON map — escaped newlines distort the reading experience the
  readability judge is supposed to evaluate.
- JSON is kept only for genuinely structured data: the reviewed target
  and the assessment response shape.
- The workspace-reading judge (read-only workspace + tools, navigating
  like a reviewer) stays a recorded future option, not planned work.

### Readability elements (corrected September 27, 2026)

- Formatting elements (tables, bold text, ordered lists, code snippets,
  directory-tree visualizations) address readability of the TASK FILE,
  not the assistant message.
- The guidance and the assessments must NOT prescribe a specific set of
  elements, and nothing about elements is asserted deterministically.
- Elements appear only as EXAMPLES inside one semantic readability
  dimension of the task-file quality assessment — illustrations of how
  long paragraphs can be avoided, never a checklist. The judge decides
  whether the sections are readable for a human; the deterministic
  structure profile stays reported facts.
- Superseded framing (recorded for continuity): an earlier draft of
  this section had per-task element expectations measured for presence.
  Rejected in review — that reintroduces prescribed shapes through the
  back door.

### Next calibration (details for continuing without this session)

Baseline numbers on B1v3 (28 subjects: 18 development + 10 kind; GLM
identity-blind judge; packages `20260926-task-quality-coverage` and
`20260926-task-kind-baseline`):

| Gap | Dimension | B1v3 result | Other evidence |
|---|---|---|---|
| 1 steps-not-design | plan_design_completeness | 22 complete / 5 partial / 1 poor | `plan_prose_share` floor 0 persists; tables nearly absent (48/50 dev files, 7/7 kind files) |
| 2 readability | findability | 28/28 complete (ceiling; zero variance) | longest paragraph 210 w dev / 120 w kind; every dev file has subsections; b0 contrast: 296 w paragraphs, 8/72 files no subsections |
| 3 dropped detail | durable_context_preservation | 23 complete / 5 partial | fresh-agent generated-file plans 6/6 complete coverage, 0/6 broad rediscovery, quality 91–96 |
| 4 placement | section_appropriateness | 28/28 complete (ceiling; zero variance) | not measured on b0 |
| 5 invented plans | plan_justification | 21 justified / 5 not_applicable / 2 fabricated | explicit-deferral violated 1/3 samples (tg07 GLM); plan-inclusion ask-and-stop 1/3 (tg10 GPT); both fabricated = tg04 GPT high+max |
| 6 forced dev shape | task_kind_fit | 26 fits / 2 missing | kind scenarios 10/10 fits; both missing = tg04 GPT high+max |

- Calibration targets: the tg04 pair (owns the `poor`, both
  `fabricated`, both `missing`, 2 of 5 context drops); the conditional
  execution-plan wording (drives both 1/3 producer failures); the two
  ceiling dimensions (leniency check below).
- Judge-leniency check (no producer runs needed): run the same quality
  assessment over the committed b0 outputs; if the judge also gives b0
  complete on the ceiling dimensions, the dimensions — not the files —
  are the problem, and C's rework is the fix.
- Candidate wording directions for the next guidance candidate (extends
  the promoted practical baseline): the execution plan is conditional
  (include one when planning happened or was requested; a
  requirements-only task file is valid; never invent plan detail);
  plan-design completeness restated as decided design, not steps
  (v3's design-visibility rule already moved this); readability
  guidance naming per-section structure, with formatting elements
  (tables, ordered lists, code snippets) shown as EXAMPLES of avoiding
  long paragraphs, never prescribed; kind-appropriate acceptance
  evidence.
- DECIDED wording direction (September 26, 2026) — section rename:
  stop prescribing the name `## Execution plan`; use `## Implementation
  plan` as the default, conditionally allowing `## Execution plan` for
  clearly process-based tasks (for example deployment runbooks).
  Rationale: models read "execution plan" as steps to execute and
  "implementation plan" as the design behind the work — the rename
  moves gap 1 without adding explanation text. What must move with it:
  the guidance prescribes the name verbatim today; the deterministic
  plan detection is already name-agnostic (`PLAN_SECTION_HINTS` matches
  any title containing "plan"), so metrics and the absent-or-draft
  assertion keep working; the committed canonical handoff fixtures and
  assessment prompt wording use the current name and update with the
  candidate — or the fixtures are already replaced by Theme D's
  generated setups by then, whichever lands first.
- ADDITIONAL wording directions (September 27, 2026): the agent
  DECIDES how much planning to include in the file, working by default
  without explicit user instruction (the omit case becomes a single
  additional instructed test on top of prior planning); the
  implementation-plan section carries a RESTATEMENT duty — restate the
  decided design completely, never invent detail the planning did not
  establish (correct under both the one-shot and two-stage pipelines);
  acceptance evidence names the decisive boundary AND what it
  deliberately does not cover (GENERIC-5 sits at 55%).
- Re-measurement after wording: kind scenarios + tg04 cells first
  (multi-sample, 3 per flaky cell), full matrix if the wording touches
  anything broader; per the September 27 ordering, the re-measurement
  RUN waits for the candidate AND the prerequisite infrastructure
  (zai provider, minimal configs, interleaved-thinking, parallel
  runner).

### D amendment — non-lossy add-and-compare design (approved
### September 27, 2026; supersedes the replacement above)

D no longer replaces the one-shot producer. The one-shot task-creation
stage STAYS (b0/B1v3/C comparability preserved), and the two-stage
pipeline is ADDED as parallel arms:

- Arm 0: one-shot (current, unchanged).
- Arm 1: plan-then-create, GUIDED planning (tasks guidance present in
  the planning turn; creation turn continues the session).
- Arm 2: plan-then-create, UNGUIDED planning (normal repo guidance
  only; tasks guidance delivered between the turns).
- Preserve-thinking variant: tried in ALL variations (arms 1–2 ×
  with/without preserving the planning turn's reasoning into the
  creation turn); kept wherever it CAUSES VARIANCE. Every scenario
  must run correctly both with and without preserve-thinking.

Clarified rules:

- "Winner" means ANY arm with added value, not a single survivor.
  Prune only arms that merely replicate their parent (trial subset
  first, then matrix-wide only the survivors).
- KIND scenarios get only the one most useful stage (at most two): no
  separate omit-plan, no separate preserve-thinking. First candidate:
  preserved thinking + task creation after prior planning WITH the
  task guidance given in planning; add the unguided-planning case only
  if it adds value. SELECTION RULE: keep the arm that shows meaningful
  new or different MISTAKES — not the best results; the worst
  (defect-showing) results are what the suite exists to find.
- OMIT-PLAN becomes a single additional test ON TOP OF PRIOR PLANNING
  (an instruction variant of the creation turn), NOT the current
  hand-made canonical omit fixture — the existing canonical omit case
  is plain wrong under this design. The guidance candidate must make
  the agent DECIDE how much planning to include, working by default
  without explicit user instruction; the omit test then verifies the
  instructed-omission path only.
- Planning sessions stay per-scenario and gated by the plan target
  (Layer 1 machinery); arm 1 and arm 2 need separate gated plans.

### Prerequisite infrastructure changes (approved September 27, 2026;
### must exist before any new evaluation runs)

1. GLM provider switch ollama → zai, SELECTABLE (config/env chooses
   between ollama and zai). Reason: ollama has no preserve-thinking
   setting; zai is wanted for GLM anyway. GPT stays as is.
2. Runtime agent configs MINIMALIZED: drop the unused snippets and
   plugins the current fixtures carry; keep only what the suite's runs
   actually use.
3. New plugin `interleaved-thinking` for the openai-compatible
   provider: omits thinking blocks from previous turns when building
   the request. Including/excluding the plugin in the agent config is
   the preserve-thinking switch, provider-independently (works on both
   zai and ollama).
4. A PARALLEL RUNNER: one command runs the whole evaluation (like a
   B1v3) or any slice, replacing the current multiple per-stage
   pytest invocations. Per-provider maximum parallelism comes from
   config; execution respects every stage dependency (planning before
   creation-from-plan, producers before their assessments, parent
   links) without breaking any of them.

### Ordering after C (decided September 27, 2026)

1. Guidance candidate FIRST (calibration drafting — the six gaps plus
   the new directions below).
2. The prerequisite infrastructure changes above.
3. The non-lossy D stages (amendment design).
4. Evaluation runs LAST, only after BOTH the candidate and the test
   changes are done: re-run the latest B1v3 and C under the new
   provider with the new candidate; then the D-arm trial. b0 is NOT
   re-run after the changes (not a priority; the committed b0 package
   stays as the historical reference).

### E. Workflow step coverage (recorded September 26, 2026; future work)

The final test suite should cover most steps of the common task-file
workflow, each step tested IN ISOLATION (not one big multi-stage test):

1. Planning (conversation only).
2. Creating the task file.
3. A NEW agent revises and accepts the plan.
4. Implementation (appending implementation notes, discovered facts).
5. Follow-up paths: minor changes (affecting implementation notes); a
   follow-up plan and implementation, possibly with requirement
   changes.

Design: each step's test has a FIXED SETUP that may consist of a
session prefix (for example, step 5 starts from a conversation that
already contains the implementation, plus a new prompt carrying the
follow-up change), a file structure containing the implementation, and
the task file with implementation notes.

- Setups are DYNAMIC, not committed: committed canonical fixtures go
  stale quickly as task-file guidance and formats evolve, and per the
  committed-vs-generated boundary in Theme D they are REPLACED, not
  maintained. A committed canonical set exists today — the handoff
  fixtures under the suite's `fixtures/handoffs/` (tg01–tg03
  retain/omit/incomplete), consumed by the canonical handoff stage —
  and serves as a temporary bridge until generated, gated replacements
  exist (first possible opportunity), not as a maintained layer.
- New setups follow the same verification pattern as the two-stage
  plan: generated by a model that can do the step well, verified by an
  assessment with a QUALITY GATE (at least 80% quality) before the
  setup is used, and CACHED per candidate (fixed while working on a
  specific candidate, not saved in the repo).
- Existing suite stages already cover steps 1 (partially, fused with
  2), 2, and fresh-agent planning (adjacent to step 3); steps 3 as
  revision-acceptance, 4, and 5 are new coverage.
- ADJUSTMENT (approved September 26, 2026; content assertion
  corrected September 27, 2026) — present the plan at implementation
  start: when implementation begins, the agent first SHOWS the plan for
  final approval — with a new agent AND with the same agent, and EVEN
  IF the task file's plan is already `Approved` (showing is always
  required; re-approval is the formality when the plan was already
  approved). The presented plan is then ASSERTED ON CONTENT, judged
  semantically: it must convey the content that matters to humans for
  that specific task (for example the query contract in tg02, when that
  is an important part of the plan) — see the plan content requirements
  below. Formatting elements are NOT asserted here; they are examples
  inside the task-file readability dimension only.
  Guidance verification (September 26, 2026): the present-again rule
  exists for Draft plans ("If one exists from an earlier session,
  reassess it and present it again") and the presentation format is
  defined ("### Presenting an execution plan": summarize outcome,
  scope, approach, material decisions or questions, acceptance
  evidence, documentation audience, risks, exclusions; conceptual
  boundaries over file inventories) — but presenting is not required
  when the plan is already `Approved`, and the tracking carve-out
  ("Steps 2–4 do not require duplicate approval…") lumps presentation
  with approval. The next candidate separates them: presentation
  always; duplicate approval not required when already approved.
  Assessment note: among the missing workflow tests, this is one of
  the most important.
- FITS THE PLANNED WORK NOW (corrected September 27, 2026): the
  suite already captures presented plans — the handoff plan stages
  (`plan-retain`, `plan-omit`, `generated-plan`) and continuations are
  "present the Draft implementation plan" turns with committed
  sessions. Sources: `plan-retain`/`plan-omit` present plans FROM THE
  COMMITTED CANONICAL task files (temporary bridge per Theme D);
  `generated-plan` and `continuation` present plans from
  MODEL-GENERATED files (dynamic arm, cached in the packages). Layer 1
  needs no new task files, adds nothing to the committed-fixture
  layer, and calibrates both arms. CORRECTED Layer 1 scope: declare
  per-scenario PLAN CONTENT REQUIREMENTS in the reviewed targets (the
  Theme D plan target: the decided-design content a human needs from a
  plan for that task, derived from the pinned revision and the fixed
  task), then judge the already-captured presented plans against them
  SEMANTICALLY — an identity-blind per-subject assessment grading
  whether each required content item is conveyed, with findings for
  missing/unclear/wrong content and any human-needed content the
  requirements missed. No deterministic element measurement anywhere.
  The full present-at-implementation-start stage (an executor-side
  turn with its fixed setup) lands with Theme D/E.

### Layer 1 — presented-plan content coverage (plan approved
### September 27, 2026)

Two requirement layers, both committed authority; one semantic
assessment; one judge-validation gate before any baseline is trusted.

**Generic requirements** (one suite-level constant, applies to every
scenario; full text authored in the suite module):

- GENERIC-1 High-impact decisions, each marked decided (brief
  rationale) or open (explicit approval question with recommendation
  when one exists) — never buried in steps.
- GENERIC-2 The result at its public boundary before mechanics:
  behavior/contract/surface change, so direction and construction are
  judgeable separately.
- GENERIC-3 What stays untouched and why; scope deliberately excluded.
- GENERIC-4 The constraints that ruled out alternatives, and the
  assumptions relied on with how each could be cheaply confirmed.
- GENERIC-5 Verification with a decisive boundary: what evidence, at
  which boundary, proves the outcomes — and what it deliberately does
  not cover.
- GENERIC-6 Risks, blast radius, and the way back (rollback, phases
  that stay shippable, escape hatches).
- GENERIC-7 The logic of the sequence (dependencies, contract before
  consumers, risk first) and the milestones where progress becomes
  verifiable or usable.
- GENERIC-8 What feedback the plan needs from the reader: approvals
  wanted, questions needing answers, priorities to confirm.
- GENERIC-9 Self-containedness: everything needed to evaluate the plan
  is in the text — facts stated not referenced; links carry, never
  replace (litmus: delete every link, the plan must still be
  evaluable); terms introduced at first use; conversation context
  restated in decided form; snippets illustrate while prose asserts;
  specifics appear as values. Proportionality guard: duty covers
  evaluation-relevant facts, not everything.
- GENERIC-10 Depth follows decisions; mechanics stay summarized:
  promises with boundaries instead of specifications, strategy over
  inventory, public surface over internal mechanics. Litmus: would
  changing this detail change the reader's decision? Over-detail is a
  finding only when it buries decisions or fakes precision.

**Task-specific requirements** (`plan_target.required_content` in each
target, ids PLAN-n, `derived_from` outcome ids): tg01 URL design with
approval status, cap + exactly-once mechanism, ordering, conditional
navigation, untouched surfaces, static-output constraint, decisive
build verification; tg02 query contract (semantics/defaults/bounds/
invalid handling), response compatibility incl. total header, ordering
guarantee, CRUD compatibility, route-level verification; tg03 where
the filter lives and survives refreshes, mutation path through
production transport and route, state/result/empty-state consistency,
untouched behavior; tg04 client-server discovery state contract,
composability and bounds, URL share/restore design, refresh retention,
unparameterized compatibility, contract-first adoption sequence; tg05
public query contract as first-class object, service via production
HTTP + real storage, client preserving current calls, CLI proving the
full path, contract-before-surfaces delivery with per-surface docs;
tg06 normalized author representation, rendering equivalence rules,
content/tooling migration approach, retirement condition,
every-revision-builds constraint shaping phases, explicit phase order.

**Assessment shape:** identity-blind per-subject judge (GLM, local).
Input: one presented-plan response + generic requirements + the
scenario's plan content requirements, embedded as rendered text (JSON
only for the response shape). Grades: per requirement
conveyed/partial/missing; GENERIC-9 self-contained/partial/
external-dependency; GENERIC-10 proportionate/over-detailed. Every
non-top grade requires a finding (where, what, why); a mistakes block
harvests content gaps beyond the requirement list. Cross-cutting
rules: an item whose meaning depends on an external resource grades at
most partial; depth must match impact — verbosity not rewarded,
brevity that loses nothing not penalized.

**Judge-validation gate (approved strategy, runs before baselines are
trusted):** generate one natural presented-plan response (any model —
an already-committed session response is fine), then hand-adjust it to
match the full requirement set ("perfect" plan). Assess both with the
same identity-blind judge. Acceptance: the adjusted plan receives a
good score overall — 100 not required, no plan is perfect on every
dimension — and NO dimension shows zero variance: any dimension that
grades always-low or always-high whatever the plan quality (across the
probe pair at minimum, and across the calibration corpus) is a
leniency/ceiling defect in the rubric to fix before recording
baselines. The adjusted probe stays a scratch calibration artifact in
tmp, never committed guidance evidence.

GATE RESULT (September 27, 2026): PASSED. Probe pair = tg02
plan-retain glm response (label b1v3-r1) + hand-adjusted
requirement-matching rewrite; judge glm-5.3-flash:cloud max;
artifacts `tmp/plan_content_gate.{py,json}`. Natural coverage 87%
(PLAN-1 partial, GENERIC-6 partial); adjusted coverage 93%; the one
non-top grade on the adjusted plan (GENERIC-4) came with a CORRECT
finding — the adjusted plan genuinely omits out-of-range offset
behavior — so the judge catches real gaps instead of rubber-stamping.
Pair variance on PLAN-1/GENERIC-4/GENERIC-6; the twelve flat-at-top
requirements get their variance test across the calibration corpus
(where the incomplete negative control should grade low).

CALIBRATION BASELINE (September 27, 2026; c1): 22 judgments over
label b1v3-r1 plan stages (retain 6, omit 6, generated-file 6,
generated-task 3, incomplete 1; 3 gpt-high continuations skipped —
invalid upstream), judge glm-5.3-flash:cloud max, frozen dataset
`task-guidance-plan-content-c1-20260927` (tmp, not committed; packages
are the committed evidence). One prompt-hardening iteration was
needed: 3/25 first-pass responses graded GENERIC-9/10 as `conveyed`;
the prompt now restates the special scales at the response contract
and the full corpus re-ran clean under one prompt (22 passed,
0 contract failures).

- Mean top-grade coverage 84% (tg01 85%, tg02 82%, tg03 86%).
- By variant: retain 79% < generated-file 83% < omit 86% <
  generated-task 92%; incomplete (n=1) 93% — the negative control
  still yields a content-rich plan, consistent with earlier handoff
  findings that agents reconstruct from the repo.
- Discriminative requirements (top-grade share across all 22):
  GENERIC-6 risks/way-back 18%, GENERIC-7 sequence logic 23%,
  GENERIC-5 verification boundary 55%, GENERIC-4 constraints/
  assumptions 77%, GENERIC-9 self-contained 91%, PLAN-1 73%,
  PLAN-3 91%.
- Zero-variance (flat at TOP in this corpus): GENERIC-1/2/3/8/10,
  PLAN-2/4/5/6/7 — none flat-low. Ceiling candidates for the Theme C
  re-judge: either genuinely easy for decent plans or leniency; probe
  with a deliberately steps-only plan before trusting them.
- GUIDANCE FINDING for the six-gap calibration: retained-plan
  presentations score LOWEST (79%) and never convey GENERIC-6 (0/6)
  or GENERIC-7 (0/6) — the canonical plan files carry steps but not
  risks/way-back or sequence logic. The next guidance candidate's
  plan template should make risks-and-the-way-back and order-logic
  first-class plan content.
- Missed-requirement findings: 0 — the judge found no human-needed
  content beyond the two requirement layers (weak evidence the layers
  are complete; possibly judge conservatism — keep harvesting).

**Wiring + tests:** prompt module, stage wiring, freeze/collect
integration (results land in packages under the cell layout), unit
tests on normalization and wiring. **Cost:** GLM judging only
(~25–30 plan sessions in the kind-baseline package, both arms), zero
producer runs. **Deliverables:** generic + task-specific requirements
committed in the suite, calibration baseline in this file, the
assessment ready as the plan-fidelity component of Theme C and the
plan-verification gate of Theme D.

### Theme C execution plan (approved September 27, 2026)

Re-judge only; producers untouched. Components: (1) findings contract
— `{where, quote, why}` replaces `occurrences`, non-top grade without
findings invalid; (2) mistake-harvesting block
`"mistakes": [{where, quote, why}]` — defect-oriented search,
completeness-oriented grades; (3) file-fidelity assessment — plan
design completeness, durable-context preservation, section
appropriateness, plan justification, task-kind fit; (4)
file-readability assessment — per-section readability over every
top-level section present (deterministic per-section structure facts
embedded as measured numbers: longest paragraph words, longest list
item, list/table usage, plan prose share) plus a whole-file
navigation grade, no formatting prescriptions; (5) embedded-markdown
judge input — task files as fenced markdown with path headers,
conversation as text, quality-specific target excerpt (title, task
summary, approved outcomes, open questions, acceptable alternatives,
kind expectations) instead of the decomposition target wholesale.

Validation gates before baselines (generalizes the Layer 1 gate):
per assessment a natural subject + hand-adjusted good probe + one
deliberately bad probe (prose wall for readability; steps-only or
dropped-context file for fidelity); acceptance: good probes score
well (not 100), bad probes grade down, no dimension flat-low,
ceiling candidates break. Then the b0 LENIENCY CHECK: re-judge a
12-file contrast subset of the committed b0 package sessions
(`20260919-current-guidance-b0`) with the same new prompts — if the
old ceiling dimensions still grade complete on b0 files under the new
rubric the dimensions are broken; if per-section readability
discriminates b0 from B1v3 the rubric is fixed.

THEME C BASELINE (September 27, 2026; c1): 28 judgments over 26
subject cells (labels b1v3-r1 + b1v3-k1; two multi-sample cells), judge
glm-5.3-flash:cloud max; frozen dataset `task-guidance-file-quality-c1-20260927`;
package `results/20260927-file-fidelity-readability/` (check passed;
generated-view links clean). Results page
`20260927-file-fidelity-readability-results.md`.

- READABILITY CEILING BROKE: old `findability` 28/28 complete on these
  subjects → per-section readability 222/249 (89%) readable with 27
  partial sections each carrying findings + 159 presentation mistakes.
  Model split: GLM 55/70 (79%) vs GPT 167/179 (93%).
- Fidelity: plan_design_completeness 25 complete / 3 partial;
  durable_context 24/4; section_appropriateness 27/1;
  plan_justification 23 justified / 5 not_applicable; task_kind_fit
  28 fits; 45 mistakes harvested (13 GLM + 32 GPT).
- CALIBRATION QUESTION: the tg04 events did NOT reproduce — old 2
  `fabricated` now `justified`, old 2 `missing` now `fits`. Either GLM
  judge variance or signal lost in the reworked prompt (target excerpt
  instead of full target). Mistake harvest still flags tg04 content;
  verify with a contrast probe before relying on `plan_justification`
  in the next calibration.
- Retirement executed: `task-quality-assessment` left the live
  configuration (no live cases, no expected sets); historical
  collection resolves its judge through
  `RETIRED_ASSESSMENT_STAGES`; the quality unit tests and old records
  and packages stay as history.

GATE RESULTS (September 27, 2026): BOTH PASSED. Artifacts
`tmp/file_quality_gate.{py,json}` (judge glm-5.3-flash:cloud max;
probes: natural tg02 glm producer from b1v3-r1, hand-built good
version, deliberately bad steps-only version with an invented
migration constraint).

- Fidelity: natural 5/5 top (1 mistake); good 4/5 top — the partial
  (`plan_design_completeness`) carried a CORRECT finding (the good
  probe's design sits in one run-on paragraph); bad 0/5 top —
  poor/poor/poor/fabricated/missing with 10 harvested mistakes, the
  fabricated grade catching the invented migration.
- Readability: the natural B1v3 file graded 2/4 sections readable
  with precise findings (a list item packing six facts; the
  load-bearing rule buried in a clause) — the old `findability`
  dimension graded the same files 28/28 complete, so THE CEILING
  BROKE. Good probe 3/4 readable (fair partial); bad probe 1/3
  readable with navigation partial and the exact expected findings
  (checklist with no checklist; contradictory ordering appended after
  the step list).

B0 LENIENCY VERDICT (September 27, 2026; artifacts
`tmp/b0_leniency_check.{py,json}`, 18 dev cells × 2 assessments, 2
retries recovered, 0 skips):

- Fidelity DISCRIMINATES where b0 is actually weak:
  `plan_design_completeness` 16/18 top, `durable_context_preservation`
  15/18 top (33 mistakes harvested). `section_appropriateness`,
  `plan_justification`, `task_kind_fit` are flat-at-top on b0 — but
  plausibly CORRECTLY: b0 producers did plan in-conversation and used
  kind-appropriate evidence; their defects were structure and dropped
  detail, which the first two dimensions catch. Fabrication events
  remain rarer (B1v3's two fabricated judgments show the dimension
  can fire).
- Readability FINDS A UNIT CONFOUND: b0 grades 242/271 (89%) sections
  readable, navigation 18/18 — BETTER than the B1v3 gate probes
  (50–75% readable). Cause: b0 task sets are MULTI-FILE with many
  small sections (tg05: 85 sections; tg06: 91), and short sections
  trivially grade readable, while B1v3 single files carry big sections
  (a 1085-word plan graded partial). Per-section readability measures
  section size as much as guidance quality when comparing different
  decompositions. CAVEAT all cross-corpus comparisons; RECOMMENDED
  follow-up: a whole-file reading-effort grade (beyond navigation), or
  word-weighted aggregation, decided with the B1v3 re-judge numbers in
  hand.
- Net: the rubric is fixed enough to baseline (gates + fidelity
  discrimination), with readability cross-corpus comparison caveated.

Execution steps: excerpt builder + contract module (unit tests);
fidelity assessment wiring (stage, consolidation, package tables);
readability assessment wiring (same, plus per-section facts from the
structure profile); probe gates; b0 check; live re-judge of the 28
B1v3 subjects × 2 assessments (~56 GLM-flash judgments), freeze +
collect new package `20260927-file-fidelity-readability/` under the
cell layout with cohort/detail/variance tables; baseline table into
this file. Old task-quality records and packages stay as history.

### Guidance gaps found by applying the task guidance to this file

Self-application findings from the review session (candidates for the
next guidance candidate or new tests), with decisions from the
September 26, 2026 review:

- No defined place for a follow-up plan — DECIDED: multiple follow-up
  plans are allowed and common; they are append-only additions to the
  open task file (this file's `## Follow-up plan` section after the
  execution plan is the blessed placement); only MAJOR new pieces of
  work become new subtasks; requirements themselves may occasionally
  change during follow-up. The guidance must also define implementation
  notes and their placement (execution-time discoveries and deviations,
  distinct from completion notes).
- What the guidance says about follow-ups TODAY (verified September 26,
  2026, current and b1v3 candidate `tasks-v7`): one sentence — "Put
  later corrections under `## Post-completion follow-up`. Ask before
  reopening or materially extending the task, or creating another
  task." — plus executor rules "Record discoveries and plan changes in
  `## Implementation Notes`" and "Add `## Implementation Notes` only
  after execution starts and immutable `## Completion Notes` only after
  completion." Nothing defines follow-up plans while a task is open,
  their append-only placement, requirement changes during follow-up, or
  recorded future options. Agents mostly do this right by convention;
  the next candidate makes it explicit.
- No durable-context rule for task files themselves: task files must
  preserve anything from the working conversation that later work
  depends on, because sessions are lost or compacted; the guidance does
  not state this explicitly for task files written during long
  collaborations.
- Numbers presentation — SUPERSEDED by the readability-elements
  decision (see above): elements are never prescribed; task-specific
  element expectations live in the reviewed targets.
- Candidate new scenario APPROVED: a request to extend or amend an
  existing task file (for example recording a follow-up plan) — tests
  whether the model knows where additions belong; would have caught the
  follow-up placement gap behaviorally.

### Data-type placement taxonomy (draft for the guidance candidate)

Draft answer to "which kinds of data appear during planning and task
completion, and is it obvious where each goes at each stage?" — to be
refined into guidance wording and, where placement is checkable, into
assessment dimensions:

| Data kind | Appears | Where it belongs |
|---|---|---|
| Approved outcome / constraint | planning | Requirements checklist (follow-up may amend it, noting the change) |
| Rejected alternative + why | planning | Questions and decisions (decision with rationale) |
| Open question / unresolved choice | planning, execution | Questions and decisions |
| Verified fact + source | planning, execution | Supporting details (durable) — NOT implementation notes |
| Material design decision | planning | Questions and decisions; design itself in the execution plan |
| Task-structure decision (single vs subtasks, boundaries) | planning | Questions and decisions; reflected in the file/directory layout |
| Approach, steps, verification plan | planning | Execution plan |
| Status of plan steps | execution | Execution plan checklist updates |
| Deviation from plan, discovery during execution | execution | Implementation notes (chronology of this execution) |
| Durable fact discovered during execution | execution | Graduates into supporting details (not left in implementation notes) |
| Verification evidence (what proved it) | completion | Completion notes via requirement verification |
| Deferred / out-of-scope item | completion, follow-up | Completion notes (unresolved scope), then follow-up plan |
| New requirement or requirement change | follow-up | Requirements checklist amendment + note |
| Correction to an earlier recorded fact | follow-up | Post-completion follow-up / follow-up plan, amending the source |
| Follow-up work item (approved direction, not yet started) | follow-up | Follow-up plan (append-only) |
| Recorded future option (worth storing, explicitly not planned now) | any stage | Follow-up plan, as a distinct kind from approved follow-ups — marked "future option", never presented as planned work (this file's workspace-reading-judge note is the live example) |

The four placement traps are DECIDED (approved September 26, 2026):
durable facts discovered during execution graduate into supporting
details (implementation notes keep the deviation story); decision
rationale lives with the decision in questions and decisions while
supporting details hold factual background; requirement changes during
follow-up amend the requirements checklist (with a note) so the
checklist alone shows current truth, and the follow-up plan records why
it changed; verified facts discovered after completion amend the source
section through post-completion follow-up rather than the immutable
completion notes. These become guidance wording plus checkable
placement assertions in the fidelity assessment (a dropped-or-misplaced
fact is a `findings` item).
