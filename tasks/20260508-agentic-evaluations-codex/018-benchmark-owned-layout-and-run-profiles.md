# Benchmark-Owned Layout And Run Profiles

Refactor the `evaluations/` package so benchmark-specific code, docs, configs, and profiles live under benchmark-owned top-level directories, while the shared runner config is narrowed to agent/provider runtime concerns only.

Parent Task: `tasks/20260508-agentic-evaluations-codex/000-main.md`

Depends On:

- `tasks/20260508-agentic-evaluations-codex/015-benchmark-registry-refactor.md`
- `tasks/20260508-agentic-evaluations-codex/017-repoqa-prompted-eval.md`

## Requirements checklist

- [x] Introduce top-level benchmark directories under `evaluations/benchmarks/`, including at minimum:
  - `repoqa_agentic/`
  - `repoqa_prompted/`
- [x] Move benchmark-specific docs/configs/profiles into those benchmark directories.
- [x] Update benchmark discovery so the shared CLI scans benchmark-owned directories rather than depending only on `evaluations/src/agent_evaluations/benchmarks/`.
- [x] Preserve a safe fallback for runtime environments where the benchmark-owned source tree is not discoverable directly.
- [x] Define and implement a clearer boundary:
  - `config.json` contains agent/provider/plugin runtime setup
  - profiles contain evaluation run definition
- [x] Move benchmark-run-definition concerns into profiles, including where applicable:
  - release/download selection
  - manifest generation inputs
  - runtime backend
  - Docker settings
  - schedule
  - benchmark-specific execution knobs
- [x] Support using a profile to drive `download`, `manifest`, and `run`, not only `run`.
- [x] Remove duplicate Docker/schedule definitions between config and profile for the real prompted OpenAI API benchmark setup.
- [x] Reduce top-level `evaluations/README.md` to shared framework/runtime guidance and move benchmark-specific operational docs into benchmark-owned directories.
- [x] Make the shared `agent-evaluations` package runnable without manual `PYTHONPATH` setup by improving editable-install ergonomics, including:
  - a console-script entry point
  - correct runtime dependency declaration for shared imports
  - docs/examples updated to prefer installed usage over repo-local `PYTHONPATH` commands
- [x] Remove concrete benchmark implementation modules from `evaluations/src/agent_evaluations/` so that `src/agent_evaluations/` contains only shared framework code.
- [x] Move the remaining RepoQA agentic logic out of `src/` into benchmark-owned directories, including any RepoQA-specific shared helpers needed by both RepoQA benchmark modes.

## Scope and intent

This task is about ownership boundaries and filesystem layout, not new benchmark semantics.

The goal is to make it obvious:

- which files define the model/runtime stack
- which files define a particular evaluation run
- where benchmark-specific docs and configs live
- where the CLI discovers benchmark definitions from

## Intended boundary

### `config.json`

Should contain only what is needed to construct and run the model/application stack, for example:

- providers
- agents
- plugins
- mixins
- auth-related setup
- provider/runtime behavior such as flex processing, retries, reasoning, or usage extensions

### benchmark profile

Should contain the evaluation plan, for example:

- benchmark id
- manifest path or manifest-generation inputs
- release
- language or languages
- limit
- seed
- runtime backend
- Docker settings
- scheduling
- restart policy
- benchmark-specific execution settings

## Recommended directory shape

```text
evaluations/
  benchmarks/
    repoqa_agentic/
      README.md
      benchmark.py
      config/
        ...
    repoqa_prompted/
      README.md
      benchmark.py
      config/
        ...
```

The exact nesting can evolve, but benchmark-specific docs/config/profile assets should live with the benchmark rather than under one shared config area.

## Functional target

For the real prompted OpenAI API setup, the desired end state is:

- a benchmark-owned config directory under `evaluations/benchmarks/repoqa_prompted/...`
- no benchmark-specific `agentic_evaluations` knobs duplicated in `config.json`
- one profile that fully defines:
  - release/download inputs
  - manifest slice definition
  - Docker runtime selection
  - schedule
  - retry behavior

## Notes

- Keep the shared CLI and scheduler/runtime logic intact where possible.
- A compatibility fallback is acceptable during the transition if Docker/runtime environments still rely on package-relative benchmark discovery.
- This task should improve human discoverability and maintainability without breaking the working RepoQA benchmarks.