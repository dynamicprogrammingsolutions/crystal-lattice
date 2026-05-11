# Evaluations Agent Guide

This directory contains the shared benchmark runner framework for evaluation tasks that execute through `AgentApplication`.

Use this guide when:

- adding a new benchmark
- modifying benchmark execution behavior
- debugging host or Docker benchmark runs
- investigating scoring, manifests, or config-dir issues

## Purpose

The `evaluations/` package provides:

- one shared CLI
- one config-dir convention
- one scheduling/runtime framework
- benchmark-specific implementations registered through a benchmark registry

Current benchmarks:

- `repoqa`
  - agentic workspace + tools
  - JSON answer shape
- `repoqa-prompted`
  - single large prompt
  - no tools
  - plain function code output

Both benchmarks use the same RepoQA task data and the same semantic scoring logic.

## Key paths

Core framework:

- `evaluations/src/agent_evaluations/cli.py`
- `evaluations/src/agent_evaluations/benchmark_registry.py`
- `evaluations/src/agent_evaluations/cli_helpers.py`
- `evaluations/src/agent_evaluations/config_dir.py`
- `evaluations/src/agent_evaluations/container_backend.py`
- `evaluations/src/agent_evaluations/scheduler.py`
- `evaluations/src/agent_evaluations/utils.py`

Benchmark registration:

- preferred: `evaluations/benchmarks/<benchmark>/benchmark.py`
- compatibility fallback: `evaluations/src/agent_evaluations/benchmarks/`

Current benchmark logic:

- `evaluations/benchmarks/repoqa_agentic/logic.py`
- `evaluations/benchmarks/repoqa_prompted/logic.py`
- `evaluations/benchmarks/repoqa_shared/common.py`

Tests:

- `evaluations/tests/`

Docker runner image:

- `evaluations/docker/RepoqaRunner.Dockerfile`

## Mental model

There are two layers:

1. Shared framework
   - CLI shell
   - config-dir loading
   - profiles
   - scheduling
   - Docker build/runtime
   - result writing

2. Benchmark-specific logic
   - dataset download
   - manifest generation
   - prompting/workspace construction
   - single-task execution
   - parsing and scoring

New benchmarks should plug into the shared framework through the registry, not by editing `cli.py` directly.

## Benchmark registration model

Benchmarks are discovered from benchmark-owned directories under:

- `evaluations/benchmarks/`

Each benchmark module exports:

- `BENCHMARK`

The registry loads benchmark modules automatically. Benchmark-specific CLI subcommands are registered from those modules.

That means adding a benchmark should not require direct edits to:

- `evaluations/src/agent_evaluations/cli.py`

## Command families

Every benchmark should fit this command shape:

- `download <benchmark>`
- `manifest <benchmark>`
- `run <benchmark>`
- `internal run-single <benchmark>`

The `internal run-single` path is the container/worker entrypoint for executing one prepared task payload.

## Config-dir contract

Benchmark runs are driven by a config directory. Expected files:

- `config.json`
- optional `.env`
- optional `AGENTS.md`
- optional `auth/`
- optional `profiles/`

`AGENTS.md` is only needed when the selected benchmark/config actually uses it.
For example, `repoqa-prompted` does not require a config-dir `AGENTS.md`.

Important roots:

- `cache_root`
- `results_root`
- `manifests_root`
- `workspace_root`
- `profiles_root`

These roots may be siblings. Do not assume results live under config.

Preferred boundary:

- `config.json` for provider/agent/plugin runtime setup
- profile for the evaluation plan, including schedule and Docker

The shared loader still supports config-level path overrides when needed, but benchmark-specific execution settings should prefer profiles.

## How to add a benchmark

1. Add benchmark-owned files under `evaluations/benchmarks/<benchmark>/`
2. Add a benchmark registration module there as `benchmark.py`
3. Keep shared or reusable logic under `evaluations/src/agent_evaluations/` as needed
4. Export `BENCHMARK`
5. Implement benchmark-owned handlers for:
   - download
   - manifest
   - run
   - internal run-single
6. Add tests under `evaluations/tests/`

Recommended tests:

- manifest determinism
- prompt/workspace construction
- parsing/scoring
- fixture-backed host run
- Docker regression or smoke coverage where practical

## Runtime model

Host mode:

- scheduler runs tasks locally
- task logic executes through `AgentApplication`

Docker mode:

- host creates task payloads and result paths
- host-side human usage should prefer the installed `agent-evaluations ...` console script
- container execution currently uses `python -m agent_evaluations internal run-single <benchmark> ...` as an implementation detail
- results are written back into the mounted results directory

Separate mounts are used for:

- config
- workspace
- results

Do not couple workspace paths or result paths to config-dir-relative assumptions.

## Docker notes

The Docker image build uses:

- a clean Git-tracked source bundle for stable runtime code
- a separately built `agent_evaluations` wheel

The image does not depend on `evaluations/` being present in the clean tracked-files snapshot because the evaluation package is installed from the wheel artifact.

Important workspace rule:

- `--workspace-root` must point to the mounted workspace path
- `task_workdir` is only the process working directory

Do not assume those are the same.

When validating Docker changes, prefer a real fixture-backed smoke run in addition to unit tests.

## Tools vs no-tools benchmarks

Agentic benchmarks may use tools and workspace overrides.

Prompted/no-tools benchmarks must use the supported tool-gating mechanism:

- set `disable_all_tools: true` in request overrides
- require `plugins.tool_gating_feature.ToolGatingFeature`

Do not rely on:

- `tools: []`

That does not disable plugin-provided tools.

For no-tools benchmarks, verify the effective request config actually exposes zero tools, for example by checking:

- `core.get_tool_schemas(effective_config) == []`

The prompted RepoQA runner already performs this preflight and fails clearly if tool gating is not active for the chosen agent/config.

## Result artifacts

Each run should produce:

- `run-manifest.json`
- `results.jsonl`
- `summary.json`

Keep benchmark mode explicit in summary metadata so custom modes are not confused with official benchmark results.

Per-task results should preserve enough information to debug failures, such as:

- parsed answer
- raw assistant output
- score details
- tool-call counts
- benchmark-specific metadata

## Current benchmark behavior

`repoqa`:

- materializes a repo workspace
- allows tool use
- expects JSON answer with:
  - `path`
  - `symbol`
  - `code`

`repoqa-prompted`:

- builds one large repo context prompt
- disables tools through `ToolGatingFeature`
- expects plain function code output
- normalizes the result into the same scorer input shape used by `repoqa`
- supports deterministic `language="all"` selection via balanced round-robin interleaving across languages
- can surface usage/cost metadata in task results and summaries when provided by the OpenAI Responses stack

## Testing commands

Main suite:

```bash
pytest evaluations/tests -q
```

When changing Docker behavior:

- run targeted container backend tests
- run a real fixture-backed Docker smoke if possible

When changing no-tools behavior:

- use a tool-enabled fixture config in tests
- assert tool gating is truly honored, not just that no tool call happened by chance

## Known gotchas

- `tools: []` does not disable plugin tools.
- `disable_all_tools` only works when `plugins.tool_gating_feature.ToolGatingFeature` is enabled in the runtime.
- Docker image tag mismatches can make smoke runs use stale code.
- Docker `no space left on device` often means Docker-internal cache pressure, not host disk exhaustion.
- Results, workspaces, and config roots may be separate paths.

## Suggested first steps

If adding a benchmark:

- read `benchmark_registry.py`
- read one existing registration module in `benchmarks/`
- read one existing benchmark logic module

If debugging a run:

- inspect `run-manifest.json`
- inspect `summary.json`
- inspect one task result in `results.jsonl`
- confirm the selected config dir and agent id

If debugging Docker:

- confirm image tag
- confirm mounts
- confirm `internal run-single <benchmark>` command

If debugging no-tools mode:

- confirm `ToolGatingFeature` is enabled
- confirm effective tool schemas are empty for the request