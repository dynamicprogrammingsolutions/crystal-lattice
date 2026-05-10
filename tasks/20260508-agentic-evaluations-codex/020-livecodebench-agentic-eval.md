# LiveCodeBench Agentic Evaluation

Extend the shared `evaluations/` package from the RepoQA task with an agentic LiveCodeBench runner that gives the agent a task workspace, public-test workflow, and a final submission artifact while keeping hidden grading outside the agent-visible workspace.

## Requirements checklist

- [ ] Reuse the shared `evaluations/` package, config-dir convention, auth commands, result format, and scheduler created in `010-repoqa-agentic-eval.md`.
- [ ] Add LiveCodeBench download support and deterministic manifest generation on the shared CLI.
- [ ] Materialize LiveCodeBench agentic task workspaces with a clear contract for:
  - task statement
  - starter code if present
  - submission file target
  - public tests and public-test runner
  - metadata
- [ ] Run tasks through the same `AgentApplication` path and per-task workspace overrides used by RepoQA.
- [ ] Keep hidden tests outside the agent-visible workspace and outside `allowed_paths`.
- [ ] Grade final submissions externally against hidden tests and store the scored artifact in the shared result schema.
- [ ] Preserve the same run-frequency and working-hours semantics as RepoQA.
- [ ] Add tests covering manifest generation, workspace construction, submission extraction, hidden/public test separation, and at least one fixture-backed benchmark run.

Parent Task: `tasks/20260508-agentic-evaluations-codex/000-main.md`

Depends On: `tasks/20260508-agentic-evaluations-codex/010-repoqa-agentic-eval.md`

## Functional target

Each LiveCodeBench task should become a small coding workspace, for example:

```text
evaluations/workspaces/livecodebench/<task-id>/
  TASK.md
  meta.json
  public_tests.json
  run_public_tests.sh
  submission/
    solution.py
```

The agent should:

- read `TASK.md`
- inspect starter files if present
- edit or write the submission artifact
- optionally run public tests
- finish by signaling completion in a deterministic way, for example `READY`

The benchmark harness should then:

- read the submission artifact from disk
- run hidden grading outside the agent workspace
- store pass/fail and related metadata

## Safety and comparability requirements

- Hidden tests must never be readable through benchmark tools.
- Public tests may be exposed for realism, but they must be consistent across runs.
- The same workspace contract must apply across agents/configs.
- Result metadata should make it explicit that this is a custom/agentic LiveCodeBench mode, not the official plain-prompt benchmark.

## Reuse expectations

This task should reuse the shared interfaces and design decisions from RepoQA:

- same config-dir contract
- same `.env` loading behavior
- same top-level `agentic_evaluations` settings subtree
- same ChatGPT auth handling
- same task scheduler / working-hours gating
- same `AgentApplication` runner abstraction
- same result-writing style

Do not create a second CLI or a second benchmark-runner stack for LiveCodeBench.

## Existing implementation patterns to reuse

- The same Codex/OpenAI default config references from `application/python/agent_terminal_app/default_config/config.json:13-121` and `application/python/agent_terminal_app/default_config/config.json:340-355` apply here.
- Existing Codex/OpenAI agent definitions remain the baseline in `application/python/agent_terminal_app/default_config/config.json:505-535`.
- Per-task workspace overrides are already demonstrated in `application/python/tests/test_terminal_default_config_codex_gpt5_apply_patch_real_api.py:168-177`.
- The shell-command tool contract that benchmark prompts should implicitly rely on already exists in `plugins/codex-tools/src/codex_tools/shell_command_tool.py:31-110`.

## External benchmark references

- Official LiveCodeBench repository:
  - `https://github.com/LiveCodeBench/LiveCodeBench`
- LiveCodeBench homepage:
  - `https://livecodebench.github.io/`
- Official dataset page:
  - `https://huggingface.co/datasets/livecodebench/code_generation_lite`
- Current upstream release/version notes already verified during research:
  - `release_v6` is the latest full release referenced in the upstream README during research
  - `release_v6` contains `1055` problems overall
  - the fine-grained `v6` slice corresponds to `test6.jsonl`
  - the inspected `v6` fine-grained slice contained `175` tasks
- Upstream dataset file layout already verified during research:
  - dataset repo contains `test.jsonl`, `test2.jsonl`, `test3.jsonl`, `test4.jsonl`, `test5.jsonl`, `test6.jsonl`
  - upstream dataset builder maps:
    - `release_v1` -> `test.jsonl`
    - `release_v6` -> all six files
    - `v6` -> `test6.jsonl`
- Official benchmark fields and semantics in upstream LiveCodeBench:
  - prompt-visible fields include `question_title`, `question_content`, `starter_code`
  - local grading fields include public/private test cases and metadata
  - official upstream defaults use multi-sample generation, but this task intentionally defines a custom/agentic mode instead

These upstream references should be treated as the benchmark-side source of truth for:

- release/version naming
- dataset download behavior
- task ids and task metadata
- public/private test semantics
- baseline grading interpretation

## Prompt and artifact guidance

Prefer an artifact-first flow over a chat-only answer:

- the prompt should direct the agent to write the final solution to a known file path
- the runner should grade that file, not scrape code out of the assistant message unless no file was produced
- the final assistant response can be a small sentinel such as `READY`

This keeps the benchmark closer to how coding agents are actually used and avoids output truncation or markdown-format drift in long solutions.

## Suggested CLI shape

Keep the interface parallel to RepoQA:

```text
python -m agent_evaluations download livecodebench --config-dir evaluations/config/main --release v6
python -m agent_evaluations manifest livecodebench --config-dir evaluations/config/main --limit 20 --seed 1
python -m agent_evaluations run livecodebench --config-dir evaluations/config/main --agent-id codex-openai
python -m agent_evaluations run livecodebench --config-dir evaluations/config/main --agent-id codex-openai-api
```

## Notes for completion

- Start with one language/runtime path if that simplifies the first implementation, but keep the workspace/result schema extensible enough for future language expansion.
- Preserve enough execution metadata to compare two runs beyond score alone:
  - submission produced or not
  - public-test result if used
  - hidden-test result
  - task wall time
  - tool-call count
  - provider-call count if available
- Keep the grading path deterministic and local to the evaluation harness.