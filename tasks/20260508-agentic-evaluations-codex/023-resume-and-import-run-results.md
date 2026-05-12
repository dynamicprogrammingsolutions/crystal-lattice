# Resume And Import Run Results

Add the simplest reusable support for resuming partially completed evaluation runs and importing prior task-instance results into a new run so larger manifests or chained workflows can avoid re-running work that already has valid results.

## Requirements checklist

- [x] Add core runner support for resuming from existing `results.jsonl` in a run directory, skipping already completed task instances and rebuilding aggregates/summaries from merged old+new results.
- [x] Keep repeat-instance identity stable and use `task_instance_id` as the canonical resume/import key.
- [x] Add workflow-level support for seeding a new run with selected prior results from another run, so a larger manifest or later stage can continue from already completed task instances without copying benchmark code.
- [x] Validate imported rows against the target run manifest so mismatched task payloads are rejected instead of silently reused.
- [x] Surface imported/resumed work clearly in reporting so actual executions and inherited/imported results can be distinguished.

Parent Task: `tasks/20260508-agentic-evaluations-codex/000-main.md`
Depends On: `tasks/20260508-agentic-evaluations-codex/017-repoqa-prompted-eval.md`
Depends On: `tasks/20260508-agentic-evaluations-codex/022-repeat-count-and-task-aggregation.md`

## Current state

The existing runner has only a shallow "resume" hook.

- `evaluations/benchmarks/repoqa_prompted/benchmark.py`
  - `_run_repoqa_prompted(...)` already accepts `--run-manifest` and passes `resume_run_manifest_path` into `run_repoqa_prompted_benchmark(...)`.
- `evaluations/benchmarks/repoqa_prompted/logic.py`
  - `run_repoqa_prompted_benchmark(...)` loads the prior `run-manifest.json` when `resume_run_manifest_path` is set.
  - It does **not** load prior `results.jsonl`.
  - It initializes `completed = []` and `next_index = 0`, then schedules tasks from the run manifest as if nothing had been completed.
  - It rewrites `task-aggregate.jsonl` and `summary.json` from only the results collected in the current process.
- `evaluations/src/agent_evaluations/repeated_runs.py`
  - `expand_task_payloads_with_repeats(...)` already creates stable repeated instance ids like `task-id#r1`, `task-id#r2`, ...
  - `task_instance_id(...)` already defines the canonical identifier that should be used as the resume/import key.
  - This stable identity means a future `repeat_count=5` run can safely reuse `#r1..#r3` from an earlier `repeat_count=3` run and only execute `#r4..#r5`.

## Why this matters

Two concrete use cases are currently blocked:

1. Partial continuation inside one run definition
   - Example: start a 100-task benchmark with `repeat_count=5`, complete only some task instances, then continue later without rerunning finished instances.

2. Seeding a new run from a prior smaller run
   - Example: reuse results from a `20 tasks x 3 repeats` run when creating a `100 tasks x 5 repeats` run.
   - Example: reuse already solved task instances when escalating a filtered workflow to a larger model.

The first use case should be implemented in the evaluation runner.
The second should be implemented in workflow/orchestration code by preparing a target run directory with imported rows, then letting normal resume logic take over.

## Simplest implementation direction

### 1. Core runner: resume from existing `results.jsonl`

Implement shared helper logic under `evaluations/src/agent_evaluations/` (either by extending `repeated_runs.py` or adding a dedicated helper module) to:

- load existing `results.jsonl`
- index rows by `task_instance_id`
- validate and deduplicate rows
- return:
  - existing result rows
  - completed instance ids
  - merged rows for aggregate/summary rebuilding

Then update `evaluations/benchmarks/repoqa_prompted/logic.py` so `run_repoqa_prompted_benchmark(...)`:

- loads existing `results.jsonl` before scheduling
- initializes `completed` from those rows
- skips any task payload whose `task_instance_id(...)` is already complete
- appends only new result rows
- rebuilds `task-aggregate.jsonl` and `summary.json` from the full merged result set

### 2. Validation rules for imported/resumed rows

At minimum, require that an imported or resumed row matches the current target task instance on:

- `task_instance_id`
- `task.task_id`
- `repeat_index`
- task payload identity
  - safest first version: exact equality of the stored `task` payload dict

If there is a mismatch, fail clearly instead of reusing the row.

### 3. Workflow layer: seed a new run with prior rows

Extend `evaluations/benchmarks/repoqa_prompted/chained_workflow.py` with a workflow command that:

- chooses a source run
- creates or targets a destination run directory / run manifest
- copies selected source rows into the destination `results.jsonl`
- then relies on the core resume feature to skip already completed task instances

Useful first version:

- support only importing *actual* prior rows where the same `task_instance_id` exists in the destination manifest
- do not synthesize inherited/assumed-success rows yet

That is sufficient for the practical case:

- reuse a `20 tasks x 3 repeats` run when scaling to `100 tasks x 5 repeats`

### 4. Later workflow enhancement: cross-profile inherited successes

After core resume/import works, a second workflow feature can synthesize imported success rows for larger-model stages.

Suggested metadata for those synthetic rows:

- `imported_result: true`
- `import_mode: "assumed_success_from_run"`
- `source_run_dir`
- `source_model`
- `source_stage`

This should remain a workflow-only feature so the core runner continues to reason only about actual rows in `results.jsonl`.

## Suggested test coverage

- Resume with existing `results.jsonl` and no new work remaining.
- Resume with partially completed repeated instances and only schedule missing instances.
- Resume when `repeat_count` increases and reuse prior `#r1..#rN` instance results.
- Reject imported rows whose stored task payload does not match the destination manifest task payload.
- Workflow-level seeding test that copies a subset of source rows into a destination run and confirms the resume layer skips those instances.

## Notes for the implementing agent

- Preserve the current `task_instance_id` scheme; it is already the right abstraction for resumability.
- Prefer rebuilding `task-aggregate.jsonl` and `summary.json` from `results.jsonl` rather than trusting any previously written aggregate file.
- Keep the core feature benchmark-agnostic where practical, but it is fine if `repoqa-prompted` adopts it first and the shared helper is extracted from there.

## Execution plan

Added during completion.

1. Add shared repeated-run resume/import helpers that can:
   - load existing `results.jsonl`
   - index rows by `task_instance_id`
   - validate row/task payload compatibility
   - provide merged result rows and completed instance ids
2. Update `repoqa-prompted` benchmark execution to:
   - preload prior results from the target run directory
   - skip already completed instances
   - rewrite aggregate and summary artifacts from the merged result set
3. Extend `chained_workflow.py` with a minimal seeding command for actual prior results only.
   - destination run manifest is prepared first
   - overlapping source rows are validated and copied into destination `results.jsonl`
   - no synthetic assumed-success imports in this phase
4. Add focused tests for:
   - repeated-run result loading and validation
   - benchmark resume behavior from existing rows
   - workflow seeding of overlapping rows
5. Smoke-test with the existing sample setup by:
   - generating a 25-task manifest
   - seeding it from the completed 20-task nano sample run
   - running/resuming so only the added 5 tasks execute

## Completion Notes

Added during completion.

- Implemented shared repeated-run helpers in `evaluations/src/agent_evaluations/repeated_runs.py` for:
  - loading existing `results.jsonl`
  - validating rows against target task instances
  - selecting overlapping rows for import
- Updated `evaluations/benchmarks/repoqa_prompted/logic.py` so resumed runs:
  - preload existing result rows
  - skip completed `task_instance_id`s
  - rewrite `task-aggregate.jsonl`
  - write summary counts for `preexisting_result_count`, `new_result_count`, `imported_result_count`, and `executed_result_count`
- Extended `evaluations/benchmarks/repoqa_prompted/chained_workflow.py` with:
  - `seed-run`
  - `run-stage --manifest-path ... --run-manifest ...`
- Added tests in `evaluations/tests/test_repoqa_prompted_resume_and_seed.py`
- Updated benchmark docs and the balanced config README to document resume and seeded continuation.

Smoke-test completed with the real sample config:

- Generated 25-task balanced manifest:
  - `evaluations/benchmarks/repoqa_prompted/config/openai_api_reasoning_none_balanced/manifests/repoqa-prompted-balanced-all-limit25-seed1.json`
- Seeded a new nano run from prior 20-task sample run:
  - source run: `evaluations/benchmarks/repoqa_prompted/config/openai_api_reasoning_none_balanced/results/nano-sample/repoqa-prompted/20260511T101417Z`
  - seeded run: `evaluations/benchmarks/repoqa_prompted/config/openai_api_reasoning_none_balanced/results/nano-sample/repoqa-prompted/20260511T122138Z`
- Verified resumed run behavior from `summary.json`:
  - `manifest_task_count = 25`
  - `task_instance_count = 75`
  - `preexisting_result_count = 60`
  - `new_result_count = 15`
  - `imported_result_count = 60`
  - `executed_result_count = 15`