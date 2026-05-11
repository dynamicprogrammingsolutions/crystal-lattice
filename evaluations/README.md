# Agent Evaluations

Shared benchmark package for running evaluation tasks through `AgentApplication`.

This top-level directory owns the shared framework:

- CLI shell
- benchmark discovery
- config-dir loading
- run-profile loading
- shared scheduler/runtime logic
- Docker packaging and task execution
- shared result artifacts

Benchmark-specific docs, configs, and run presets should live under:

- `evaluations/benchmarks/<benchmark>/`

## Installation

Prefer an editable install over ad hoc `PYTHONPATH` usage:

```bash
pip install -e core/python
pip install -e evaluations
```

After that, use the console script:

```bash
agent-evaluations --help
```

The old `PYTHONPATH="evaluations/src:application/python:core/python:..." python -m agent_evaluations ...`
style is still useful as a repo-local fallback, but it should not be the primary documented workflow.

## Benchmark Layout

Preferred structure:

```text
evaluations/
  benchmarks/
    <benchmark>/
      README.md
      benchmark.py
      config/
        ...
```

The shared CLI discovers benchmark definitions from those benchmark-owned directories
when available, with a compatibility fallback for package-relative benchmark modules.

## Config vs Profile Boundary

### `config.json`

Use `config.json` only for model/application runtime setup, for example:

- providers
- plugins
- agents
- mixins
- auth-related setup
- provider/runtime behavior such as retries, flex processing, reasoning, or usage extensions

### profile

Use a benchmark run profile for the evaluation plan, for example:

- benchmark id
- manifest path or manifest-generation inputs
- release
- language or languages
- limit
- seed
- runtime backend
- Docker settings
- schedule
- restart policy
- benchmark-specific execution settings

Profiles may be used not only for `run`, but also to drive `download` and `manifest`.

## Config Dir Contract

An evaluation config directory may contain:

```text
<config-dir>/
  .env
  config.json
  AGENTS.md
  auth/
  profiles/
  manifests/
```

Only `config.json` is required by the shared framework.

`AGENTS.md` is optional and should only exist when the chosen benchmark/config
actually uses it.

If benchmark runner paths are not specified explicitly, the shared loader defaults to:

- `cache/`
- `results/`
- `manifests/`
- `workspaces/`
- `profiles/`

under the config directory.

## CLI Overview

Common command families:

```text
agent-evaluations download <benchmark> --config-dir <config-dir> [--profile <profile>]
agent-evaluations manifest <benchmark> --config-dir <config-dir> [--profile <profile>]
agent-evaluations container build --config-dir <config-dir> [--profile <profile>]
agent-evaluations container warm-cache --config-dir <config-dir> [--profile <profile>]
agent-evaluations run <benchmark> --config-dir <config-dir> [--profile <profile>]
```

Benchmark-specific command examples should live in the benchmark README.

## Docker Runtime

Docker execution uses the same scheduler, manifests, retries, and scoring logic as host execution.

- Build the runner image with `container build`.
- Warm the shared plugin cache once with `container warm-cache` before a cold parallel Docker run, or rely on benchmark runs to do this automatically.
- Docker image builds use a clean tracked-files source bundle created from the current Git revision.
- The evaluation runner itself is installed from a separately built wheel artifact.
- Each task runs in its own short-lived container.
- The config directory is mounted at `/config`.
- The task workspace is mounted separately from results.
- Results are mounted at `/results`.
- `--workspace-root` inside the container uses the mounted workspace path, not the container working directory.
- The bundled default Dockerfile lives at `evaluations/docker/RepoqaRunner.Dockerfile`.

## Output Artifacts

Each run produces:

- `run-manifest.json`
- `results.jsonl`
- `summary.json`

For reproducible experiments, treat the manifest plus the config dir plus the selected profile as the benchmark definition.

## See Also

- shared framework guidance: `evaluations/AGENTS.md`
- benchmark-specific setup: `evaluations/benchmarks/<benchmark>/README.md`
