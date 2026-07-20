# Real-Model Task Guidance Evaluation

Create a gated empirical test harness that exercises the draft task-file guidance against a pinned real repository using ChatGPT GPT-5.6 Luna and Ollama GLM-5.2.

## Requirements checklist

- [x] Run both scenarios against fresh worktrees of the same pinned OpenAI Codex commit under `tmp/`.
- [x] Exercise ChatGPT account auth with `gpt-5.6-luna` and credentials rooted at `~/.crystal`, plus the default Ollama GLM-5.2 model.
- [x] In scenario one, request a plan and then ask only to create the task file, preserving the default behavior when the user does not explicitly request that the plan be included.
- [x] In scenario two, start from a valid requirements-only task file, request an execution plan, and inspect both the updated task file and approval response.
- [x] Bound tool-loop execution and fail cases that exceed the configured task-file mutation-call limit.
- [x] Preserve prompts, responses, task files, diffs, session/tool telemetry, and a manual review template under `tmp/`.
- [x] Keep the evaluation separate from the cloud-script-author test and document how to run and review it.

## Context

- Guidance under test: `agents/TASKS-v7.md`.
- Default config currently loads `TASKS_v6.md`; the harness must stage the selected guidance under that expected filename in an isolated config copy.
- External repository: `openai/codex`, pinned to commit `9f42c89c0112771dc29100a6f3fc904049b2655f`.
- Evaluation task: make MDM `requirements_toml_base64` resolve home-relative `permissions.filesystem.deny_read` paths consistently with file-based requirements while preserving existing behavior.
- The initial review is empirical and performed by the executing agent; mechanical assertions should protect experiment integrity without trying to judge all plan quality automatically.
- Optional later extension: fork the first scenario after its initial planning response and compare continuations that request a task with or without the plan, or request immediate execution.

## Execution plan

Status: Approved

Implement a standalone, gated real-model evaluation under the top-level `test/` area. Reuse the production `AgentApplication` and copied default config, but keep repository checkout, prompts, artifact collection, and empirical scoring owned by the evaluation harness.

Use a cached pinned Codex checkout with one fresh worktree per scenario/model case. Stage `agents/TASKS-v7.md` into each isolated config as `TASKS_v6.md`, enable task guidance before session creation, constrain paths to the worktree, and preserve the same session across follow-up turns.

Run the matrix with the default-config ChatGPT/Codex agent overridden to `gpt-5.6-luna`, `auth_mode: chatgpt`, and `~/.crystal/auth/chatgpt-auth.json`; run the default `glm-ollama` agent with its configured `glm-5.2:cloud` model unless overridden. Apply a hard tool-loop ceiling and a lower mutation-call budget covering `apply_patch` and equivalent write/edit tools.

### Requirement verification

- Scenario/model setup: mechanical assertions verify the pinned commit, isolated worktree, selected agent/model/auth settings, and guidance injection.
- Scenario one: a real multi-turn integration case verifies the first turn leaves the repository unchanged and the continuation creates only one task file.
- Scenario two: a real integration case verifies only the premade task file changes, its requirements remain unchanged, and the plan is written before the final approval response.
- Tool limits: captured tool calls verify the hard mutation budget and expose total/read/write call telemetry.
- Empirical review: saved artifacts are reviewed manually for required structure, requirement quality, durable planning, requirement-facing test coverage, documentation treatment, approval discipline, and concise user presentation.

### Documentation

Add a short evaluation README for developers running the gated test. Document credentials, Ollama prerequisites, model overrides, the pinned repository, run command, artifact layout, mutation-call limit, and manual review procedure. No product documentation changes are required.

### Task checklist

- [x] Add the premade task fixture and manual review template under `test/fixture/`.
- [x] Implement checkout/config/session/artifact helpers.
- [x] Implement the two scenarios parameterized over ChatGPT and Ollama.
- [x] Add mechanical integrity and mutation-budget assertions.
- [x] Add the evaluation README and exact run commands.
- [x] Run fast non-provider checks for collection and helper behavior.
- [x] Run all four real-model cases and complete the empirical review.
- [x] Record verification, findings, and artifact paths in completion notes.

## Implementation Notes

- The first live attempt showed that a per-case plugin cache caused every copied default config to rebuild all plugin dependencies before reaching the model. The harness now shares only the generated plugin cache under `tmp/task-guidance-eval/`; worktrees, configs, sessions, and artifacts remain isolated per case.
- The first complete matrix exposed two harness issues: unrelated default-config application plugins could fail before the selected agent started, and a 12-loop ceiling stopped GLM while it was still reading relevant files. The staged config now keeps only the selected agents' shared provider/system-message features, and the general loop ceiling is 24 while the stricter three-call file-mutation budget remains enforced.
- The next harness run showed that agent-specific plugins were still resolved for every configured agent and that the mutation wrapper did not forward the tool loop's cancellation keyword. Each staged config now contains only the selected default agent, and the wrapper transparently forwards the full tool execution call.
- ChatGPT startup still inherited an older host `attr` module before the cached Codex tool dependencies were activated. The selected agent's production tool package is now staged first in the copied config, and only stale `attr`/`attrs` modules are evicted before constructing the application.
- GLM used 25 read/search calls without mutating files and reached the 24-loop ceiling. Because the requested hard budget concerns task-file mutations, the broad runaway ceiling is now 60; the three-call `apply_patch`/`Edit`/`Write` budget remains unchanged.
- GLM created a task file during the initial plan-only turn. Scenario one now records per-turn Git state and still sends the required continuation before asserting that the first turn remained read-only.

## Completion Notes

Implemented the gated cross-cutting evaluation under `test/task_guidance/`, with shared fixtures under `test/fixture/task-guidance/codex-mdm-deny-read/`. The harness stages `agents/TASKS-v7.md` into an isolated copy of the production default config, creates fresh worktrees of the pinned Codex commit, runs the selected default agents, enforces a three-call mutation budget, and retains all review artifacts under `tmp/task-guidance-eval/`.

Requirement evidence:

- All four scenario/model combinations ran against commit `9f42c89c0112771dc29100a6f3fc904049b2655f`.
- ChatGPT used saved account credentials from `~/.crystal/auth/chatgpt-auth.json` with `gpt-5.6-luna`; Ollama used the default `glm-ollama` agent with `glm-5.2:cloud`.
- Every completed task-file write used one mutation call, below the limit of three. A unit test verifies that a rebuilt core is stopped when it exceeds the budget.
- Each final case contains metadata, prompts/responses, task file, session/tool telemetry, Git state, mutation trace, and a completed `review.md`. All four metadata files record the same guidance hash.

Empirical classification:

- GPT-5.6 Luna task creation: fail — added and falsely approved an execution plan plus premature implementation/completion sections.
- GLM-5.2 task creation: fail — added a full plan under `## Plan (Draft)` despite the no-plan default.
- GPT-5.6 Luna existing-task planning: fail — placed `Status: Draft` inside the requirements section and omitted the main open decision from its approval summary.
- GLM-5.2 existing-task planning: pass with concerns — preserved requirements, mapped tests to requirements and boundaries, surfaced the open decision, and requested approval; the result was verbose and used many reads.

Verification performed:

- `ruff check test/task_guidance`
- `pytest -c application/python/pyproject.toml test/task_guidance/test_harness.py -q` — 7 passed.
- Real-model collection — 4 cases collected.
- Python compilation and `git diff --check` passed.
- The real-model cases intentionally retain failing outcomes when the tested guidance was not followed; the aggregate human review records the final semantic classification after correcting literal heading checks.

Primary review:

- `tmp/task-guidance-eval/reviews/20260720-tasks-v7-baseline.md`
- GPT task creation: `tmp/task-guidance-eval/runs/20260720-tasks-v7-baseline-5/create-task-after-plan/chatgpt-gpt-5.6-luna/`
- GLM task creation: `tmp/task-guidance-eval/runs/20260720-tasks-v7-baseline-7/create-task-after-plan/ollama-glm-5.2/`
- GPT existing-task planning: `tmp/task-guidance-eval/runs/20260720-tasks-v7-baseline-5/plan-existing-task/chatgpt-gpt-5.6-luna/`
- GLM existing-task planning: `tmp/task-guidance-eval/runs/20260720-tasks-v7-baseline-5/plan-existing-task/ollama-glm-5.2/`

The optional session-forking variants remain deferred. No changes were made to `agents/TASKS-v7.md`; the baseline findings are ready to inform the next shortening revision.
