# Terminal-Bench 2.1 Evaluation Via Harbor (Option B)

Run the Terminal-Bench 2.1 benchmark against our `AgentApplication` stack by
plugging a custom `BaseAgent` adapter into the official Harbor harness, with an
Ollama + GLM-5.2 config and a unified runner script. Restructure `evaluations/`
so multiple independent evaluations can coexist.

## Requirements checklist

- [ ] `evaluations/` supports multiple independent evaluations, each with its own
  code namespace under `src/agent_evaluations/evaluations/<name>/` and its own
  data tree under `evaluations/evaluations/<name>/`.
- [ ] RepoQA continues to work after the restructure: `agent-evaluations run
  repoqa ...` and `agent-evaluations run repoqa-prompted ...` dispatch correctly
  and existing RepoQA tests pass.
- [ ] Terminal-Bench 2.1 runs end-to-end via Harbor with a custom agent adapter
  that wraps `AgentApplication`, so our provider/plugin/tool stack drives the
  terminal inside Harbor's task containers.
- [ ] An Ollama + GLM-5.2 (`glm-5.2:cloud`) config and harbor job profile exist
  and are sufficient to launch a run without additional manual setup beyond
  `ollama serve` and Docker running.
- [ ] A unified runner script invokes `harbor run` with our adapter and config,
  and a test-slice variant runs a 5-task smoke.
- [ ] A test-run against Ollama + GLM-5.2 completes (does not crash), produces
  harbor job artifacts, and the verifier runs for each trial.
- [ ] Terminal-Bench evaluation has `AGENTS.md` and `README.md` documenting
  setup, the adapter contract, and how to add a new evaluation.
- [ ] A `stats_mapper` Protocol exists in the shared framework as the extension
  point for future Option C cross-harness output comparability; no terminal-bench
  mapper implementation is required yet.

## Subtasks

- [ ] `tasks/20260623-terminal-bench-evaluation/010-evaluations-restructure.md`
- [ ] `tasks/20260623-terminal-bench-evaluation/020-terminal-bench-adapter.md`
- [ ] `tasks/20260623-terminal-bench-evaluation/030-ollama-glm52-config.md`
- [ ] `tasks/20260623-terminal-bench-evaluation/040-runner-script.md`
- [ ] `tasks/20260623-terminal-bench-evaluation/050-harbor-smoke-and-test-run.md`
- [ ] `tasks/20260623-terminal-bench-evaluation/060-docs-and-stats-mapper.md`

## Open requirement questions

None currently. Prior questions were resolved during planning (see Execution
plan history): model is `glm-5.2:cloud`, harbor installed via `pip install
harbor`, test slice is 5 tasks, layout uses code/data split.

## Execution plan

Status: Approved

### Context

Terminal-Bench 2.1 is an 89-task benchmark of terminal-based agent work
(software engineering, sysadmin, data processing, model training, security).
Each task ships with an instruction, a Dockerfile, pytest tests that check the
final container state, an oracle solution, and a time limit. The official
harness is Harbor (from the Laude Institute). The dataset is published on
Harbor Hub as `terminal-bench/terminal-bench-2-1`.

Three options were considered for running it through our stack:

- **Option A** — use harbor's built-in `terminus-2` agent and route the LLM
  through our endpoint via `api_base`. Lowest effort, but our agent stack
  (tools, plugins, sessions) is not exercised.
- **Option B** — write a custom `BaseAgent` adapter that wraps
  `AgentApplication`; harbor runs the task containers + verifier. Our agent
  stack drives the terminal. **Chosen.**
- **Option C** — implement terminal-bench inside our own `evaluations/`
  framework (full scheduler control, but reimplement harbor's Docker
  orchestration). Deferred; only the `stats_mapper` Protocol hook is sketched
  now so Option C can plug in cleanly later.

### Approach

**Layout (code/data split):**

```
evaluations/
  src/agent_evaluations/evaluations/     # per-evaluation code (importable)
    repoqa/         benchmark_prompted.py, benchmark_agentic.py, logic_*.py, common.py
    terminal_bench/  adapter/ (agent.py, env_bridge.py, context_writer.py)
  evaluations/                            # per-evaluation data
    repoqa/         config/, workflows/, scripts/, AGENTS.md, README.md
    terminal_bench/ config/ollama_glm52/, scripts/, AGENTS.md, README.md
```

Code is in the installed package (importable via `agent_evaluations.evaluations.<name>`);
data is co-located with the evaluation but not packaged.

**Adapter design (Option B):**

- `OurTerminalBenchAgent(BaseAgent)` — external agent flavor. `setup()` builds
  the `AgentApplication` from our config; `run(instruction, environment,
  context)` drives our agent and translates tool calls into
  `environment.exec` bash commands.
- A single `bash` tool plugin is registered in our `AgentApplication` config;
  its `execute_tool` calls back into the adapter, which calls
  `await environment.exec(command)`.
- LLM routing is fully ours (Ollama provider, `glm-5.2:cloud` model). Harbor's
  `--model` flag is accepted but ignored by our adapter.
- Our event stream is mapped into harbor's `Trajectory` (ATIF) format
  minimally — enough for the viewer and verifier; full ATIF fidelity is
  deferred.
- `ApiRateLimitError` from `harbor.agents.installed.base` is raised on
  provider rate-limit signals so `--max-retries --retry-include
  ApiRateLimitError` works.

**Rate limiting:** Harbor has no built-in "tasks per time window". For the
first version we rely on `--n-concurrent` + `--n-tasks`. A `BaseJobPlugin`
rate limiter is deferred unless the test-run shows we need it.

**Import path:** harbor imports the agent via `module:ClassName`. Our adapter
lives at `agent_evaluations.evaluations.terminal_bench.adapter:OurTerminalBenchAgent`,
importable because `agent_evaluations` is an installed package.

### Sequencing

1. **010 — Restructure** (partially done): move RepoQA, update registry, fix
   tests and docs.
2. **020 — Adapter**: `BaseAgent` subclass + `BashToolPlugin` + context
   writer, with offline unit tests.
3. **030 — Ollama config**: `config.json`, harbor job profile, `.env.example`.
4. **040 — Runner script**: unified entrypoint + test-slice variant.
5. **050 — Harbor smoke + test-run**: oracle smoke, then 5-task Ollama run.
6. **060 — Docs + stats mapper**: terminal-bench `AGENTS.md`/`README.md`,
   top-level `evaluations/` docs, `stats_mapper.py` Protocol.

### Implementation decisions and open questions

**Decided:**
- Code/data split (code in package, data in `evaluations/evaluations/`).
- External agent flavor (not installed) — our agent runs in the harbor host
  process, talks to the container via `environment.exec`.
- Single `bash` tool surface — keeps our tool-loop, streaming, and plugin
  stack fully in play.
- `pip install harbor` (not `uv tool install`).
- Model tag: `glm-5.2:cloud`.
- Test slice: 5 tasks.
- No windowed rate-limit plugin in the first version.

**Deferred / open:**
- Full ATIF trajectory fidelity (needed only for leaderboard submission).
- `BaseJobPlugin` rate limiter (only if test-run shows we need it).
- Option C implementation (only the `stats_mapper` Protocol is sketched).
- Harbor version pinning (will add a version note in `.env.example`).

### Documentation

- `evaluations/evaluations/terminal_bench/AGENTS.md` — adapter contract,
  setup, gotchas.
- `evaluations/evaluations/terminal_bench/README.md` — quickstart, run
  commands, config overview.
- `evaluations/README.md` + `evaluations/AGENTS.md` — updated for the new
  multi-evaluation layout.
- `evaluations/evaluations/repoqa/AGENTS.md` + `README.md` — unified from
  the 4 split files.

### Task checklist

- [ ] 010: Finish RepoQA restructure (tests, config-embedded scripts, docs)
- [ ] 010: Verify `pytest evaluations/tests -q` passes
- [ ] 020: Implement adapter + offline unit tests
- [ ] 030: Create Ollama config + profile + `.env.example`
- [ ] 040: Create unified runner script + test-slice script
- [ ] 050: Harbor oracle smoke passes
- [ ] 050: 5-task Ollama test-run completes without crashing
- [ ] 060: Terminal-bench AGENTS.md + README.md
- [ ] 060: Update top-level evaluations/README.md + AGENTS.md
- [ ] 060: Add `stats_mapper.py` Protocol

### Requirement verification

| Requirement | Evidence |
|---|---|
| Multi-evaluation layout | `evaluations/evaluations/<name>/` + `src/agent_evaluations/evaluations/<name>/` exist; registry discovers both |
| RepoQA still works | `pytest evaluations/tests -q` passes; `agent-evaluations run repoqa ...` dispatches |
| Terminal-Bench runs via Harbor | `harbor run -d terminal-bench/terminal-bench-2-1 --agent agent_evaluations.evaluations.terminal_bench.adapter:OurTerminalBenchAgent ...` completes |
| Ollama + GLM-5.2 config | `evaluations/evaluations/terminal_bench/config/ollama_glm52/` has `config.json`, profile, `.env.example` |
| Unified runner script | `run_terminal_bench.sh` invokes harbor with our adapter + config; `run_test_slice.sh` runs 5 tasks |
| Test-run completes | Harbor job dir has `result.json`, per-trial `agent/trajectory.json`, `verifier/ctrf.json` |
| Docs | Terminal-bench `AGENTS.md` + `README.md` exist; top-level docs updated |
| Stats mapper Protocol | `src/agent_evaluations/stats_mapper.py` defines the Protocol |

## Implementation Notes

### 2026-06-23 — Phase 1 (restructure) partially complete

Committed as `8ee24d20 Restructure evaluations/ for multi-evaluation layout`.

**Done in that commit:**
- Created `evaluations/src/agent_evaluations/evaluations/{__init__.py,repoqa/__init__.py,terminal_bench/__init__.py}`.
- Moved RepoQA code: `common.py`, `logic_prompted.py`, `logic_agentic.py`,
  `benchmark_prompted.py`, `benchmark_agentic.py` into the package.
- Moved RepoQA data: `config/`, `workflows/`, `scripts/`, `AGENTS_*.md`,
  `README_*.md` into `evaluations/evaluations/repoqa/`.
- Removed old `evaluations/benchmarks/` and stale `evaluations/config/`.
- Replaced `importlib.util` hacks with proper package imports in logic and
  benchmark files.
- Rewrote `benchmark_registry.py` to discover `benchmark_*.py` under
  `agent_evaluations.evaluations.*` subpackages (kept external + legacy
  fallbacks).
- Updated 4 of 6 test files to new paths.
- Updated 2 top-level runner scripts to new paths.

**Remaining for 010 (see subtask):** 3 test files still reference old paths;
config-embedded scripts in some config dirs still reference old paths;
top-level docs and RepoQA unified docs not yet written; tests not yet run.