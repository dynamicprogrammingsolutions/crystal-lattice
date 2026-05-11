# RepoQA Prompted Guide

Use this file for the `repoqa-prompted` benchmark specifically.

## Purpose

`repoqa-prompted` is the single-prompt RepoQA mode.

It:

- builds one large prompt from repository context plus the needle description
- disables tools for the request
- expects plain function source code output
- scores the normalized answer with the shared RepoQA semantic scorer

## Key files

- `evaluations/benchmarks/repoqa_prompted/benchmark.py`
- `evaluations/benchmarks/repoqa_prompted/logic.py`
- `evaluations/benchmarks/repoqa_shared/common.py`

## Important behavior

This benchmark is no-tools by design.

It relies on:

- request override `disable_all_tools: true`
- `plugins.tool_gating_feature.ToolGatingFeature`

Do not try to disable tools with `tools: []`.

## Prompt/context behavior

The runner:

- loads the target repo from the RepoQA release payload
- orders files deterministically
- truncates to the configured context budget
- writes `PROMPT.txt`
- stores prompt metadata in `meta.json`

Important prompt metadata fields:

- `included_paths`
- `included_file_count`
- `target_path`
- `target_in_context`
- `context_budget_chars`
- `context_chars_used`
- `truncated`

## Fairness rule

If the target file is missing from prompt context:

- the request is not sent
- the task instance is marked `skipped_missing_target_context`
- it is excluded from the main accuracy denominator

This is why prompted summaries expose:

- `eligible_task_count`
- `excluded_missing_target_context_count`
- `raw_accuracy_over_manifest`

## Answer normalization

The model returns plain code, not JSON.

`logic.py` extracts the main code block or plain function text, infers the symbol, and then passes:

- `path`
- `symbol`
- `code`

into the shared RepoQA scorer.

## Repeated runs

Repeated runs are fully supported here.

Useful aggregate fields in `task-aggregate.jsonl`:

- `matched_instance_count`
- `eligible_instance_count`
- `success_rate`
- `excluded_missing_target_context_count`
- `outcome_counts`
- `instance_results`

This is the preferred input for custom follow-up filtering scripts.

## Where to investigate

If behavior looks wrong:

- prompt construction: `build_repoqa_prompted_prompt(...)`
- fairness exclusion: `_target_in_prompt_context(...)`
- answer parsing: `parse_repoqa_prompted_answer(...)`
- per-task retries/results: `run_repoqa_prompted_task_with_restarts_in_workspace(...)`
- run expansion and summary writing: `run_repoqa_prompted_benchmark(...)`

## Common gotchas

- target omission from context is not a model failure
- repeated task instances must use `repeat_count`, not duplicated manifest entries
- if tools still appear, the selected config is missing `ToolGatingFeature`