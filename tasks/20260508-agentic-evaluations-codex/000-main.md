# Agentic Codex Evaluations Package

Create a root-level `evaluations/` package that runs agentic benchmark tasks through `AgentApplication` using Codex-style tools and OpenAI Responses auth modes, with one shared CLI and one config-dir convention for both RepoQA and LiveCodeBench.

## Task checklist

- [x] `tasks/20260508-agentic-evaluations-codex/010-repoqa-agentic-eval.md`
- [ ] `tasks/20260508-agentic-evaluations-codex/015-benchmark-registry-refactor.md`
- [ ] `tasks/20260508-agentic-evaluations-codex/017-repoqa-prompted-eval.md`
- [ ] `tasks/20260508-agentic-evaluations-codex/018-benchmark-owned-layout-and-run-profiles.md`
- [x] `tasks/20260508-agentic-evaluations-codex/019-repoqa-prompted-context-eligibility.md`
- [ ] `tasks/20260508-agentic-evaluations-codex/020-livecodebench-agentic-eval.md`
- [x] `tasks/20260508-agentic-evaluations-codex/021-shared-parser-backed-code-comparison.md`

## Shared requirements

- Build a dedicated root package at `evaluations/` rather than mixing benchmark code into `core/python` or `application/python`.
- Expose a single CLI for all benchmark operations, for example:
  - `auth login-chatgpt`
  - `auth status`
  - `auth logout`
  - `download repoqa`
  - `download livecodebench`
  - `manifest ...`
  - `run repoqa ...`
  - `run livecodebench ...`
- Use one config-dir convention per evaluation environment, preferably benchmark-owned under `evaluations/benchmarks/<benchmark>/config/<env-name>/`, containing at minimum:
  - `.env`
  - `config.json`
  - `AGENTS.md`
  - `auth/chatgpt-auth.json`
  - `auth/chatgpt-rate-limits.json`
- The `config.json` in that directory must contain benchmark-runner settings under a dedicated top-level key. Recommended key: `agentic_evaluations`.
- Use the default Codex system-message stack plus Codex tools from the existing config system, and layer custom evaluation instructions via `AGENTS.md` instead of replacing the default Codex prompt.
- Support two OpenAI Responses auth paths with the same CLI and config-dir:
  - ChatGPT login-backed auth
  - API-key-backed auth
- Login must be a separate command, not an implicit side effect of `run`.
- Task runs must support both:
  - coarse scheduling: e.g. one benchmark task every 15 minutes
  - working-hours gating: e.g. run only during specified local hours and weekdays
- Because agentic tasks may trigger multiple provider requests through the tool loop, the design should include both:
  - minimum time between benchmark task starts
  - minimum time between actual provider requests
- Benchmarks are custom/agentic, but must still be reproducible and comparable across two runs by freezing:
  - benchmark manifest
  - config dir
  - agent id
  - enabled tools
  - scheduling/rate-limit policy
  - workspace materialization logic
  - scoring logic

## Recommended config shape

Historically the shared runner used `evaluations/config/<env-name>/config.json`. The preferred layout is now benchmark-owned, for example `evaluations/benchmarks/<benchmark>/config/<env-name>/config.json`, with a dedicated subtree such as:

```json
{
  "providers": { "...": "..." },
  "plugins": ["..."],
  "agents": {
    "codex-openai": { "...": "..." },
    "codex-openai-api": { "...": "..." }
  },
  "application": {
    "chatgpt_auth": {
      "credentials_path": "${env:CONFIG_DIR}/auth/chatgpt-auth.json",
      "rate_limits_path": "${env:CONFIG_DIR}/auth/chatgpt-rate-limits.json"
    }
  },
  "agentic_evaluations": {
    "workspace_root": "${env:CONFIG_DIR}/../workspaces",
    "cache_root": "${env:CONFIG_DIR}/../cache",
    "results_root": "${env:CONFIG_DIR}/../results",
    "manifests_root": "${env:CONFIG_DIR}/../manifests",
    "schedule": {
      "timezone": "America/New_York",
      "allowed_weekdays": ["Mon", "Tue", "Wed", "Thu", "Fri"],
      "working_hours": [{"start": "09:00", "end": "17:00"}],
      "min_task_interval_minutes": 15,
      "max_tasks_per_day": 32
    },
    "provider_pacing": {
      "min_provider_request_interval_seconds": 60
    }
  }
}
```

The exact field names can change during implementation, but the task runner should keep benchmark-specific settings out of the normal provider/agent fields and gather them under one explicit subtree.

## Important repo references

- Default Codex developer-message selection and system-message composition already live in `application/python/agent_terminal_app/default_config/config.json:13-121`.
- The default OpenAI Responses provider config already carries `auth_mode`, Codex-friendly flags, and `allowed_paths` / `working_directory` in `application/python/agent_terminal_app/default_config/config.json:340-355`.
- Existing Codex/OpenAI agents are already declared in `application/python/agent_terminal_app/default_config/config.json:505-535`.
- Existing multi-family tool configs show how Codex tools are attached to providers and how `working_directory` / `allowed_paths` are configured in `application/python/agent_terminal_app/config_v2_multi_family_tools.json:4-120`.
- Per-request workspace overrides are already exercised in the real integration test `application/python/tests/test_terminal_default_config_codex_gpt5_apply_patch_real_api.py:61-74` and `application/python/tests/test_terminal_default_config_codex_gpt5_apply_patch_real_api.py:151-229`.
- ChatGPT auth persistence paths for OpenAI Responses are already covered in `plugins/chatgpt-auth-app/tests/test_chatgpt_auth_app_plugin_unit.py:199-245`.
- The login flow and saved credentials behavior are already covered in `plugins/chatgpt-auth-app/tests/test_chatgpt_auth_app_plugin_unit.py:283-380`.
- The interactive ChatGPT login display payload and actions are implemented in `plugins/chatgpt-auth-app/src/chatgpt_auth_app/__init__.py:1206-1310`.

## Suggested execution order

1. Implement the shared `evaluations/` package, CLI, config-dir loader, scheduler, and ChatGPT auth commands in the RepoQA task.
2. Add RepoQA download, workspace materialization, agentic prompting, and scoring.
3. Reuse the same CLI/config/scheduler/auth stack for LiveCodeBench.
4. Add LiveCodeBench-specific workspace and scoring behavior without diverging from the shared runner interface.