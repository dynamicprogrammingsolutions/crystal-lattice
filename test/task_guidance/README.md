# Task Guidance Real-Model Evaluation

This gated empirical evaluation runs the repository task-file guidance against a pinned OpenAI Codex checkout with:

- ChatGPT account auth and `gpt-5.6-luna`
- the default `glm-ollama` agent and its configured GLM-5.2 model

It exercises two scenarios:

1. Ask for a plan, then ask only to create a single task file.
2. Add a requirements-only task file, then ask for an execution plan.

The tests make only mechanical assertions. Review the saved task file, response, diff, session, and tool telemetry using the generated review template.

## Prerequisites

- Saved ChatGPT credentials at `$CHATGPT_TEST_STATE_DIR/auth/chatgpt-auth.json`; `CHATGPT_TEST_STATE_DIR` defaults to `~/.crystal`.
- Ollama's OpenAI-compatible endpoint at `OLLAMA_OPENAI_BASE_URL`, defaulting to `http://localhost:11434/v1`.
- Network access for the pinned Codex checkout and ChatGPT request.

## Run

```bash
RUN_TASK_GUIDANCE_REAL_MODEL_EVAL=1 \
CHATGPT_TEST_STATE_DIR="$HOME/.crystal" \
pytest -c application/python/pyproject.toml \
  test/task_guidance/test_tasks_guidance_real_api.py \
  -m manual_integration -s
```

Useful overrides:

- `TASK_GUIDANCE_FILE` — guidance file to stage; defaults to `agents/TASKS-v7.md`.
- `TASK_GUIDANCE_CHATGPT_MODEL` — defaults to `gpt-5.6-luna`.
- `TASK_GUIDANCE_OLLAMA_MODEL` — defaults to the `glm-ollama` model in the copied default config.
- `TASK_GUIDANCE_MUTATION_CALL_LIMIT` — hard per-case limit for `apply_patch`, `Edit`, `Write`, and equivalent file-mutation calls; defaults to `3`.
- `TASK_GUIDANCE_TOOL_LOOP_LIMIT` — broad runaway ceiling; defaults to `60`. The separate mutation-call limit is the stricter task-file editing guard.
- `TASK_GUIDANCE_RUN_ID` — stable artifact directory name for a rerun.

Artifacts are retained under:

```text
tmp/task-guidance-eval/runs/<run-id>/<scenario>/<model>/
```

Each case records prompts, assistant responses, task files, Git state and diff, session snapshots, events, tool telemetry, run metadata, and `review-template.md`.

The checkout cache lives under `tmp/task-guidance-eval/repo-cache/`. Each case receives a fresh detached worktree at the pinned commit.

The copied default config retains the selected agents, providers, system-message mixins, and model-specific tool packages, while excluding unrelated application plugins from the evaluation plugin catalog. This keeps the test focused on the default agent harness and avoids unrelated plugin installation failures.
