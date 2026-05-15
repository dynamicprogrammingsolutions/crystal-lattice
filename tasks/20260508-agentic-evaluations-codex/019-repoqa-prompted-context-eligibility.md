# RepoQA Prompted Context Eligibility

Detect when a `repoqa-prompted` task omits the target file from prompt context because of context limits, skip the model request in that case, and exclude those tasks from the main accuracy denominator while still reporting them clearly.

Parent Task: `tasks/20260508-agentic-evaluations-codex/000-main.md`

Depends On:

- `tasks/20260508-agentic-evaluations-codex/017-repoqa-prompted-eval.md`
- `tasks/20260508-agentic-evaluations-codex/018-benchmark-owned-layout-and-run-profiles.md`

## Requirements checklist

- [x] Detect before request execution whether the target file path is present in the prompted context.
- [x] When the target file is omitted because of prompt-context limits, do not send the model request.
- [x] Record a distinct result outcome for this case, separate from model mismatches and runtime failures.
- [x] Mark these tasks as not eligible for the main accuracy denominator.
- [x] Update prompted summaries to show both:
  - eligible-task accuracy
  - excluded-task counts due to missing target context
- [x] Preserve enough per-task metadata to explain why a task was excluded.
- [x] Add tests proving omitted-target tasks skip the request path and are excluded from the main accuracy stats.

## Implementation plan

1. Add a prompted-task eligibility check based on prompt metadata:
   - target path included in `included_paths`
   - truncation/context-limit diagnostics retained
2. Short-circuit prompted execution before request send when the target is absent from context.
3. Add explicit result fields such as:
   - `outcome`
   - `eligible_for_accuracy`
   - `failure_category`
4. Update prompted summary generation to report:
   - `manifest_task_count`
   - `eligible_task_count`
   - `excluded_missing_target_context_count`
   - `accuracy`
   - `raw_accuracy_over_manifest`
5. Add regression tests for:
   - excluded omitted-target task
   - normal eligible task
   - summary denominator behavior

## Notes

- This task is specific to `repoqa-prompted`, where context truncation can make a task unfair before any model call.
- Runtime failures and real model mismatches should remain in the eligible-task denominator.