# Two-stage creation pipeline (non-lossy add-and-compare)

Parent scope: task 120 (Theme D amendment, approved September 27, 2026).
This subtask implements the added two-stage arms next to the kept one-shot
producer, the planning gate, and their wiring through the suite and the
parallel runner.

## Requirements checklist

- [ ] Arm 0 (one-shot `task-creation`) stays runnable and unchanged; all
  existing stages, records, and baselines keep collecting exactly as before.
- [ ] Arm 1 `planning-session` (guided): a fresh fixture workspace, the
  scenario's natural request, the tasks guidance INCLUDED in the planning
  turn's system message, and an ask to present the implementation plan
  without implementing.
- [ ] Arm 2 `planning-session` (unguided): identical, except the tasks
  guidance is ABSENT from the planning turn's system message
  (`include_tasks=False`); the compiled fixture workspace contains no tasks
  guidance either (fixture targets have no tasks slot — verified).
- [ ] `task-creation-from-plan`: the SAME session continues with the tasks
  guidance included (delivery check `tasks_occurrences == 1` holds for the
  writing turn), the agent creates the task file(s); every producer
  validity check of `task-creation` applies.
- [ ] Preserve-thinking variants run in ALL new-stage variations via the
  `interleaved-thinking` plugin present/absent in the runtime agent config;
  every scenario must run correctly both ways. GPT documents the
  limitation: the plugin requires the openai-compatible provider, so the
  GPT arm keeps provider-default thinking behavior.
- [ ] The planning session is judged by the plan-content assessment
  against the scenario's `plan_target`; the gate status is recorded with
  the planning run (shared per scenario+arm at top effort, reused as the
  continuation prefix across producer cells).
- [ ] OMIT-PLAN is a single additional test on top of prior planning: an
  instructed omission in the creation turn for one scenario; the canonical
  omit fixture stays as the historical bridge.
- [ ] Kind scenarios get one most-useful stage only (first candidate:
  guided planning + preserve-thinking), chosen by which shows meaningful
  new or different MISTAKES; a second arm is added only if it adds value.
- [ ] Arms without added measurable value are pruned from default runs
  (kept runnable, not selected by default) after the trial.
- [ ] The parallel runner runs the new stages with the same one-command
  slicing and per-agent parallelism as the existing stages.

## Decided mechanics (from the September 27 session)

- Guidance delivery is per-request: the fixture targets' compiled
  AGENTS.md has NO tasks slot, so arm differences reduce to the
  `include_tasks` request flag already used by assessments; the writing
  turn always compiles with `include_tasks=True`.
- Preserve-thinking is CONFIG-FILE-DRIVEN per provider (corrected
  September 28 per the zai reasoning tests): zai preserves via
  `request_options.thinking.clear_thinking: false` (server-side state,
  no plugin); zai strip = default. Ollama preserves by default (inline
  `<think>` content re-sent); ollama strip =
  `path:${env:BUILTIN_PLUGINS}/interleaved-thinking` in the plugin list
  — the plugin is needed ONLY for ollama.
- STAGE-DECLARED BASE CONFIG + OVERRIDES (final, September 28): one
  base config file per agent; every stage declares
  `{config, agent_id, overrides}` in configuration.json, and small
  variations are OVERRIDES via the existing core mechanism
  (`resolve_request_config` merges a per-request override dict over the
  base agent config; `_effective_overrides` stores them on the session
  and shallow-merges later turns — so the zai thinking setting applied
  at planning persists and the writing turn flips only `include_tasks`).
  Examples: planning-unguided = `{include_tasks: false}`; zai preserve =
  `{request_options: {thinking: {clear_thinking: false}}}`; ollama strip
  = `{plugins: [...agent plugins + interleaved-thinking path...]}`;
  model/effort = existing override keys. No per-variant config files.
  The overrides are committed stage data applied through the core path;
  delivery checks stay as verification.
- Cross-model continuation: the shared plan is produced by GPT at max
  effort (recorded decision), and producer cells (glm/gpt) continue that
  session via `continue_from` + session restore; cell differences measure
  file creation, not planning luck. The planning turn's delivery record
  carries `include_tasks` per arm so judges stay identity-blind.
- Planning prompt = the scenario's natural request + a standard
  investigate-and-present-your-plan instruction (no implementation).
- Creation-turn prompt = a standard create-the-task-file continuation
  ask; the omit variant adds the explicit no-plan-section instruction.

## Execution plan

Status: Draft

1. Stage catalog: `planning-session` (executor `run_planning_session`,
   variants guided/unguided, record `task-guidance-planning.json`) and
   `task-creation-from-plan` (executor `run_task_creation_from_plan`,
   record `task-guidance-from-plan.json`); wire into configuration.json
   for the six dev scenarios; kind scenarios declare only the one chosen
   stage.
2. Harness: `run_planning_session` (fresh TaskGuidanceWorkspaceFactory
   workspace; `include_tasks` per variant; validity: completed, non-empty
   response, no mutations) and `run_task_creation_from_plan`
   (`continue_from` the planning run on its workspace;
   `include_tasks=True`; capture task files; full producer validity +
   delivery checks; omit-instruction variant uses
   `assert_no_execution_plan`-style checks). Value types carry the
   planning session snapshot for the gate.
3. Config variant: extend `agent_config_file(..., variant=...)` with
   `"strip-thinking"` (plugin appended); the from-plan executor selects
   the variant per case; cache identity includes the variant.
4. Gate: judge each planning session with `plan_content_prompt` +
   plan-content assessment on the GLM judge cell; record the judgment and
   a pass/fail gate flag on the planning record (threshold: no missing
   requirement grades and coverage ≥ 0.8 unless the target says stricter;
  regeneration is a fresh re-run until the gate passes).
5. Matrix + records + freeze + result-package wiring following the
   established per-stage patterns (cases keyed by arm and
   preserve-thinking; producer-table columns for arm + gate).
6. Runner: add the new stages to `STAGE_GROUPS` (planning before
   from-plan, from-plan before its assessments); CLI slicing works
   unchanged.
7. Trial: one dev scenario first (tg01) across arms × preserve-thinking;
   prune per the recorded rule; then matrix-wide for surviving arms; kind
   arm selection by the mistake rule.
8. Tests: stage wiring, case enumeration, planning validity, from-plan
   validity (incl. instructed omission), config variant (plugin present),
   gate pass/fail paths, runner group ordering.

### Implementation decisions and open questions

- Decided locally (reversible): stage names, record file names, gate
  threshold default 0.8 + no missing grades, planning-prompt wording,
  omit test on tg01.
- Open (user): none blocking; kind-arm second addition and pruning happen
  after the trial per the recorded rules.

### Documentation

- Suite test-plan/test-cases pages gain the two stages, arms, and the
  gate; the reproducing page's runner section already covers slicing;
  plugin README already documents the switch.

### Task checklist

- [x] Stage specs (landed September 28 with the wiring tests corrected
  to the new stage graph: `test_parented_stages_match_the_pipeline_graph`
  now expects three parented stages; the executor-existence and assembly
  tests skip the two in-flight executors via the documented
  PENDING_EXECUTORS set, which shrinks to empty when increment 2 lands)
- [x] Executors (increment 2, landed September 29: `run_planning_session`
  + `run_task_creation_from_plan` on the harness, with
  `PlanningRunValue`, `planning_session_identity`/`from_plan_identity`,
  `PLANNING_VARIANTS`/`CREATION_VARIANTS` + the planning suffix and the
  two creation asks, `compiled_delivery_evidence` now recording the
  actual `include_tasks` flag, and the writing turn's request overrides
  shallow-merging `include_tasks=True` over the planning turn's stored
  overrides; `PENDING_EXECUTORS` removed — executor-existence and
  assembly mechanics coverage fully restored, 233 tests green)
- [ ] Configuration wiring (which categories/scenarios run which arms;
  the stages enter configuration.json with their variants)
- [ ] Planning-session executor + validity (executor landed; the
  validity application — completed, non-empty, no mutations — rides the
  matrix/records wiring increment)
- [ ] From-plan executor + validity + omit instruction (executor and the
  omit ask landed; producer-validity application rides the matrix/records
  wiring increment)
- [ ] Agent-config variant (strip-thinking)
- [ ] Plan-content gate on planning runs
- [ ] Matrix/records/freeze/package wiring
- [ ] Runner stage groups
- [ ] Trial on tg01 + pruning + kind-arm selection
- [ ] Tests and docs

### Requirement verification

- Arm equivalence and non-loss: the existing deterministic suite (228
  tests) stays green with the new stages added, and a dry-run still
  enumerates every pre-existing case unchanged.
- Two-stage behavior: one real trial run on tg01 through the runner
  (planning gate recorded, from-plan delivery `tasks_occurrences == 1`,
  task files produced, unguided planning turn shows the tasks section
  absent from its compiled system message).
- Preserve-thinking: the strip-thinking config variant loads the plugin
  (unit) and both variants complete a real planning+creation cycle.
- Omit instruction: the instructed-omission case produces a
  requirements-only file (validity check), distinct from the canonical
  omit fixture stage.

### Additional implementation verification

- Runner ordering: new stages appear in `STAGE_GROUPS` between producers
  and assessments; unit test asserts the order.

## Implementation Notes

- September 29, 2026 — increment 2 landed (one commit): the two harness
  executors. `run_planning_session` builds a fresh
  `TaskGuidanceWorkspaceFactory` workspace, appends
  `PLANNING_SESSION_SUFFIX` to the scenario prompt, sets
  `include_tasks` per variant, records
  `task_guidance.planning`/`delivery`/`tool_metrics`, and returns
  `PlanningRunValue` (variant + response + tool stats + delivery; the
  response is the gate input). `run_task_creation_from_plan` continues
  the planning run (`continue_from`, parent workspace), records
  `task_guidance.from_plan` with the parent message count, filters tool
  calls to the writing turn, and returns a full `TaskRunValue` so every
  producer-validity consumer applies unchanged. Both go through
  `_execute` with variant- and parent-aware cache identities.
  `compiled_delivery_evidence` gained an `include_tasks` keyword so an
  unguided planning turn records `include_tasks: false` (its
  `tasks_occurrences` will be 0 from the compiled body itself). The
  omit-plan creation ask is the instructed no-execution-plan-section
  variant of the standard ask; validity application for both stages is
  downstream of the records wiring and stays open.
