# Ollama + GLM-5.2 Config For Terminal-Bench

Create the `AgentApplication` config and harbor job profile needed to run
Terminal-Bench 2.1 with Ollama serving `glm-5.2:cloud`.

Parent Task: `tasks/20260623-terminal-bench-evaluation/000-main.md`

Depends On: `tasks/20260623-terminal-bench-evaluation/010-evaluations-restructure.md`

## Requirements checklist

- [ ] `evaluations/evaluations/terminal_bench/config/ollama_glm52/config.json`
  defines an `ollama` provider pointing at `http://localhost:11434` and an
  agent using model `glm-5.2:cloud`.
- [ ] The config registers the `bash` tool plugin (from the adapter) so the
  `AgentApplication` has the terminal tool surface.
- [ ] `evaluations/evaluations/terminal_bench/config/ollama_glm52/.env.example`
  documents `OLLAMA_BASE_URL`, `AGENT_EVALUATIONS_CONFIG_DIR`, and
  `HARBOR_DATASET`.
- [ ] `evaluations/evaluations/terminal_bench/config/ollama_glm52/profiles/terminal-bench-2-1-ollama-glm52-local.json`
  is a harbor `JobConfig` that selects dataset
  `terminal-bench/terminal-bench-2-1`, our adapter as the agent, `n_concurrent:
  1`, `n_tasks: 5` (for the test slice), and generous agent timeouts.
- [ ] The profile passes `config_dir` via `agent_kwargs` so the adapter can
  load our `AgentApplication` config.
- [ ] A `.gitignore` in the config dir excludes `cache/`, `results/`,
  `workspaces/`, `.env`, and `auth/`.

## Scope and intent

This is configuration only — no new code. The config must be sufficient to
launch a harbor run with no manual setup beyond `ollama serve`, Docker
running, and `pip install -e evaluations`.

**In scope:**
- Our `AgentApplication` config (`config.json`).
- Harbor job profile (JSON `JobConfig`).
- `.env.example` and `.gitignore`.

**Out of scope:**
- The adapter code (subtask 020).
- The runner script (subtask 040).
- Actually running the benchmark (subtask 050).

## Execution plan

Status: Approved

### `config.json` structure

```json
{
  "plugin_cache_dir": "${config_dir}/.plugin_cache",
  "providers": {
    "ollama": {
      "provider": "ollama",
      "base_url": "http://localhost:11434",
      "model": "glm-5.2:cloud"
    }
  },
  "agents": {
    "terminal-bench-ollama-glm52": {
      "provider": "ollama",
      "model": "glm-5.2:cloud",
      "temperature": 0.0
    }
  },
  "plugins": [
    "agent_evaluations.evaluations.terminal_bench.adapter:BashToolPlugin"
  ]
}
```

**Notes:**
- The `bash` tool plugin is loaded from our adapter package. The exact
  import path depends on 020's implementation; if the plugin needs an
  injected executor, the config may use a `path:` source or a factory
  entry point. Will finalize during implementation once 020's
  `BashToolPlugin` shape is known.
- `temperature: 0.0` for deterministic terminal agent behavior.
- No reasoning summary or flex processing (Ollama doesn't support those).

### Harbor job profile structure

```json
{
  "dataset": "terminal-bench/terminal-bench-2-1",
  "agents": [
    {
      "name": "agent_evaluations.evaluations.terminal_bench.adapter:OurTerminalBenchAgent",
      "kwargs": {
        "config_dir": "<absolute path to evaluations/evaluations/terminal_bench/config/ollama_glm52>"
      }
    }
  ],
  "n_concurrent_trials": 1,
  "n_tasks": 5,
  "include_task_names": ["<5 fast tasks picked from the 89>"],
  "timeout_multiplier": 1.0,
  "agent_timeout_multiplier": 2.0,
  "retry": {
    "max_retries": 1,
    "include_exceptions": ["ApiRateLimitError"]
  }
}
```

**Notes:**
- `n_concurrent: 1` — Ollama is single-stream; bump later if the local
  Ollama instance handles parallel requests.
- `n_tasks: 5` + `include_task_names` — the test slice. Picked from fast
  tasks in the 89 (will select during 050).
- `agent_timeout_multiplier: 2.0` — Ollama is slow; generous.
- The `config_dir` kwarg is passed to our adapter's `__init__`.

### `.env.example`

```
OLLAMA_BASE_URL=http://localhost:11434
AGENT_EVALUATIONS_CONFIG_DIR=evaluations/evaluations/terminal_bench/config/ollama_glm52
HARBOR_DATASET=terminal-bench/terminal-bench-2-1
```

### `.gitignore`

Same pattern as RepoQA config dirs:
```
.env
auth/
cache/
results/
workspaces/
_sessions/
```

### Implementation decisions and open questions

**Decided:**
- Model tag: `glm-5.2:cloud` (confirmed by user).
- `temperature: 0.0`.
- `n_concurrent: 1` for the first version.
- Test slice: 5 tasks.

**Open:**
- Exact `bash` tool plugin import path / registration mechanism — depends
  on 020's `BashToolPlugin` design. Will finalize when 020 is implemented.
- Which 5 tasks to pick for the test slice — will select during 050 from
  the 89 based on estimated runtime (fast tasks first).

### Documentation

- `evaluations/evaluations/terminal_bench/README.md` (in subtask 060) will
  reference this config.

### Task checklist

- [ ] Create `config/ollama_glm52/config.json`
- [ ] Create `config/ollama_glm52/.env.example`
- [ ] Create `config/ollama_glm52/.gitignore`
- [ ] Create `config/ollama_glm52/profiles/terminal-bench-2-1-ollama-glm52-local.json`
- [ ] Verify `python -c "from agent_evaluations.config_dir import load_evaluation_environment; load_evaluation_environment('evaluations/evaluations/terminal_bench/config/ollama_glm52')"` succeeds (after 020 is done)

### Requirement verification

| Requirement | Evidence |
|---|---|
| `config.json` defines ollama provider + glm-5.2:cloud agent | `jq .providers.ollama.model config.json` returns `glm-5.2:cloud` |
| `bash` tool plugin registered | `jq .plugins config.json` includes the adapter plugin path |
| `.env.example` documents required vars | File lists `OLLAMA_BASE_URL`, `AGENT_EVALUATIONS_CONFIG_DIR`, `HARBOR_DATASET` |
| Harbor profile selects dataset + adapter | `jq .dataset profile.json` returns `terminal-bench/terminal-bench-2-1`; `jq .agents[0].name` returns our adapter path |
| Profile passes `config_dir` kwarg | `jq .agents[0].kwargs.config_dir profile.json` is non-empty |
| `.gitignore` excludes runtime dirs | File lists `cache/`, `results/`, `workspaces/`, `.env`, `auth/` |