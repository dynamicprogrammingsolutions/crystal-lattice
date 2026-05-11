# RepoQA Agentic Evaluation

Build the shared `evaluations/` package and implement the first end-to-end benchmark on top of it: an agentic RepoQA runner that uses Codex tools through `AgentApplication` and can compare `codex-openai` against `codex-openai-api` or any other configured agent.

## Requirements checklist

- [x] Create the root-level `evaluations/` package with a single CLI entrypoint and package-local tests/docs.
- [x] Define the config-dir convention for evaluation environments:
  - `.env`
  - `config.json`
  - `AGENTS.md`
  - `auth/chatgpt-auth.json`
  - `auth/chatgpt-rate-limits.json`
- [x] Define and document the dedicated top-level benchmark settings subtree in `config.json`. Recommended key: `agentic_evaluations`.
- [x] Add separate ChatGPT auth commands to the CLI using the existing application plugin flow:
  - login
  - status
  - logout
- [x] Add a shared scheduling layer that supports:
  - task-start quotas per scheduling window
  - max parallel tasks
  - optional randomized task-start placement within each window
  - allowed weekdays
  - local working-hours windows
  - optional max tasks per day
  - graceful sleeping until the next allowed slot
- [x] Add RepoQA download support and deterministic manifest generation.
- [x] Add RepoQA task workspace materialization for agentic runs.
- [x] Run RepoQA tasks through `AgentApplication` using a selected `agent_id` and per-task workspace overrides.
- [x] Score RepoQA agentic outputs with reproducible local scoring and emit JSONL plus summary artifacts.
- [x] Add tests covering config loading, auth-command wiring, scheduling decisions, RepoQA manifest generation, and at least one end-to-end dry-run or fixture-backed benchmark task.

Parent Task: `tasks/20260508-agentic-evaluations-codex/000-main.md`

## Scope and ownership

This task should own the shared scaffold for both benchmarks:

- package layout under `evaluations/`
- single CLI
- config-dir loading
- `.env` loading
- `AgentApplication` runner
- ChatGPT auth commands
- scheduling / pacing
- result and manifest formats

LiveCodeBench should extend this scaffold rather than creating a parallel one.

## Functional target

The first finished benchmark mode should be RepoQA in agentic form:

- Each task becomes a workspace with:
  - `TASK.md`
  - `meta.json`
  - `repo/`
  - optional `submission/`
- The agent receives a small tool-oriented prompt and uses tools to inspect the checked-out repo.
- The runner sets per-task overrides such as:
  - `working_directory`
  - `allowed_paths`
- The final answer should be machine-parseable, for example JSON with:
  - `path`
  - `symbol`
  - `code`
- The scorer compares the returned code against the ground-truth function.

## Config and auth requirements

- The config dir should be self-contained enough that a user can point the CLI at it and run:
  - ChatGPT login-backed OpenAI Responses auth
  - API-key-backed OpenAI Responses auth
- Reuse the existing ChatGPT auth plugin and OpenAI Responses provider instead of inventing a custom auth path.
- The CLI should explicitly call the application action plugin for login/status/logout rather than requiring manual Python interaction.
- The login credentials and saved rate-limit/auth metadata should live in the config dir under `auth/`.

## Scheduling and fair-use requirements

Support a run policy that makes the benchmark behave more like a human user:

- `min_task_interval_minutes`
  - example: start at most one benchmark task every 15 minutes
- `min_provider_request_interval_seconds`
  - required because one benchmark task may produce multiple provider calls through the tool loop
- `timezone`
- `allowed_weekdays`
- `working_hours`
  - example: `[{"start":"09:00","end":"17:00"}]`
- optional `max_tasks_per_day`

The runner should be able to:

- decide whether a task may start right now
- sleep until the next valid slot
- record when and why a task was deferred

## Existing implementation patterns to reuse

- Use `AgentApplication.create_session_ephemeral(...)` / request execution patterns already present in `core/python/agent_app/application_future.py:1807-1845` and `core/python/agent_app/application_future.py:2053-2145`.
- The tool loop already handles repeated LLM/tool phases in `core/python/agent_app/tool_loop.py:449-560`.
- Codex shell-command semantics already exist in `plugins/codex-tools/src/codex_tools/shell_command_tool.py:31-110`.
- Existing real tests already show per-task `working_directory` and `allowed_paths` overrides in `application/python/tests/test_terminal_default_config_codex_gpt5_apply_patch_real_api.py:61-74` and `application/python/tests/test_terminal_default_config_codex_gpt5_apply_patch_real_api.py:168-177`.
- Existing default config already shows the intended Codex/OpenAI agents in `application/python/agent_terminal_app/default_config/config.json:505-535`.
- Existing OpenAI Responses auth-mode expectations for `codex-openai-api` are already tested in `application/python/tests/test_default_config_effective_agent_configs.py:59-64`.
- Existing ChatGPT auth plugin config and persisted auth paths are shown in `plugins/chatgpt-auth-app/tests/test_chatgpt_auth_app_plugin_unit.py:199-245`.
- Existing login start/status flow and credential persistence are shown in `plugins/chatgpt-auth-app/tests/test_chatgpt_auth_app_plugin_unit.py:283-380`.

## External benchmark references

- Official RepoQA repository:
  - `https://github.com/evalplus/repoqa`
- RepoQA project page:
  - `https://evalplus.github.io/repoqa.html`
- RepoQA release data used during research:
  - `https://github.com/evalplus/repoqa_release/releases`
  - specifically the current inspected data release: `2024-06-23`
  - direct asset pattern used by the current code and research:
    `https://github.com/evalplus/repoqa_release/releases/download/2024-06-23/repoqa-2024-06-23.json.gz`
- Current dataset facts already verified during research and safe to reuse here:
  - current inspected release contains `600` needle tasks across `6` languages
  - benchmark layout is `10 repos x 10 needles` per language
  - languages in the inspected release: `python`, `cpp`, `java`, `typescript`, `rust`, `go`
- Official prompt structure in upstream RepoQA:
  - instruction + code context + function description + instruction again
  - this is reflected in the upstream `search_needle_function.py` template

These upstream references should be treated as the benchmark-side source of truth for:

- release selection
- dataset acquisition
- repo/language/needle identifiers
- baseline scoring semantics
- upstream prompt/task interpretation

## Suggested CLI shape

Keep this benchmark on the same CLI that LiveCodeBench will later reuse. Example shape:

```text
agent-evaluations auth login-chatgpt --config-dir evaluations/benchmarks/repoqa_agentic/config/<env>
agent-evaluations auth status --config-dir evaluations/benchmarks/repoqa_agentic/config/<env>
agent-evaluations download repoqa --config-dir evaluations/benchmarks/repoqa_agentic/config/<env> --profile <profile>
agent-evaluations manifest repoqa --config-dir evaluations/benchmarks/repoqa_agentic/config/<env> --profile <profile>
agent-evaluations run repoqa --config-dir evaluations/benchmarks/repoqa_agentic/config/<env> --profile <profile>
```

For local development, prefer editable installs:

```text
pip install -e core/python
pip install -e evaluations
```

## Notes for completion

- Prefer ephemeral sessions by default so benchmark runs do not accumulate large long-lived session stores.
- Save enough raw output to debug failures:
  - final assistant message
  - parsed answer
  - tool-call counts
  - provider-call counts if available
- Treat benchmark mode as explicitly custom/agentic in the result metadata so it is never confused with official RepoQA scores.

## Execution plan

Added during completion based on updated user requirements.

1. Build the shared `evaluations/` package scaffold with a single CLI, config-dir loader, dotenv support, run-profile manifest support, and ChatGPT auth commands wired through `AgentApplication.execute_application_action(...)`.
2. Implement scheduler semantics around task starts only:
   - configurable tasks-per-window
   - configurable window size
   - configurable max parallel tasks
   - optional randomized placement within each scheduling window
   - resumable run-state tracking so deferred and started tasks are reproducible
3. Implement RepoQA support:
   - release download/cache
   - deterministic manifest generation
   - task workspace materialization with `TASK.md`, `meta.json`, and `repo/`
   - agentic run loop through `create_session_ephemeral(...)` and `send_request(...)`
   - restart failed tasks from scratch until a turn completes or retry limits are reached
4. Support two OpenAI run modes through profile/config selection:
   - API auth mode with flex processing enabled
   - ChatGPT login auth mode
5. Add package-local tests for config loading, auth wiring, scheduling decisions, manifest determinism, workspace construction, and fixture-backed RepoQA runs.
6. Run targeted tests and a limited API-backed benchmark smoke run using `gpt-5.4-mini` when the required credentials are available.

## Completion Notes

Added during completion.

- [x] Created the root-level `evaluations/` package with:
  - `pyproject.toml`
  - `README.md`
  - `src/agent_evaluations/`
  - `tests/`
- [x] Implemented a single CLI entrypoint with:
  - `auth login-chatgpt`
  - `auth status`
  - `auth logout`
  - `download repoqa`
  - `manifest repoqa`
  - `run repoqa`
- [x] Implemented config-dir loading with:
  - `config.json`
  - `.env`
  - `AGENTS.md`
  - `auth/`
  - `profiles/`
- [x] Added and documented the `agentic_evaluations` config subtree and default path conventions.
- [x] Implemented task-start scheduling with:
  - window-based quotas
  - max parallel tasks
  - optional randomized starts
  - weekday / working-hours / daily-cap support
- [x] Implemented RepoQA release download, deterministic manifest generation, workspace materialization, task execution through `AgentApplication`, retry-on-pre-completion-failure, JSONL results, and summary artifacts.
- [x] Enforced OpenAI API-mode runs through the OpenAI Responses stack with flex processing enabled on evaluation runs.
- [x] Added package-local tests covering:
  - config loading
  - auth-command wiring
  - scheduling decisions
  - RepoQA fixture manifest/run flow
  - retry behavior
  - max parallelism behavior
- [x] Added a real OpenAI API smoke integration test for `codex-openai-api` with `gpt-5.4-mini`.
- [x] Verification completed:
  - `pytest evaluations/tests -q`
  - `pytest evaluations/tests/test_repoqa_openai_api_integration.py -q` with `.env` loaded
  - one limited CLI-style RepoQA run with `codex-openai-api` and `gpt-5.4-mini`

Notes:

- The updated user requirement explicitly superseded per-provider-request pacing; the implementation therefore schedules task starts only.
- The limited real API run completed end-to-end and produced artifacts successfully, but the single sampled RepoQA task scored `0.0` in that smoke run. The runner is functioning; benchmark quality tuning can continue iteratively.