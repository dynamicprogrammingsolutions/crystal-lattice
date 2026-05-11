# RepoQA Agentic Guide

Use this file for the `repoqa` benchmark specifically.

## Purpose

`repoqa` is the workspace-and-tools RepoQA mode.

It:

- materializes the repository into a task workspace
- lets the agent inspect files with tools
- expects a strict JSON answer
- scores the answer against ground truth using shared semantic comparison

## Key files

- `evaluations/benchmarks/repoqa_agentic/benchmark.py`
- `evaluations/benchmarks/repoqa_agentic/logic.py`
- `evaluations/benchmarks/repoqa_shared/common.py`

## Answer contract

The model is expected to return exactly one JSON object with:

- `path`
- `symbol`
- `code`

`logic.py` parses the final assistant text as JSON and then calls the shared RepoQA scorer.

## Workspace model

Per task, the runner creates a workspace containing:

- `repo/`
- `TASK.md`
- `meta.json`
- `submission/`

The task prompt instructs the agent to inspect `repo/` and identify the target function.

## Important behavior

- this benchmark is tool-using by design
- per-request overrides set `working_directory` and `allowed_paths`
- repeated runs use distinct `task_instance_id` values so workspaces do not collide

## Useful result fields

Per-instance rows in `results.jsonl` include:

- `task`
- `task_instance_id`
- `repeat_index`
- `repeat_count`
- `parsed_answer`
- `score`
- `final_assistant_text`
- `tool_call_count`

`task-aggregate.jsonl` groups repeated instances by logical `task_id`.

## Where to investigate

If a run behaves unexpectedly:

- prompt/workspace creation: `materialize_repoqa_workspace(...)`
- final parsing: `parse_repoqa_answer(...)`
- retries and per-task result payloads: `run_repoqa_task_with_restarts_in_workspace(...)`
- run expansion and summary writing: `run_repoqa_benchmark(...)`

## Common gotchas

- malformed JSON is a parse failure, even if the code is otherwise correct
- repeating the same logical task must happen through `repeat_count`, not duplicated manifest entries
- Docker task-input and task-output files are keyed by `task_instance_id`