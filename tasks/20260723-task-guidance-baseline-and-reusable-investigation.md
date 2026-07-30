# Validate Revised Task Guidance with Reusable Unguided Investigation

Evaluate the revised task-file guidance against the previous guidance and the corrected evaluation rubric while avoiding repeated repository investigation. The planning seed must run without task-file guidance, then be reusable by guided task-creation forks so comparison runs differ only at their intended guidance or evaluator boundary.

## Requirements checklist

- [x] **R1. Three attributable comparison states:** Review artifacts exist for (a) the original `TASKS-v7.md` with the pre-correction evaluator, (b) the revised `TASKS-v7.md` with the same pre-correction evaluator, and (c) the revised guidance with the corrected evaluator. The artifacts identify the exact guidance, evaluator, model, prompt, and source investigation used.
- [x] **R2. Guidance-neutral investigation:** The initial repository investigation and planning request runs as if task guidance were disabled and does not receive `TASKS-v7.md` in its compiled request.
- [x] **R3. Reusable investigation:** A compatible saved investigation session can seed later retain-plan and omit-plan task-creation cases across guidance revisions without rerunning the investigation.
- [x] **R4. Guided task creation:** Each task-creation fork receives the selected task guidance even when its imported investigation session was created without guidance.
- [x] **R5. Corrected evaluation coverage:** The final evaluator distinguishes user-observable requirement acceptance evidence from implementation-specific verification and reviews whether material open questions are prominent and the handoff is concise.
- [x] **R6. Comparable provenance:** The evaluation prevents or clearly reports incompatible source-session reuse and makes it possible to confirm that comparison cases share the same investigation-session content.
- [x] **R7. Documented and tested workflow:** Deterministic tests cover the new seed/fork behavior and evaluator contracts, and the task-guidance evaluation README explains the generic guidance-neutral investigation and source-case reuse capabilities.

## Scope

This task changes only the task-guidance evaluation harness, fixtures, assertions, review rubric, and documentation. It does not change production task loading or the application’s user-facing task-guidance checkbox.

In this task, **original guidance** means `agents/TASKS-v7.md` at `cd1ed06b`, immediately before guidance commit `182ea572`. **Revised guidance** means the file at `182ea572`.

## Decisions

### Third-state model execution

Reevaluate the second state’s saved response with the corrected assertions and empirical rubric. This isolates the evaluator change; a new stochastic model response would confound that comparison. A fresh corrected-evaluator model run may be retained as supplementary evidence.

### Canonical comparison model

Use one pinned Ollama/GLM model for the canonical comparison because it is reproducible and inexpensive, then run the revised guidance and corrected evaluator with the pinned ChatGPT/Codex model as supplementary confirmation. Requiring both models for all three states doubles model work without improving isolation of the guidance and evaluator changes.

## Supporting details

### Existing evaluation stages

`test/task_guidance` already separates:

- a planning seed;
- retain-plan and omit-plan forks;
- deterministic mechanical assertions;
- a separate GLM empirical review;
- review-bundle generation.

`--source-case` can import `session-1.json`, but the planning seed currently starts with task guidance enabled. The case configuration and every `send_turn` override set `include_tasks: true`, and `start_agent` asserts that value.

### Current provenance

Cases retain the selected guidance snapshot and hash, source-case path, fork-parent session hash, compiled request, sessions, prompts, responses, Git status, and tool telemetry. Imported sessions record the current case’s guidance hash, but source compatibility is not modeled independently of guidance.

A reusable investigation should be keyed by inputs that can affect investigation behavior, including the pinned repository revision, provider/model and relevant request options, investigation prompt, effective non-guidance configuration, and session content. The guidance hash must not be part of that compatibility key because guidance is intentionally absent from the seed.

### Current assertion gap

The existing mechanical assertions still pass after the guidance revision. They verify structure, preservation, traceability, mutation scope, plan retention/omission, and approval state.

The empirical rubric still asks for an “evidence type and test boundary,” does not assess separation of additional implementation verification, and does not assess top-level open-question visibility or concision. These semantic properties should remain empirical/manual checks rather than brittle word-count or exact-heading-position failures.

### Comparison refs

- Original-guidance base: `cd1ed06b`
- Revised-guidance, old evaluator: `182ea572`
- Corrected evaluator: a new commit based on the revised-guidance state

The guidance-neutral seed optimization must be present in both original- and revised-guidance comparison environments. It should be isolated from the evaluator correction so it does not become an untracked difference between the first two states.

## Execution plan

Status: Approved

Use one guidance-neutral investigation session for all comparable task-creation cases. Keep the seed optimization in a standalone commit that can be applied to both guidance refs, and keep evaluator/rubric corrections in a later commit.

### Implementation direction

#### Guidance-neutral seed and guided forks

Make task-guidance inclusion explicit per model turn rather than assuming it is always enabled:

- planning seeds set task-guidance inclusion to false;
- retain-plan, omit-plan, and existing-task planning turns set it to true;
- the captured request and case metadata record whether guidance was enabled;
- assertions prove that the seed request excludes the guidance and guided forks include the selected guidance.

Keep the selected guidance snapshot with a task-creation case for provenance even when its imported planning seed was guidance-neutral. Do not treat the presence of an artifact snapshot as proof that the request received it.

#### Reusable source compatibility

Represent the guidance-neutral investigation as a reusable source artifact with a compatibility fingerprint derived from inputs that affect that investigation: repository revision, model/provider and relevant request options, investigation prompt, and effective non-guidance configuration. Record the source session hash separately.

Validate this compatibility before importing a source case. Exclude the task-guidance hash because guidance was absent from the source request. Report incompatible reuse clearly instead of silently rerunning the investigation or accepting incomparable input.

#### Comparison branches and commits

Create an original-guidance branch from `cd1ed06b`. Implement the seed/reuse optimization as an isolated commit and apply the same commit to the revised-guidance state at `182ea572`.

Produce the three comparison states in this order:

1. original guidance plus the pre-correction evaluator;
2. revised guidance plus the same pre-correction evaluator;
3. revised guidance plus the corrected evaluator.

All states use the same compatible source investigation. Keep evaluator corrections in a later commit so the first two states differ only by guidance. Subject to the open question above, reevaluate state two’s generated artifact for state three so the evaluator change is isolated from model variability.

#### Evaluator correction

Retain strict mechanical checks for structure, provenance, requirement-ID traceability, mutation scope, approval, and plan retention or omission. Update the empirical prompt, manual review checks, and human review template to assess:

- acceptance evidence at a user-relevant or public boundary;
- separation of implementation-specific robustness checks;
- prominence of material open questions;
- concision without repeated requirements, investigation chronology, or exhaustive inventories.

Add deterministic compatibility coverage for H4 requirement groups and optional `### Additional implementation verification`, but do not make that optional section universally required.

### Requirement verification

#### R1 and R6: attributable three-state comparison

- Inspect the three review bundles and their metadata to confirm the original/revised guidance hashes, old/corrected evaluator refs, identical model and task prompts, and identical imported investigation-session hash.
- Confirm the first two states differ only in task guidance and the third state reevaluates the revised-guidance artifact or explicitly identifies any fresh generation as supplementary.

#### R2–R4: neutral reusable investigation and guided forks

- Run a real planning seed with guidance disabled and inspect the captured compiled request to confirm task guidance is absent.
- Reuse that saved session for original-guidance and revised-guidance retain-plan/omit-plan forks, then inspect each fork’s compiled request to confirm its selected guidance is present.
- Confirm no second repository-investigation model turn occurs in either fork.

#### R5: corrected evaluation behavior

- Use generated tasks containing requirement acceptance evidence, implementation-risk checks, and material open questions to confirm the corrected empirical review addresses their separation, prominence, and concision.
- Confirm a Draft plan with optional `### Additional implementation verification` remains structurally valid and requirement IDs must still appear in `### Requirement verification`.

#### R7: workflow usability

- Follow the documented commands from a clean evaluation workspace to create one neutral seed, reuse it for the comparison states, run assertions/reviews, and produce review bundles.
- Run the deterministic `test/task_guidance` suite successfully.

### Additional implementation verification

- Unit-test per-turn guidance enablement so the seed is disabled and task-creation forks are enabled.
- Unit-test source compatibility metadata, accepted reuse, and rejection or clear reporting of incompatible repository/model/prompt inputs.
- Unit-test requirement-verification extraction with H4 workstream groups followed by optional additional implementation verification.
- Unit-test the revised empirical prompt and human review template wording.
- Keep semantic concision and question prominence out of hard word-count and universal-heading assertions.

### Documentation

Update `test/task_guidance/README.md` for developers and human evaluators. It should explain:

- why investigation is guidance-neutral;
- which steps receive task guidance;
- how source-session compatibility and provenance work;
- how to reuse a source case across guidance revisions;
- which properties are mechanical assertions and which require empirical or human review.

Keep experiment-specific branch names, commit refs, run IDs, and the three-state comparison procedure in this task and its generated review artifacts, not in the general README.

### Task checklist

- [x] Create a dedicated original-guidance comparison branch from `cd1ed06b`.
- [x] Add a per-turn task-guidance control and run planning seeds with guidance disabled while retaining guidance for task-creation forks.
- [x] Record guidance-neutral seed compatibility and provenance independently from the task-creation guidance hash.
- [x] Add deterministic coverage for neutral seeds, guided forks, compatible reuse, and incompatible reuse reporting.
- [x] Commit the seed/reuse optimization separately so the same change can be applied to the original- and revised-guidance refs.
- [x] Create one neutral investigation session and preserve its content hash and request provenance.
- [x] Run the original-guidance comparison with the pre-correction evaluator.
- [x] Run the revised-guidance comparison with the same pre-correction evaluator and source investigation.
- [x] Correct the empirical rubric, manual checks, review template, and deterministic compatibility coverage for the revised guidance.
- [x] Evaluate the revised-guidance artifact with the corrected evaluator; retain any fresh model generation as supplementary evidence.
- [x] Update the evaluation README and command examples.
- [x] Run deterministic tests and generate the three review bundles.
- [x] Record the comparison outcome and human confirmation against R1–R7 before marking requirements complete.

## Implementation Notes

- Execution approved on 2026-07-23 with the recommended third-state replay and canonical Ollama/GLM comparison decisions.
- Created branch `task-guidance-original-baseline` at `cd1ed06b` before changing the evaluation harness.
- Implemented guidance-neutral source reuse in `4d4fa184` and cherry-picked the identical change to the original-guidance branch as `406d3c55`. Planning seeds pass `include_tasks: false`; guided task-creation turns pass `include_tasks: true`.
- Source reuse now requires matching repository, model/provider, prompt, non-guidance request profile, and session hash. It rejects guided or incompatible source sessions.
- Deterministic verification after the final evaluator correction: `pytest test/task_guidance -q` passed 28 tests; `ruff check test/task_guidance` passed.
- Corrected the evaluator rubric in `557347e3`. It now distinguishes requirement acceptance from implementation robustness, requires the Execution plan itself to own implementation direction, reviews top-level human priorities and concision, and treats planned verification/documentation as prohibited rather than required in omit-plan handoffs.
- Canonical neutral GLM investigation: fingerprint `228934361b81538cff610ab5399bf370a1126b934baf4aafa493f57dc3411e4d`, session SHA-256 `ceed4937645681d1e256c7e646ed4eca1f840c7a91ffdfad0d3bf64b409999cb`. Its compiled request did not contain `TASKS-v7.md`.
- Original-guidance/pre-correction state (`cd1ed06b`, evaluator `406d3c55`) passed all mechanical checks for retain-plan and omit-plan.
- Revised-guidance/pre-correction state (`182ea572`, evaluator `4d4fa184`) reused the same GLM investigation. Both generated tasks omitted requirement checkboxes; the retained plan also used a numbered task list, causing the existing mechanical checks to fail. These failures were preserved rather than rerun.
- Revised-guidance/corrected-evaluator state replayed the exact revised tasks without another model call. The corrected review identified that the retained Execution plan jumps from `Status: Draft` directly to requirement verification, relies on pre-plan decisions and its checklist for implementation direction, and contains repeated or inventory-like detail. The omit-plan review also identified relabeled implementation and verification planning.
- Supplementary ChatGPT/Codex run used its own guidance-neutral investigation and passed all mechanical checks. Its corrected empirical review independently identified the same missing implementation direction inside the retained Execution plan and relabeled verification planning in the omit-plan handoff.
- Review bundles:
  - Original guidance / old evaluator: `tmp/task-guidance-original-baseline-worktree/tmp/task-guidance-eval/review-bundles/20260723-task-guidance-original-old-evaluator`
  - Revised guidance / old evaluator: `tmp/task-guidance-eval/review-bundles/20260723-task-guidance-revised-old-evaluator`
  - Revised guidance / corrected evaluator: `tmp/task-guidance-eval/review-bundles/20260723-task-guidance-revised-corrected-evaluator`
  - Supplementary ChatGPT/Codex: `tmp/task-guidance-eval/review-bundles/20260723-task-guidance-chatgpt-revised-corrected`
- The README documents only generic guidance-neutral investigation, compatibility, reuse, and scenario-aware review behavior. Experiment-specific refs and the three-state procedure remain confined to this task and generated artifacts.

## Completion Notes

- Completed the guidance-neutral investigation and source-reuse harness, the original/revised/corrected three-state comparison, corrected scenario-aware assertions, review bundles, and supplementary ChatGPT/Codex confirmation.
- Requirement evidence is recorded in `## Implementation Notes`; deterministic verification finished with 28 passing task-guidance tests and a clean Ruff run.
- The comparison found that the revised guidance improved top-level human-review placement and reduced GLM retain-plan length, but made checkbox syntax too implicit, did not ensure the Execution plan itself contained implementation direction, and left omit-plan boundaries around implementation and verification planning ambiguous.
- The corrected evaluator detects these issues without imposing a word-count limit and treats retain-plan and omit-plan verification/documentation expectations differently.
- Human confirmation was received on 2026-07-23 with authorization to proceed to a separate follow-up revision. That revision is intentionally deferred from this completed evaluation task.