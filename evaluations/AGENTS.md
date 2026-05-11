# Evaluations Agent Guide

Use this file for shared runner behavior. For benchmark-specific behavior, read:
- `evaluations/benchmarks/<benchmark>/AGENTS.md`
- `evaluations/benchmarks/<benchmark>/README.md`

## Purpose
The `evaluations/` package provides one shared CLI, benchmark discovery, config/profile loading, scheduling, host/Docker execution, repeated-run expansion, and shared result artifacts.

Framework code:
- `evaluations/src/agent_evaluations/`

Benchmark definitions:
- `evaluations/benchmarks/`

Most useful shared files:
- `evaluations/src/agent_evaluations/benchmark_registry.py`
- `evaluations/src/agent_evaluations/cli.py`
- `evaluations/src/agent_evaluations/cli_helpers.py`
- `evaluations/src/agent_evaluations/config_dir.py`
- `evaluations/src/agent_evaluations/container_backend.py`
- `evaluations/src/agent_evaluations/repeated_runs.py`
- `evaluations/src/agent_evaluations/scheduler.py`
- `evaluations/src/agent_evaluations/utils.py`

Useful tests:
- `evaluations/tests/`

Docker image:
- `evaluations/docker/RepoqaRunner.Dockerfile`

## Mental model
Two layers:
1. Shared framework
   - CLI shell
   - benchmark discovery
   - config/profile loading
   - scheduling
   - host vs Docker execution
   - repeated-run expansion
   - result writing
2. Benchmark-specific logic
   - dataset download
   - manifest generation
   - task execution
   - parsing and scoring

New benchmarks should plug into the shared framework through the registry, not by editing `cli.py`.

## Benchmark registration
Preferred layout:

```text
evaluations/
  benchmarks/
    <benchmark>/
      AGENTS.md
      README.md
      benchmark.py
      logic.py
      config/
```

Each `benchmark.py` exports `BENCHMARK`.

When adding or debugging one benchmark, start with:
- `evaluations/benchmarks/<benchmark>/benchmark.py`
- `evaluations/benchmarks/<benchmark>/logic.py`
- `evaluations/benchmarks/<benchmark>/AGENTS.md`

## Config vs profile
`config.json` should hold runtime setup:
- providers
- plugins
- agents
- auth/runtime features

Profiles should hold the evaluation plan:
- manifest path or manifest-generation inputs
- agent id
- model override
- repeat count
- runtime backend
- Docker settings
- schedule
- retry settings

Useful resolved roots:
- `cache_root`
- `results_root`
- `manifests_root`
- `workspace_root`
- `profiles_root`

These may be siblings. Do not assume results live under the config dir.

## CLI structure
Common command families:
- `agent-evaluations download <benchmark> ...`
- `agent-evaluations manifest <benchmark> ...`
- `agent-evaluations run <benchmark> ...`
- `agent-evaluations container build ...`
- `agent-evaluations container warm-cache ...`
- `agent-evaluations internal run-single <benchmark> ...`

Use `agent-evaluations --help` and per-command `--help` for exact syntax.
If the CLI wiring is unclear, check:
- `evaluations/src/agent_evaluations/cli.py`
- `evaluations/src/agent_evaluations/cli_helpers.py`
- `evaluations/benchmarks/<benchmark>/benchmark.py`

Most useful run arguments:
- `--config-dir`
- `--profile`
- `--manifest-path`
- `--agent-id`
- `--model`
- `--runtime-backend`
- `--repeat-count`
- `--max-task-restarts`

Most useful schedule arguments:
- `--window-minutes`
- `--tasks-per-window`
- `--max-parallel-tasks`
- `--randomize-task-starts`
- `--random-seed`

## Host vs Docker
Host mode runs tasks locally through `AgentApplication`.

Docker mode:
- host prepares task payloads and paths
- container executes one prepared task
- results are written back through mounted paths

Important Docker rules:
- config, workspace, and results are separate mounts
- `--workspace-root` inside the container must use the mounted workspace path
- `task_workdir` is only the container process working directory
- image builds use a clean Git-tracked source bundle plus a built `agent_evaluations` wheel

For Docker behavior, inspect:
- `evaluations/src/agent_evaluations/container_backend.py`
- `evaluations/docker/RepoqaRunner.Dockerfile`

## Repeated runs
`repeat_count` is a shared runner feature.

Behavior:
- each logical task is expanded into repeated task instances in the run manifest
- each instance gets:
  - `task_id`
  - `task_instance_id`
  - `repeat_index`
  - `repeat_count`
- runtime storage uses `task_instance_id` to avoid collisions

Do not repeat tasks by duplicating raw entries inside a benchmark manifest. Use `repeat_count`.
For repeat expansion and aggregation behavior, inspect:
- `evaluations/src/agent_evaluations/repeated_runs.py`

## Result artifacts
Each run produces:
- `run-manifest.json`
- `results.jsonl`
- `task-aggregate.jsonl`
- `summary.json`

Meaning:
- `run-manifest.json`: actual planned run, including expanded task instances
- `results.jsonl`: one row per executed task instance
- `task-aggregate.jsonl`: one row per logical task aggregated across repeats
- `summary.json`: run-level rollup

Most useful repeated-run fields:
- `task_instance_id`
- `repeat_index`
- `repeat_count`
- `matched_instance_count`
- `eligible_instance_count`
- `success_rate`
- `outcome_counts`
If scheduling behavior matters, inspect:
- `evaluations/src/agent_evaluations/scheduler.py`