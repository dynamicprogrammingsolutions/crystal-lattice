# Build a Real-Model Evaluation Workflow for Task-File Guidance

Create a reviewable evaluation workflow that exercises the repository task-file guidance with real agents, preserves complete run artifacts, and lets humans run model scenarios, mechanical assertions, and empirical guidance review as separate steps.

## Requirements checklist

- [x] R1: Exercise task-file behavior against a pinned real repository and the default application harness rather than a synthetic agent stub.
  - Evidence: the harness checks out OpenAI Codex commit `9f42c89c0112771dc29100a6f3fc904049b2655f` and uses the copied default application configuration.
- [x] R2: Support ChatGPT account authentication with `gpt-5.6-luna` and Ollama with the configured GLM-5.2 model.
  - Evidence: `test/task_guidance/task_guidance_eval.py` accepts provider, agent, model, ChatGPT credentials-directory, and Ollama endpoint overrides.
- [x] R3: Test both creating a task after planning and adding a draft execution plan to an existing requirements task.
  - Evidence: the CLI supports `plan`, `retain-plan`, `omit-plan`, and `existing-task-plan` steps.
- [x] R4: Fork the same completed planning session into explicit retain-plan and omit-plan continuations.
  - Evidence: the two fork prompts are defined in `test/task_guidance/harness.py`, and each fork records the parent-session hash and receives an independent clean checkout.
- [x] R5: Preserve the exact guidance version and enough request/session evidence to reproduce and review each result.
  - Evidence: every case records `TASKS.md`, its SHA-256, request-time compiled system/developer messages, prompts, responses, full sessions, events, Git state, and tool telemetry.
- [x] R6: Export human-readable review artifacts containing all visible user, assistant commentary, and final assistant messages with intervening tool-call counts.
  - Evidence: `test/task_guidance/prepare_review_bundle.py` produces per-case transcripts, assertion reports, failures, task files, sessions, compiled prompts, and review metadata.
- [x] R7: Enforce a small task-file mutation budget and retain a broad tool-loop ceiling without treating extensive read-only research as a model failure.
  - Evidence: mutation calls are recorded and limited separately from the tool loop; proportional read-only tool use is not part of the review verdict.
- [x] R8: Separate model execution, deterministic assertions, empirical review, and bundle creation so humans can run and inspect each stage independently.
  - Evidence: `test/task_guidance/task_guidance_eval.py` exposes `run`, `assert`, `review`, and `bundle` commands.
- [x] R9: Make the CLI self-guiding with copyable `--help` examples, a suggested next command after each stage, and practical combined forms.
  - Evidence: the CLI supports `run --assert`, `assert --review`, and `review --bundle`, and each command prints the next review step.
- [x] R10: Keep mechanical assertions small and objective, and use empirical review only for understanding task-guidance concepts that cannot be checked structurally.
  - Evidence: structural assertions cover task shape, fork provenance, requirement identifiers, retained research markers, plan presence, and mutation limits; the empirical rubric is limited to requirements versus tasks, supporting details versus plan content, and presentation rules.
- [x] R11: Do not use empirical review to score repository understanding, implementation quality, technical test adequacy, architectural judgment, or overall model intelligence.
  - Evidence: the final review prompt explicitly excludes those judgments from its overall guidance-compliance result.
- [x] R12: Document prerequisites, model selection, scenario commands, separate assertions, empirical review, artifact locations, and review-bundle generation.
  - Evidence: `test/task_guidance/README.md` documents the complete human-operated workflow.

## Background and scope

The original evaluation request was to test the task-file instructions with two real models using a pinned, nontrivial repository task:

- ChatGPT account auth with `gpt-5.6-luna`, using credentials under `~/.crystal`.
- Ollama with GLM-5.2.
- A Codex repository fixture involving macOS MDM-delivered requirements and home-relative `deny_read` paths.
- A first scenario that asks for a plan and then asks for a task file.
- A second scenario that starts from a premade requirements task and asks for an execution plan.

The evaluation was also required to retain reviewable sessions, messages, task files, compiled prompts, assertions, and failures. Model calls were constrained by a task-file mutation budget and a broad tool-loop limit.

Review of the first runs showed that the continuation “OK, create a single task file” was conversationally ambiguous. The final workflow therefore uses two explicit forks:

- Retain the prior plan as a separate draft execution plan.
- Preserve the requirements and supporting context while omitting the execution plan.

The task-file guidance was refined alongside the evaluation so that requirements, supporting details, execution plans, requirement questions, and design decisions have distinct meanings.

## Relevant implementation

- Task guidance: `agents/TASKS-v7.md`
  - Supporting-details definition near line 10.
  - Explicit retain/omit handoff behavior near line 33.
  - Requirement-question and design-decision handling near line 47.
- Shared prompts and harness: `test/task_guidance/harness.py`
- Human-operated CLI: `test/task_guidance/task_guidance_eval.py`
  - `run_command` near line 435.
  - `assert_run` near line 526.
  - `review_command` near line 685.
  - `bundle_run` near line 719.
  - CLI construction and help near line 732.
- Mechanical and manual assertion generation: `test/task_guidance/prepare_review_bundle.py`
- Empirical review checklist: `test/fixture/task-guidance/codex-mdm-deny-read/review-template.md`
- Premade requirements fixture: `test/fixture/task-guidance/codex-mdm-deny-read/premade-task.md`
- Usage documentation: `test/task_guidance/README.md`

## Execution plan

Status: Approved

This plan was approved before implementation and is recorded retrospectively so another agent can understand the intended boundaries and the decisions that governed the work.

### Approach

1. Checkpoint the existing real-model pytest harness and review-artifact work in a focused commit without including unrelated repository changes.
2. Refine `agents/TASKS-v7.md` so:
   - Requirements remain concise and verifiable.
   - Factual research and supporting details remain available below the requirements.
   - A user explicitly chooses whether a prior plan is retained or omitted.
   - Retained plans occupy a separate `## Execution plan`.
   - Requirement questions and material design decisions have distinct handling.
3. Replace the real-model pytest entry point with a command-line workflow:
   - `run` executes selected model steps and saves artifacts.
   - `assert` applies deterministic checks to existing artifacts.
   - `review` asks GLM for a separate empirical review.
   - `bundle` prepares an easy-to-review directory.
4. Support both fresh planning and imported planning sessions:
   - A fresh `plan` step may feed both forks.
   - `--source-case` may reuse `session-1.json` from a prior run, even when that planning turn used an older guidance version.
   - Each fork uses the current selected guidance and an independent clean worktree.
5. Keep assertions intentionally small:
   - Verify task shape, expected file changes, mutation limit, guidance hash, session provenance, requirement identifiers, research markers, and required plan structure.
   - Leave semantic distinctions that cannot be established mechanically to empirical review.
6. Capture complete review evidence:
   - Exact guidance snapshot and hash.
   - Full compiled system/developer message.
   - Sessions, events, prompts, responses, task files, diffs, failures, and tool counts.
   - Human-readable message export and assertion report.
7. Make the CLI easy for humans to operate:
   - Include copyable commands in `--help`.
   - Print the next obvious command after each stage.
   - Support `run --assert`, `assert --review`, and `review --bundle`.
8. Verify the implementation with deterministic unit tests and one small Ollama smoke that forks an already-completed GLM planning session.
9. Keep later empirical-review scope corrections in a separate focused commit.

### Requirement verification

- R1–R5: Verify through deterministic harness tests, guidance hashes, captured compiled prompts, source-session provenance, and the imported-session Ollama fork smoke.
- R6: Verify the exporter against deterministic session fixtures containing user, commentary, tool, and final-assistant messages.
- R7: Verify mutation detection and limit accounting with unit tests and inspect mutation telemetry from the smoke run.
- R8–R9: Verify CLI parsing, `--help` output, combined flags, and printed next commands without contacting a model.
- R10–R11: Verify the generated assertion set and empirical prompt text with unit tests; confirm that technical-quality judgments are explicitly outside the review verdict.
- R12: Inspect the README commands and run Python compilation, Ruff, and Markdown/diff whitespace checks.

### Documentation

Update `test/task_guidance/README.md` for developers and human evaluators. It must explain:

- What each scenario does.
- How to select Ollama or ChatGPT account models.
- How to reuse an existing planning session.
- How to run assertions independently.
- How to request the separate GLM empirical review.
- How to prepare and locate the review bundle.
- Which checks are mechanical and which require human interpretation.

No product-user documentation is required because this is repository evaluation infrastructure rather than an application feature.

### Task checklist

- [x] Checkpoint the initial real-model evaluation and review exporter.
- [x] Define requirements, supporting details, open questions, and material design decisions in the guidance.
- [x] Add explicit retain-plan and omit-plan continuation prompts.
- [x] Add requirement identifiers and precise relative-path behavior to the Codex fixture.
- [x] Replace the real-model pytest runner with the human-operated CLI.
- [x] Add imported-session fork provenance and independent fork worktrees.
- [x] Add separate deterministic assertion, GLM review, and bundle commands.
- [x] Add copyable help examples, next-step output, and combined flags.
- [x] Add deterministic CLI, assertion, reviewer, and exporter tests.
- [x] Run the imported-session Ollama fork smoke.
- [x] Narrow empirical review from model quality to task-guidance clarity.
- [x] Commit the completed implementation in focused commits.

## Implementation Notes

These notes were added retrospectively from the findings recorded during completion.

### Initial harness and artifact capture

- The first implementation used a gated real-model pytest module with two model cases and two task workflows.
- Exact guidance snapshots were added at both run and case level. A run refuses to continue if the same run ID is reused with a different guidance file.
- Request-time prompt capture was added around `AgentCore._pre_request`:
  - ChatGPT captures `request.instructions`.
  - GLM captures the rendered system request.
- The exporter was added so old and new runs can be reviewed without manually opening raw event/session files.

### Assertion findings

- A broad approval regex initially treated the negative sentence “not to track the plan as Draft/Approved” as a positive approval claim.
- The assertion was narrowed to detect positive approval claims, and a deterministic regression test was added.
- Structural assertions could pass even when a model preserved a plan under headings such as “Proposed implementation direction.” This established that heading checks alone cannot decide whether the omit-plan instruction was understood in substance.
- Requirement identifiers and research markers were introduced only as traceability checks. They are not intended to prove that the implementation plan is technically correct.

### Guidance and scenario findings

- The original default no-plan expectation conflicted with ordinary conversational interpretation after the assistant had just presented a plan.
- The guide also asked for enough handoff detail to avoid rediscovery, which overlapped with the definition of an execution plan.
- The scenario was changed from an ambiguous “OK, create a single task file” continuation to two explicit forks:
  - `Create a single task file and include the execution plan as Draft.`
  - `Create a single task file with the requirements and supporting context, but omit the execution plan.`
- Omitting a plan was clarified not to mean dropping factual research. The common handoff retains requirements, findings, supporting details, accepted decisions, and unresolved questions.
- Requirements remain concise; explanatory details may live below them, but must not silently introduce an untracked completion condition.

### CLI extraction

- Real-model execution was removed from pytest. Pytest now covers only deterministic helpers.
- The CLI accepts comma-separated steps and can run a fresh plan or fork an older `session-1.json`.
- Fork metadata records the parent-session hash, source case, old provenance, current guidance hash, shared tool calls, branch tool calls, and branch mutation calls.
- `run` does not judge model behavior. `assert` produces objective checks. `review` produces a GLM opinion for human inspection without using that opinion as the process exit status.
- `--help` includes copyable commands, and each stage prints the next expected command.

### Smoke-run findings

- The first CLI smoke attempt failed before either model call because pytest had previously supplied placeholder provider and cloud environment variables implicitly.
- A reusable per-case environment context was added to the CLI, including cleanup of `RuntimeEnvOverlay`.
- The corrected imported-session smoke completed both GLM continuations:
  - Retain-plan fork: 13 PASS, 2 MANUAL, 0 FAIL; 2 branch tool calls; 1 mutation.
  - Omit-plan fork: 13 PASS, 2 MANUAL, 0 FAIL; 5 branch tool calls; 1 mutation.
- The guidance SHA-256 used by the successful smoke matched the working guide:
  - `11894d337de6685191a5adc622963a9a8fd526be302f439eb71658e84234276b`
- The smoke intentionally reused a planning session created under an older guide. The continuation requests compiled and used the current guide, demonstrating the intended fork compatibility path.

### Review-scope correction

- The first empirical checklist mixed guidance compliance with model intelligence and plan quality.
- Checks such as whether the plan was technically correct, whether tests were sufficient, whether the model chose the best design, and whether the plan truly satisfied every requirement were removed.
- The final empirical review is limited to guidance concepts that cannot be checked reliably with simple assertions:
  - Requirements versus execution tasks.
  - Supporting details versus hidden requirements or relabeled plan steps.
  - Retain-plan versus omit-plan behavior in substance.
  - The requested presentation level for requirement verification and documentation.
  - Whether the user-facing response is easier to review than the full stored plan.
- Model-reasoning observations may be recorded separately but do not affect the overall task-guidance compliance judgment.

## Completion Notes

These completion notes were added retrospectively after the implementation was complete.

### Outcome

- The repository now has a human-operated real-model task-guidance evaluation CLI.
- The task guidance supports explicit retain-plan and omit-plan handoffs while preserving factual research and supporting details.
- Real-model execution, mechanical assertions, empirical review, and bundle generation are separate, composable stages.
- The empirical review evaluates instruction clarity rather than model quality.

### Commits

- `d9ff98ba` — `Add real-model task guidance evaluation`
- `91408506` — `Add reviewable task guidance evaluation`
- `13665e82` — `Add explicit task handoff forks and evaluation CLI`
- `6c6bf88e` — `Focus task guidance review on instruction clarity`

All four commits are ancestors of the current `develop` branch.

### Verification

- Ruff passed for `test/task_guidance`.
- Python compilation passed for the CLI, harness, and exporter.
- Diff whitespace checks passed.
- Final deterministic suite: 22 passed.
- Final Ollama smoke artifacts:
  - `tmp/task-guidance-eval/runs/20260721-task-guidance-cli-fork-smoke-2`
- No final GLM empirical review was executed automatically; that is deliberately a human-invoked step.
- No fresh ChatGPT run or fresh full planning run was required for the final CLI smoke.

### Human commands

```bash
python test/task_guidance/task_guidance_eval.py --help
```

```bash
python test/task_guidance/task_guidance_eval.py assert \
  --run-dir tmp/task-guidance-eval/runs/20260721-task-guidance-cli-fork-smoke-2
```

```bash
python test/task_guidance/task_guidance_eval.py review \
  --run-dir tmp/task-guidance-eval/runs/20260721-task-guidance-cli-fork-smoke-2 \
  --model glm-5.2:cloud
```

```bash
python test/task_guidance/task_guidance_eval.py bundle \
  --run-dir tmp/task-guidance-eval/runs/20260721-task-guidance-cli-fork-smoke-2
```

## Post-completion follow-up

These follow-ups were requested and completed after the initial evaluation implementation.

### Reviewable artifacts

- Added exported conversations containing all visible user, assistant commentary, and final assistant messages with intervening tool-call counts.
- Added exact guidance snapshots, compiled system/developer prompts, assertions, raw failures, task files, sessions, and telemetry to review bundles.
- Added a standalone exporter that can prepare bundles from already-existing artifacts.

### Guidance iteration and result analysis

- Adjusted the guide through the permitted revision budget and preserved the exact version used by every run.
- Documented the main behavioral differences observed between GPT and GLM.
- Identified the overlap between required handoff completeness and execution-plan content.

### Explicit session forks

- Replaced the ambiguous default continuation with explicit retain-plan and omit-plan branches from the same planning session.
- Preserved factual research and supporting details in the omit-plan branch.
- Added definitions and handling rules for requirement questions, design decisions, and material design decisions.

### Human-operated workflow

- Replaced real-model pytest execution with the CLI.
- Added provider, model, credentials, endpoint, guidance, run-step, source-session, and run-ID options.
- Added copyable `--help` commands, next-step output, and combined flags.
- Kept deterministic pytest coverage for the CLI and artifact helpers.

### Empirical review boundary

- Removed checks that evaluated repository understanding, implementation quality, technical test adequacy, architectural judgment, or general model intelligence.
- Retained only guidance-understanding checks that cannot be reduced to simple structural assertions.