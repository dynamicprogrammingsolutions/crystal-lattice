# Benchmark Registry Refactor

Refactor the shared `evaluations/` package so that new benchmarks can be added without editing `evaluations/src/agent_evaluations/cli.py` directly. Keep the current RepoQA benchmark behavior intact while introducing a lightweight benchmark registration/discovery model.

Parent Task: `tasks/20260508-agentic-evaluations-codex/000-main.md`

Depends On: `tasks/20260508-agentic-evaluations-codex/010-repoqa-agentic-eval.md`

## Requirements checklist

- [ ] Introduce a lightweight benchmark registration/discovery layer under `evaluations/src/agent_evaluations/`.
- [ ] Refactor CLI construction so benchmark-specific subcommands are registered by benchmarks rather than hardcoded in `cli.py`.
- [ ] Preserve the existing shared commands and behavior:
  - `auth ...`
  - `container build`
  - config-dir loading
  - profiles
  - scheduler
  - Docker image build/runtime config
- [ ] Move the current RepoQA benchmark command wiring onto the new registry without changing RepoQA behavior.
- [ ] Support benchmark-registered subcommands for all four command families:
  - `download <benchmark>`
  - `manifest <benchmark>`
  - `run <benchmark>`
  - `internal run-single <benchmark>`
- [ ] Ensure Docker internal execution dispatch no longer depends on `cli.py` hardcoding RepoQA as the only benchmark.
- [ ] Add tests covering benchmark discovery, parser registration, and internal benchmark dispatch.

## Scope and intent

This is intentionally a small structural refactor, not a new plugin system.

The goal is:

- adding a new benchmark should require adding a new benchmark module
- benchmark-specific CLI registration should live with the benchmark
- `cli.py` should not need a direct code change for each new benchmark

Do **not** over-engineer this into:

- abstract base classes with large inheritance trees
- Python packaging entry-point plugins
- a second benchmark framework parallel to the current one

## Functional target

After this refactor, the current RepoQA benchmark should still expose commands equivalent to:

```text
python -m agent_evaluations download repoqa --config-dir ...
python -m agent_evaluations manifest repoqa --config-dir ...
python -m agent_evaluations run repoqa --config-dir ...
python -m agent_evaluations internal run-single repoqa --config-dir ...
```

But those commands should be registered through a benchmark definition/discovery path rather than hardcoded directly in `cli.py`.

## Recommended implementation approach

### 1. Add a benchmark registry module

Create a small shared registry module, for example:

- `evaluations/src/agent_evaluations/benchmark_registry.py`

It should define:

- a lightweight benchmark definition type, likely a dataclass of callables
- benchmark discovery/loading
- lookup by benchmark id

### 2. Add a benchmarks package

Create a package such as:

- `evaluations/src/agent_evaluations/benchmarks/`

Each benchmark module in that package should export one benchmark definition symbol, for example:

- `BENCHMARK`

Discovery should load benchmark modules from this package automatically so that future benchmarks do not require edits to `cli.py`.

### 3. Refactor RepoQA CLI integration into a benchmark registration module

Keep the existing RepoQA logic module:

- `evaluations/src/agent_evaluations/repoqa.py`

Add a benchmark registration/adapter module, for example:

- `evaluations/src/agent_evaluations/benchmarks/repoqa_agentic.py`

This module should:

- register `download repoqa`
- register `manifest repoqa`
- register `run repoqa`
- register `internal run-single repoqa`

by calling through to the existing RepoQA logic.

### 4. Keep shared parser helpers central

If useful, extract shared CLI argument helpers into:

- `cli.py`
- or a small `cli_helpers.py`

Examples of shared benchmark argument helpers:

- common run args
- schedule args
- runtime backend args
- common manifest args

Benchmarks may then reuse these helpers when registering their own subcommands.

### 5. Keep Docker image build shared

Do not refactor away the shared Docker packaging/runtime pieces in:

- `evaluations/src/agent_evaluations/container_backend.py`

This task should only make benchmark dispatch extensible.

### 6. Make internal run-single benchmark-extensible

The `internal run-single` subtree should be benchmark-registered just like `download`, `manifest`, and `run`.

This is important so that Docker execution for a future benchmark can work without editing `cli.py`.

## Docker dispatch note

The current Docker image build/runtime support is shared, but internal benchmark execution is still effectively benchmark-specific. This task should make the benchmark selection portion extensible, even if the actual host-side task runner functions remain benchmark-specific.

It is acceptable if benchmark-specific container execution helpers remain separate for now, as long as:

- the CLI/internal dispatch path is registry-driven
- future benchmarks can add their own internal run-single entry without editing `cli.py`

## Expected outcome

At the end of this task:

- `cli.py` still owns shared top-level command families
- benchmark-specific subcommands are registered through the benchmark registry
- RepoQA behavior remains unchanged
- a second benchmark can be added without directly changing `cli.py`

## Tests

Add tests covering at minimum:

- benchmark discovery loads the RepoQA benchmark
- parser construction includes RepoQA commands via registry registration
- `internal run-single repoqa` dispatch still works
- unknown or duplicate benchmark ids fail clearly

## Notes

- Keep this task focused on extension structure, not new benchmark behavior.
- Avoid folding the upcoming prompted RepoQA implementation into this task.
- The success criterion is that the next benchmark task can be added through benchmark modules and shared registry hooks rather than direct CLI edits.