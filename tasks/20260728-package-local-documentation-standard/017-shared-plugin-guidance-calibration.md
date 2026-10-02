Parent Task: tasks/20260728-package-local-documentation-standard/000-main.md

Depends On:

- `tasks/20260728-package-local-documentation-standard/010-documentation-standard-and-agent-guidance.md`
- `tasks/20260728-package-local-documentation-standard/015-agent-evaluation-framework.md`

Specification:
`maintainer/docs/development/specifications/crystal-lattice-guidance-integration/index.md`

Requirement IDs:
`DOCREP-002`, `DOCGUIDE-003`, `DOCLOCAL-001`, `DOCVAL-010`, `AEVAL-020`

# Shared Plugin Guidance Calibration

Determine why Test 18 completes under the previous guidance but repeatedly
exhausts the 30-call budget under the rewritten guidance. Separate scenario
complexity, model/tool behavior, fixture problems, and guidance interpretation
before changing either the public guidance or the acceptance contract.

## Requirements checklist

- [x] Test 18's previous-guidance pass and both candidate failures are
  reproduced or restored with exact model, guidance, prompt, fixture, and tool
  provenance.
- [x] The investigation identifies where the candidate runs spend additional
  tool calls and why they fail to produce a complete final response.
- [x] Unsupported plugin-loading, compilation, configuration, or verification
  claims are traced to their source in the seed, fixture, inherited guidance,
  or model inference.
- [x] Diagnostic runs distinguish a hard 30-call stop from a scenario that
  would complete correctly with additional calls; a larger budget is not used
  as acceptance evidence by itself.
- [x] Any proposed scenario split preserves both package-example quality and
  shared plugin-authoring ownership rather than making the test trivially
  local.
- [x] Deterministic assertions distinguish incomplete execution, unsupported
  claims, broken indexing, and excessive file creation.
- [x] Public guidance changes are proposed only after paired evidence isolates
  a missing or misleading rule.
- [x] Model-specific variance and framework/tool defects are reported without
  being relabeled as documentation-guidance failures.

## Scope

In scope:

- Test 18 scenario, seed, fixture, assertions, and evidence presentation;
- GLM diagnostic repetitions;
- an optional focused second-model sentinel after explicit hosted authorization;
- evaluation support needed to expose stop reason and tool-call distribution;
- a proposal for public guidance only when causally justified.

Out of scope:

- Test 22 and task-requirement minimality;
- Test 13 vocabulary guidance;
- root AGENTS consolidation;
- broad plugin-documentation rewrite;
- changing tool budgets globally to manufacture a pass.

## Supporting details

Observed September 12 evidence:

| Guidance | Completed calls | Result |
|---|---:|---|
| Previous `develop` guidance | 10 | passed |
| Rewritten guidance, matrix run | 30 | incomplete final response and failed assertions |
| Rewritten guidance, fresh repeat | 30 | no final response and failed assertions |

The candidate workspace included edits to the plugin README and shared plugin
pages, but the model repeatedly used invalid shell argument shapes, created
extra page names, retained unsupported claims, and reached the stop limit.

Because the previous guidance is longer than the rewrite, instruction length
alone is not a sufficient explanation. The scenario combines source
verification, package documentation, shared documentation, index updates, and
commands. It may be too broad for one diagnostic branch, but splitting it
without preserving a cross-owner check would weaken the intended behavior.

## Implementation Notes

- September 14, 2026: Restored the September 12 sessions and ran one fresh old
  guidance sample, two immediate-pre-change samples, four normal candidate
  samples, and one 45-call diagnostic with `glm-5.3-flash:cloud`.
- The 45-call diagnostic used only 11 branch calls. Tool budget was not causal.
- The array shell allowed models to inspect mutable sibling worktrees despite
  the configured evaluation workspace. `read_file` rejected the same external
  paths. `ShellArrayTool` currently resolves workdir without enforcing
  `allowed_paths`.
- The fixture removes runtime sources that inherited plugin documentation tells
  agents to consult. This contradictory pressure caused both cautious
  fixture-only outputs and invalid external verification.
- Calibrated assertions now accept any consistent uppercase example, reject
  known unsupported fixture claims and observed external-worktree evidence,
  check Node availability claims, and enforce the documented mutation
  allowlist.
- Current normal candidate outcomes after calibration are one pass and three
  failures; the diagnostic candidate passes. Both immediate-pre-change samples
  fail. These results are not a valid guidance-regression comparison.
- Created Draft subtask 019 for shell/evaluation confinement, fixture-owned
  verification, and focused package/shared/cross-owner scenarios.
- Full findings and exact guidance hashes are recorded in
  `maintainer/docs/evaluations/documentation-guidance/20260914-guidance-followup-results.md`.

## Execution plan

Status: Approved

### 1. Reconstruct the three decisive runs

1. Restore the previous pass and two candidate failures from recorded run data.
2. Build a compact timeline of reads, writes, shell attempts, invalid tool
   calls, completed call count, changed paths, and final response state.
3. Compare seed output and branch history for unsupported assumptions already
   present before candidate guidance.

### 2. Classify the failure source

1. Determine whether the 30-call stop is caused by repeated malformed shell
   calls, patch retries, unnecessary repository exploration, excessive file
   decomposition, or unresolved verification.
2. Identify claims that cannot be verified from the bounded fixture.
3. Check whether current package/shared plugin AGENTS guidance conflicts with
   or overwhelms the two-page documentation guidance.
4. Distinguish evaluation-harness defects from model behavior.

### 3. Run bounded diagnostics

1. Repeat the unchanged candidate at the normal 30-call budget.
2. Run one diagnostic candidate with a higher budget only to observe whether
   it converges and whether the resulting content is correct.
3. If explicitly authorized, run one focused GPT sentinel with the same
   prompt, fixture, and acceptance contract.
4. Preserve all runs; do not replace a failing normal-budget result with a
   diagnostic pass.

### 4. Calibrate the scenario only if justified

1. Prefer simplifying fixture noise or assertion false negatives before
   changing behavioral pressure.
2. If the combined task is too broad, propose two focused branches plus one
   lightweight cross-owner sentinel.
3. Keep package-specific behavior in the README and genuinely shared workflow
   in the shared guide.
4. Retain objective checks for complete first use, verified claims,
   discoverability, no universalization, and documentation-only scope.

### 5. Decide whether guidance needs change

1. Make no public guidance edit if the failure is model/tool/scenario-specific.
2. If a missing rule is isolated, propose the shortest general wording and
   obtain approval before editing the public guide.
3. Rerun exact paired cases after any approved change.

### 6. Verify and report

1. Run deterministic evaluation-package tests and collection.
2. Record the final scenario shape, model outcomes, tool-budget behavior, and
   remaining variance.
3. Update requirement/task evidence without marking human interpretation
   complete automatically.

### Implementation decisions and open questions

- Approved: keep 30 calls as the acceptance budget and use a higher budget only
  for diagnosis.
- Approved: do not edit public documentation guidance during the first
  diagnostic pass.
- No hosted second-model sentinel is authorized in this execution. Propose one
  later only if GLM evidence cannot distinguish model behavior from scenario
  design.
- If the combined scenario is demonstrated to be too broad, present a focused
  package/shared split with a retained cross-owner sentinel for approval before
  changing the scenario contract.

### Documentation

- Test 18 scenario/seed documentation when its contract or diagnostics change
- Documentation-standard suite guide when a diagnostic mode is retained
- This task and affected requirements evidence
- A concise result report under the documentation-standard behavior-verification
  directory

No public documentation change is planned unless separately approved after
causal evidence.

### Task checklist

- [x] Restore and compare the three decisive runs.
- [x] Produce a tool-call and mutation timeline.
- [x] Classify unsupported claims and stop causes.
- [x] Run a normal-budget diagnostic repeat.
- [x] Run a higher-budget diagnostic without treating it as acceptance.
- [x] Decide whether a second-model sentinel is justified and authorized.
- [x] Propose scenario calibration only if evidence requires it.
- [x] Propose public guidance wording only if causally justified.
- [x] Run deterministic verification.
- [x] Record final evidence and human-review questions.

### Requirement verification

| Requirement group | Acceptance evidence |
|---|---|
| Failure classification | A compact timeline explains the extra candidate calls, stop condition, incomplete response, and unsupported claims relative to the previous pass. |
| Scenario validity | The retained or revised scenario still checks both package example quality and shared authoring ownership without embedding the expected answer in the prompt. |
| Budget integrity | Normal-budget outcomes remain authoritative; higher-budget diagnostics are labeled separately and cannot replace a normal failure. |
| Guidance causality | Any proposed public wording is tied to paired evidence that isolates a missing rule; otherwise the result is classified as model, tool, fixture, or scenario behavior. |
| Evaluation quality | Deterministic tests pass and model results retain exact profile, prompt, guidance, tool, changed-path, and stop provenance. |

### Additional implementation verification

- Confirm no diagnostic command modifies source outside isolated run
  workspaces.
- Compare repeated candidate tool-call categories and malformed-call counts.
- Verify generated pages contain no unsupported claims before accepting a
  scenario pass.

## Completion Notes

Completed September 14, 2026.

The investigation found no isolated public-guidance defect. Test 18 combined an
incomplete fixture, contradictory inherited instructions, unrestricted shell
access to mutable sibling worktrees, a broad authoring task, and assertions
that accepted unsupported claims while rejecting an equivalent example.

The assertions were calibrated without changing the prompt or model outputs,
and all sessions were reviewed through concise text transcripts. The
normal-budget candidate remains variable, but its pass/fail state now better
matches observed behavior. The substantial product/evaluation repair is
deferred to Draft subtask 019 and requires separate approval.

No public guidance was changed by this subtask. No hosted model was run.
