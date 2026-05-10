# Agent Evaluations

Shared benchmark package for agentic evaluations.

The first implemented benchmark is RepoQA in agentic mode. The package is
designed to run benchmark tasks through `AgentApplication`, using config
directories that can support both OpenAI API auth and ChatGPT-login auth.

## Config Dir Convention

Each evaluation environment should live in its own directory, for example:

```text
evaluations/config/main/
  .env
  config.json
  AGENTS.md
  auth/
    chatgpt-auth.json
    chatgpt-rate-limits.json
  profiles/
    repoqa-openai-api.json
    repoqa-chatgpt.json
```

`config.json` should include benchmark settings under the top-level
`agentic_evaluations` key.

## CLI

Examples:

```text
python -m agent_evaluations auth login-chatgpt --config-dir evaluations/config/main --agent-id codex-openai
python -m agent_evaluations auth status --config-dir evaluations/config/main --agent-id codex-openai
python -m agent_evaluations download repoqa --config-dir evaluations/config/main --release 2024-06-23
python -m agent_evaluations manifest repoqa --config-dir evaluations/config/main --release 2024-06-23 --language python --limit 25 --seed 1
python -m agent_evaluations run repoqa --config-dir evaluations/config/main --agent-id codex-openai-api --manifest-path /path/to/manifest.json
python -m agent_evaluations container build --config-dir evaluations/config/main
python -m agent_evaluations run repoqa --config-dir evaluations/config/main --agent-id codex-openai --runtime-backend docker
```

## Run Profiles

Profiles are optional JSON files stored under `profiles/` in the config
directory. They let you freeze a repeatable run configuration, including:

- benchmark id
- agent id
- model overrides
- release/language/seed/limit
- task scheduling policy
- retry policy

Every `run` command writes a concrete `run-manifest.json` artifact so the exact
task plan can be reused later.

## Docker Runtime

Docker execution is optional and uses the same scheduler, manifests, retries,
and scoring logic as host execution.

- Build the runner image with `container build`.
- Docker image builds use a clean tracked-files source bundle created from the
  current Git revision instead of sending the live repo tree as the build
  context.
- The evaluation runner itself is installed from a separately built wheel
  artifact, so the clean source bundle does not need to contain the
  `evaluations/` directory.
- Select Docker with `--runtime-backend docker` or a run profile.
- Each task runs in its own short-lived container.
- The config directory is mounted at `/config`.
- The task workspace is mounted at `/workspace` by default.
- Results are mounted separately at `/results`, so `results_root` does not need
  to live under the config directory.
- The bundled default Dockerfile lives at `evaluations/docker/RepoqaRunner.Dockerfile`.
