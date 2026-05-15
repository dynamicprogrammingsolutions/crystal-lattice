# Repeat Count And Task Aggregation

Add `repeat_count` as a first-class run feature for evaluations so one benchmark run can execute each logical task multiple times, store each repetition separately, and emit a per-task aggregation artifact that downstream scripts can use to build follow-up manifests.

Parent Task: `tasks/20260508-agentic-evaluations-codex/000-main.md`

Depends On:

- `tasks/20260508-agentic-evaluations-codex/018-benchmark-owned-layout-and-run-profiles.md`
- `tasks/20260508-agentic-evaluations-codex/019-repoqa-prompted-context-eligibility.md`
- `tasks/20260508-agentic-evaluations-codex/021-shared-parser-backed-code-comparison.md`

## Requirements checklist

- [x] Add `repeat_count` as a run-level setting with support in:
  - CLI
  - profiles
  - persisted run manifests
- [x] Keep each repetition as a separate executable task instance rather than duplicating raw tasks in the benchmark manifest.
- [x] Give each task instance a unique runtime identity, including at minimum:
  - `task_id`
  - `task_instance_id`
  - `repeat_index`
  - `repeat_count`
- [x] Use `task_instance_id` for runtime storage paths so repeated instances do not collide in:
  - workspaces
  - task-input artifacts
  - task-output artifacts
  - any other task-instance-specific runtime files
- [x] Preserve per-instance raw execution output in `results.jsonl`.
- [x] Add a separate per-task aggregation artifact that groups repeated instances by logical `task_id`.
- [x] Include enough aggregate fields for custom follow-up scripts to filter tasks without needing to re-derive everything from raw rows.
- [x] Update `summary.json` so it reports both:
  - instance-level totals
  - logical-task-level repeated-run aggregates
- [x] Ensure prompted exclusion states such as `skipped_missing_target_context` aggregate correctly.
- [x] Keep host and Docker backends working with repeated task instances.
- [x] Update human docs and agent docs so the repeated-run workflow is discoverable and correctly explained.
- [x] Add regression tests for run-manifest expansion, instance path isolation, aggregation output, and repeated-run benchmark execution.

## Implementation plan

### 1. Run-level repeat configuration

Add `repeat_count` to:

- common run CLI arguments
- run profile payloads
- persisted run manifests

Behavior:

- default to `1`
- apply to both `repoqa` and `repoqa-prompted`

### 2. Expand logical tasks into task instances in the run manifest

Do not duplicate tasks in the benchmark manifest itself.

Instead, when creating the run manifest:

- keep the logical task metadata
- expand each task into `repeat_count` runnable instances

Each instance should include:

- `task_id`
- `task_instance_id`
- `repeat_index`
- `repeat_count`
- `planned_start_at`

Example:

- logical task: `abc123`
- instances:
  - `abc123#r1`
  - `abc123#r2`
  - `abc123#r3`

### 3. Use task-instance identities for runtime paths

All per-execution paths should key off `task_instance_id`, not only `task_id`.

This includes:

- workspace directories
- Docker task-input files
- Docker task-output files
- any per-instance session or temp paths

This is required to avoid collisions when repeats are present in a single run.

### 4. Preserve per-instance raw results

Keep `results.jsonl` as one row per executed instance.

Each row should include at least:

- `task_id`
- `task_instance_id`
- `repeat_index`
- `repeat_count`
- all existing score/outcome/cost/metadata fields

### 5. Add a per-task aggregation artifact

Add a new artifact, preferably:

- `task-aggregate.jsonl`

with one row per logical task.

Each aggregate row should include:

- logical task metadata
- `repeat_count`
- `completed_instance_count`
- `eligible_instance_count`
- `matched_instance_count`
- `success_rate`
- `excluded_missing_target_context_count`
- per-outcome counts
- cost totals and averages
- a compact per-instance breakdown suitable for custom scripts

This artifact is the main output for downstream scripted filtering.

### 6. Update run summaries

Update `summary.json` to expose both instance-level and logical-task-level metrics.

Suggested fields:

- `repeat_count`
- `manifest_task_count`
- `task_instance_count`
- `logical_task_count`
- `logical_tasks_with_all_successes`
- `logical_tasks_with_any_success`
- `logical_task_average_success_rate`
- existing instance-level accuracy fields
- cost totals/averages

For prompted runs, preserve:

- `eligible_task_count`
- `excluded_missing_target_context_count`

and make denominator semantics explicit.

### 7. Keep scheduling semantics simple

Treat repeated instances as ordinary scheduled units.

That means:

- scheduling applies to task instances
- repeats may be interleaved with other tasks depending on planned starts and parallelism

Do not add special back-to-back repeat scheduling in this task.

### 8. Share the aggregation logic where practical

Introduce shared helpers for:

- expanding repeated task instances
- aggregating per-instance result rows by logical `task_id`

Benchmark-specific runners can call those helpers when writing results and summaries.

### 9. Test coverage

Add tests for:

- run-manifest expansion with `repeat_count > 1`
- task-instance-specific runtime paths
- aggregation artifact correctness
- prompted omitted-target aggregation behavior
- Docker repeated-instance filename/path isolation
- a fixture-backed repeated benchmark run

### 10. Documentation updates

Update:

- `evaluations/README.md`
- `evaluations/AGENTS.md`
- benchmark-specific README files where applicable

to explain:

- what `repeat_count` does
- how repeated runs are stored
- how to use `task-aggregate.jsonl`
- that custom scripts should filter from the aggregate artifact, not by duplicating tasks inside one manifest

## Notes

- Native manifest filtering is out of scope for this task.
- The key design constraint is avoiding collisions by introducing task-instance identities.
- The final result should make “small-model repeated screening, then script-generated smaller manifest for a larger model” a straightforward workflow.