# Task Guidance Real-Model Evaluation

This human-operated evaluation runs the repository task-file guidance against a
pinned OpenAI Codex checkout. Real-model runs, mechanical assertions, GLM
empirical review, and review-bundle generation are separate CLI steps.

Supported model paths:

- Ollama through its OpenAI-compatible endpoint; the default agent is
  `glm-ollama` and its model comes from the default application config.
- ChatGPT account auth; the default model is `gpt-5.6-luna`.

Run `--help` for copyable starting commands:

```bash
python test/task_guidance/task_guidance_eval.py --help
```

Each successful command prints the next most obvious command. `run --assert`
combines model execution with the mechanical assertion step, `assert --review`
also requests the GLM empirical review, and `review --bundle` prepares the
review bundle afterward.

## Scenarios

- `plan`: inspect the pinned repository and produce a plan without changing it.
- `retain-plan`: fork a planning session and create a task that retains the
  execution plan as `Draft`.
- `omit-plan`: fork the same planning session and create a task that retains
  requirements and supporting context but omits the execution plan.
- `existing-task-plan`: add the premade requirements task and ask for a draft
  execution plan.

The retain/omit forks may follow a fresh `plan` step in the same command or
reuse `session-1.json` from an older case through `--source-case`. Imported
sessions record both their source provenance and the current guidance hash.

## Quick start with an existing GLM planning session

```bash
python test/task_guidance/task_guidance_eval.py run \
  --steps retain-plan,omit-plan \
  --provider ollama \
  --source-case \
    tmp/task-guidance-eval/runs/20260721-tasks-v7-revision-6/create-task-after-plan/ollama-glm-5.2 \
  --run-id task-guidance-fork-smoke \
  --assert
```

## Fresh run

```bash
python test/task_guidance/task_guidance_eval.py run \
  --steps plan,retain-plan,omit-plan \
  --provider ollama \
  --run-id task-guidance-fresh
```

Use ChatGPT account credentials instead:

```bash
python test/task_guidance/task_guidance_eval.py run \
  --steps plan,retain-plan,omit-plan \
  --provider chatgpt \
  --model gpt-5.6-luna \
  --credentials-dir "$HOME/.crystal" \
  --run-id task-guidance-chatgpt
```

Useful run options:

- `--agent` and `--model` select the effective agent/model.
- `--credentials-dir` selects the ChatGPT account state directory.
- `--ollama-base-url` defaults to `http://localhost:11434/v1`.
- `--guidance` defaults to `agents/TASKS-v7.md`.
- `--steps` accepts a comma-separated list.
- `--assert` runs mechanical assertions immediately after the model steps.

## Separate mechanical assertions

```bash
python test/task_guidance/task_guidance_eval.py assert \
  --run-dir tmp/task-guidance-eval/runs/<run-id>
```

Use `--case` to select one scenario. Add `--review` to run the GLM empirical
review after the mechanical assertions finish; assertion failures still remain
visible through the command's nonzero exit status.

Mechanical checks intentionally stay small: expected task structure, fork
provenance, requirement identifiers, retained factual research markers,
requirement-verification traceability, allowed mutations, and absence/presence
of the requested execution plan. Semantic requirement alignment remains an
empirical human-reviewed judgment.

## Separate GLM empirical review

```bash
python test/task_guidance/task_guidance_eval.py review \
  --run-dir tmp/task-guidance-eval/runs/<run-id>
```

The reviewer receives the saved task, response, fixture requirements, and
mechanical assertions. It writes `empirical-review.md` and the raw request and
response artifacts, but its judgment does not control the command exit status.
Humans decide whether the behavior is acceptable. Add `--bundle` to prepare the
review bundle immediately afterward.

## Review bundle

```bash
python test/task_guidance/task_guidance_eval.py bundle \
  --run-dir tmp/task-guidance-eval/runs/<run-id>
```

Bundles are written under:

```text
tmp/task-guidance-eval/review-bundles/<run-id>/
```

They include exported user/assistant/commentary messages with intervening tool
counts, the exact `TASKS.md`, the request-time compiled system/developer
message, full sessions, generated task files, mechanical assertions, empirical
reviews, and Git/tool telemetry.

## Prerequisites

- Ollama at `OLLAMA_OPENAI_BASE_URL`, defaulting to
  `http://localhost:11434/v1`.
- For ChatGPT runs, saved account credentials under
  `<credentials-dir>/auth/chatgpt-auth.json`; the default credentials directory
  is `~/.crystal`.
- Network access when the pinned repository or ChatGPT provider is used.

Artifacts are retained under:

```text
tmp/task-guidance-eval/runs/<run-id>/<scenario>/<model>/
```

The checkout cache lives under `tmp/task-guidance-eval/repo-cache/`.

Pytest covers only deterministic CLI, assertion, and artifact helpers; it does
not contact real models.