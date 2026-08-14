# Terminal-Bench Docs And Stats Mapper Protocol

Write the terminal-bench evaluation docs (AGENTS.md, README.md), update the
top-level `evaluations/` docs for the new multi-evaluation layout, and add
the `stats_mapper` Protocol stub that Option C will use later for
cross-harness output comparability.

Parent Task: `tasks/20260623-terminal-bench-evaluation/000-main.md`

Depends On: `tasks/20260623-terminal-bench-evaluation/010-evaluations-restructure.md`

## Requirements checklist

- [ ] `evaluations/evaluations/terminal_bench/AGENTS.md` documents the
  adapter contract, the setup requirements (harbor, Docker, Ollama), the
  config/profile structure, and the key files to inspect when debugging.
- [ ] `evaluations/evaluations/terminal_bench/README.md` has a quickstart
  (install, pre-flight, run commands), a config overview, and pointers to
  the AGENTS.md for details.
- [ ] `evaluations/README.md` documents the new multi-evaluation layout:
  the code/data split, the per-evaluation contract, how to add a new
  evaluation, and the shared framework boundaries.
- [ ] `evaluations/AGENTS.md` updates the discovery section and the "where
  to change what" section for the new `evaluations/evaluations/<name>/`
  and `src/agent_evaluations/evaluations/<name>/` paths.
- [ ] `evaluations/src/agent_evaluations/stats_mapper.py` defines a
  `StatsMapper` Protocol (or ABC) with a method that maps our
  `results.jsonl` / `summary.json` into a benchmark-native summary format,
  documented as the extension point for Option C.
- [ ] The `StatsMapper` Protocol has a docstring explaining when to
  implement it (cross-harness comparability) and what the output shape
  should be (benchmark-native, e.g. harbor's `JobResult` shape for
  terminal-bench).

## Scope and intent

Documentation and the Option C extension hook. No terminal-bench mapper
implementation is required — only the Protocol definition so a future
`terminal_bench_native/` evaluation (Option C) can plug in cleanly.

**In scope:**
- Terminal-bench `AGENTS.md` + `README.md`.
- Top-level `evaluations/README.md` + `AGENTS.md` updates.
- `stats_mapper.py` Protocol stub.

**Out of scope:**
- A terminal-bench `StatsMapper` implementation (deferred to Option C).
- Updating the existing `tasks/20260508-agentic-evaluations-codex/` task
  files (they're historical; the user said to keep them intact).

## Execution plan

Status: Approved

### `evaluations/evaluations/terminal_bench/AGENTS.md`

Structure (mirror the RepoQA AGENTS.md style):

```markdown
# Terminal-Bench Evaluation Guide

## Purpose
Run Terminal-Bench 2.1 tasks through our AgentApplication via a Harbor
BaseAgent adapter (Option B).

## Architecture
- Harbor runs each task in a Docker container and runs the verifier.
- Our adapter (BaseAgent subclass) runs in the harbor host process.
- Our AgentApplication drives the LLM; a single `bash` tool delegates to
  `environment.exec` in the container.

## Key files
- `src/agent_evaluations/evaluations/terminal_bench/adapter/agent.py`
- `src/agent_evaluations/evaluations/terminal_bench/adapter/env_bridge.py`
- `src/agent_evaluations/evaluations/terminal_bench/adapter/context_writer.py`
- `evaluations/evaluations/terminal_bench/config/ollama_glm52/`
- `evaluations/evaluations/terminal_bench/scripts/run_terminal_bench.sh`

## Setup
- `pip install -e core/python`
- `pip install -e evaluations`
- `pip install harbor`
- Docker running
- `ollama serve` + `ollama pull glm-5.2:cloud`

## Running
- Full: `bash evaluations/evaluations/terminal_bench/scripts/run_terminal_bench.sh`
- Test slice: `bash evaluations/evaluations/terminal_bench/scripts/run_test_slice.sh`

## Debugging
- Oracle smoke: `harbor run -d terminal-bench/terminal-bench-2-1 --agent oracle --n-tasks 2`
- View results: `harbor view jobs`
- Inspect a trial: `jobs/<job>/<trial>/agent/trajectory.json`

## Option C hook
- `src/agent_evaluations/stats_mapper.py` defines the Protocol for
  cross-harness output comparability. A future `terminal_bench_native/`
  evaluation can implement it to produce harbor-shaped summaries.
```

### `evaluations/evaluations/terminal_bench/README.md`

Shorter, quickstart-focused:

```markdown
# Terminal-Bench 2.1 Evaluation

Run Terminal-Bench 2.1 through our agent stack via Harbor (Option B).

## Quickstart
1. Install: `pip install -e core/python && pip install -e evaluations && pip install harbor`
2. Start Ollama: `ollama serve` (ensure `glm-5.2:cloud` is available)
3. Start Docker
4. Test slice: `bash evaluations/evaluations/terminal_bench/scripts/run_test_slice.sh`
5. Full run: `bash evaluations/evaluations/terminal_bench/scripts/run_terminal_bench.sh`

## Config
- `config/ollama_glm52/config.json` — our AgentApplication config (Ollama provider, glm-5.2:cloud)
- `config/ollama_glm52/profiles/...` — harbor JobConfig (dataset, n_concurrent, timeouts)

See AGENTS.md for the adapter contract and debugging guide.
```

### `evaluations/README.md` updates

Update the "Benchmark Layout" section to document:

```
evaluations/
  src/agent_evaluations/evaluations/<name>/   # per-evaluation code (importable)
  evaluations/<name>/                          # per-evaluation data (configs, scripts, docs)
```

Add a "Per-evaluation contract" section listing what each evaluation should
have:
- `benchmark_*.py` (optional — only if plugging into `agent-evaluations` CLI)
- `AGENTS.md` + `README.md`
- `config/<config-name>/{config.json, profiles/, .env.example}`
- `scripts/` (entrypoints)
- `adapter/` (only for harbor-backed evaluations)

### `evaluations/AGENTS.md` updates

Update the "Benchmark registration" section to mention the new
`agent_evaluations.evaluations.*` discovery path. Update "Where to
investigate" pointers.

### `stats_mapper.py` Protocol

```python
from __future__ import annotations
from pathlib import Path
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class StatsMapper(Protocol):
    """Map our evaluation results into a benchmark-native summary format.

    Implement this for an evaluation when you want its outputs to be
    comparable with the outputs of the benchmark's original harness (e.g.
    harbor's JobResult shape for terminal-bench). This is the extension
    point for Option C (run terminal-bench inside our own framework) so
    its results can be compared side-by-side with Option B (harbor run).

    The mapper reads our standard artifacts (results.jsonl, task-aggregate.jsonl,
    summary.json) and produces a benchmark-native summary object.
    """

    def map_results(self, results_root: Path) -> dict[str, Any]:
        """Map our results into the benchmark-native summary format.

        Args:
            results_root: Directory containing results.jsonl, task-aggregate.jsonl,
                and summary.json from one of our runs.

        Returns:
            A dict in the benchmark-native summary shape (e.g. harbor's
            JobResult JSON for terminal-bench).
        """
        ...
```

### Implementation decisions and open questions

**Decided:**
- Protocol (not ABC) for the `StatsMapper` — matches harbor's `JobPlugin`
  pattern and allows structural typing.
- No terminal-bench mapper implementation now — only the Protocol.
- Keep `tasks/20260508-agentic-evaluations-codex/` task files intact per
  user instruction.

**Open:**
- Whether to add a `StatsMapperRegistry` for discovery, or just let each
  evaluation import its mapper directly. **Recommendation:** keep it simple;
  no registry yet. Add one if/when a second evaluation implements a mapper.

### Documentation

- This subtask creates the docs listed above.

### Task checklist

- [ ] Create `evaluations/evaluations/terminal_bench/AGENTS.md`
- [ ] Create `evaluations/evaluations/terminal_bench/README.md`
- [ ] Update `evaluations/README.md`
- [ ] Update `evaluations/AGENTS.md`
- [ ] Create `evaluations/src/agent_evaluations/stats_mapper.py`
- [ ] Verify `python -c "from agent_evaluations.stats_mapper import StatsMapper; print(StatsMapper)"` works

### Requirement verification

| Requirement | Evidence |
|---|---|
| Terminal-bench AGENTS.md exists | File at `evaluations/evaluations/terminal_bench/AGENTS.md` with adapter contract, setup, debugging sections |
| Terminal-bench README.md exists | File at `evaluations/evaluations/terminal_bench/README.md` with quickstart |
| Top-level README updated | `evaluations/README.md` mentions multi-evaluation layout and per-evaluation contract |
| Top-level AGENTS updated | `evaluations/AGENTS.md` mentions `agent_evaluations.evaluations.*` discovery |
| StatsMapper Protocol exists | `evaluations/src/agent_evaluations/stats_mapper.py` defines `StatsMapper` Protocol with `map_results` method |
| Protocol importable | `python -c "from agent_evaluations.stats_mapper import StatsMapper"` succeeds |