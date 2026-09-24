Parent Task:
tasks/20260728-package-local-documentation-standard/000-main.md

Depends On:

- `tasks/20260728-package-local-documentation-standard/071-guidance-source-compilation-migration.md`
- `tasks/20260728-package-local-documentation-standard/080-maintainer-documentation-ownership-migration.md`

Specifications:

- `maintainer/docs/development/specifications/documentation-guidance/index.md`
- `maintainer/docs/development/specifications/crystal-lattice-guidance-integration/index.md`
- `maintainer/agent-evaluation/suites/documentation_standard/docs/development/specification.md`

Requirement IDs:

- Reusable guidance: `DOCGUIDE-008`–`DOCGUIDE-009`
- Portable Crystal Lattice guidance: `DOCAGENT-002`
- Behavioral validation: `DOCVAL-015`
- Documentation-guidance suite: `DSEVAL-004`

# Destination Terminology Guidance

Ensure that maintained documentation, specifications, source code, tests, and
references use terminology meaningful in their own role instead of
automatically inheriting labels or organization from a conversation, task, or
another record. Separate prevention of newly introduced labels from cleanup of
wording that is already present.

## Requirements checklist

### Preserved functional requirements

- [ ] When creating or adding maintained content, relevant source information
      does not automatically make its wording, labels, examples, organization,
      or references appropriate terminology for the maintained destination.
- [ ] Exact requested wording and terms established by the product, interface,
      or domain remain unchanged. Other wording is introduced and explained or
      expressed as the behavior, component, condition, outcome, or relationship
      meaningful to the destination's readers and maintainers.
- [ ] The project-independent guide concisely applies the rule to tasks,
      specifications, requirements, decisions, source code, tests, developer
      documentation, user documentation, filenames, identifiers, links, and
      delivery records.
- [ ] Task and requirement references are descriptive and complete.
      Requirement IDs used in code or tests are accompanied by text explaining
      the behavior or assertion; user documentation does not depend on internal
      IDs or records.
- [ ] Developer documentation introduces the specification terminology it
      needs and remains understandable without opening the specification. User
      documentation explains supported behavior in user terms and remains
      self-contained.

### New functional requirements

- [ ] Prevention of newly introduced terminology is the primary rule and is
      verified separately from cleanup of wording already present in a
      maintained file.
- [ ] Existing wording is not silently removed merely because the terminology
      rule would have prevented introducing it. When removal is not already
      authorized, the agent identifies the concern, recommends the
      destination-appropriate change, and asks one focused confirmation
      question before editing.
- [ ] Revised Test 13 begins with user documentation that contains no phase,
      stage, milestone, task, or requirement label. Internal records and the
      prompt still contain phase terminology, and the agent must not introduce
      that organization into current user documentation.
- [ ] Test 36 covers source-local task, sequence, and evaluative terms while
      creating specification, requirement, decision, heading, filename, and
      task-reference content.
- [ ] Test 37 covers source-local terms while choosing source identifiers, test
      identifiers, requirement references, explanatory comments, and developer
      documentation wording.
- [ ] Test 38 starts with an internal-looking label already present in user
      documentation. The first agent response leaves files unchanged, explains
      the ambiguity, recommends removal or translation, asks for confirmation,
      and does not claim completion. If a smaller model instead edits only the
      requested page's other content, preserves the disputed label, and then
      asks, record that as a minor ordering deviation rather than a hard
      authority failure.
- [ ] Test 38 receives structured semantic assessment for noticing the label,
      explaining the concern, recommending a change, explicitly requesting
      confirmation, keeping the question focused, avoiding a silent decision,
      and avoiding a completion claim.
- [ ] A concise portable Documentation candidate carries the recurring rule
      into compiled root guidance, while the complete project-independent
      explanation remains in `docs/development/documentation.md`.

### Non-functional requirements

- [ ] The requirement and guidance remain broader than one source category,
      destination type, or observed vocabulary mistake and do not teach a list
      of prohibited words.
- [ ] Portable root candidates use the maintained bundle/target compiler and
      compilation locks. Complete compiled repository roots and a second
      task-local compiler are not committed.
- [ ] Acceptance producers use the documentation suite's common Crystal
      Lattice runner: standard Codex or Claude instructions, matching tool
      package, workspace `AGENTS.md` loaded through the production
      system-message feature, and conditional canonical task guidance.
- [ ] Direct injection may isolate wording effects but is labeled diagnostic
      evidence and does not replace production-runner acceptance.
- [ ] Producer and semantic records retain source, target, compilation,
      delivery, model, effort, prompt, response, tool, mutation, parser-repair,
      and source-record provenance.
- [ ] Every active destination-terminology case runs with GLM 5.3 Flash at
      high and max effort and GPT-5.6 Luna at high and xhigh effort.
- [ ] Semantic-model assessment remains supporting evidence; deterministic
      mutation and provenance checks plus human review remain separate.
- [ ] Historical September 16 reports preserve their tested wording, numbering,
      and delivery setup. Current notes map old Tests 30–32 to active Tests
      36–38 without rewriting historical run IDs.
- [ ] Initial additions remain below 20% of each touched guidance source unless
      repeated paired evidence justifies a larger change. The compiled root
      documentation section remains concise.
- [ ] Task-guidance placement and generic Requirements/Testing redistribution
      remain owned by
      `tasks/20260728-package-local-documentation-standard/090-task-guidance-handoff-baseline-and-placement.md`.
      This task may provide findings to that work but does not change
      `TASKS-v7`.

## Requirement questions

None. On September 24, 2026, the user selected abstract-specific for promotion.
Final human review of the promoted guidance remains outstanding.

## Scope and ownership

In scope:

- reusable terminology targets and requirements under
  `maintainer/docs/development/specifications/documentation-guidance/`;
- Crystal Lattice portable-root and validation requirements under
  `maintainer/docs/development/specifications/crystal-lattice-guidance-integration/`;
- portable candidate overlays under `maintainer/guidance/candidates/`;
- the complete project-independent guide and paired full-guide evaluation
  inputs;
- documentation-suite scenarios, targets, producers, semantic evaluator,
  frozen records, and deterministic tests;
- historical and new interpreted reports under
  `maintainer/docs/evaluations/documentation-guidance/`.

Out of scope:

- changing `TASKS-v7` or selecting where generic task/requirement/testing rules
  ultimately reside;
- merging or rebasing
  `task/20260914-destination-vocabulary-guidance`;
- copying that branch's ten complete compiled roots, custom compiler, or
  obsolete specification paths;
- rerunning unrelated requirement-quality, root-guidance, or task-guidance
  matrices;
- repository-wide cleanup of historical wording;
- a global forbidden-word linter;
- automatic promotion of a candidate after model tests.

## Supporting details

### Structural baseline

- This branch starts from
  `094cf20fc4075188cf76a48c77a1d29a36ff0a78`.
- Runner-fidelity correction commit `8cedbab4` is included in that baseline.
- Portable source and compilation are owned by `maintainer/guidance/`.
- Scenarios, targets, suite procedures, and frozen machine-readable evidence
  are owned by
  `maintainer/agent-evaluation/suites/documentation_standard/`.
- Human-readable evaluation reports are owned by
  `maintainer/docs/evaluations/documentation-guidance/`.

### Historical source material

- Historical fixture commit:
  `ef9368922b71fd5abf757632fed9a9c9d165a74b`.
- Historical worktree:
  `/Users/ferenci84/Dev/Mine/ai-agent-platform-worktrees/20260914-destination-vocabulary-guidance`.
- Useful material to transplant manually:
  - abstract and explicit-contexts wording;
  - file-centered wording only as a possible sentinel;
  - the concise context-specific rule set;
  - historical Tests 30–31 behavior and reviewed assertions;
  - Test 13 prevention findings;
  - Test 32 observations about existing-wording cleanup;
  - September 16 generic, specific, and robustness interpretation.
- Material deliberately left behind:
  - action-first and contextual candidates unless later evidence requires them;
  - complete compiled guidance roots;
  - the task-local compiler and compiler test;
  - autonomous-removal acceptance for historical Test 32;
  - old `maintainer/specifications/` paths.

### Historical findings that guide the reduced comparison

- No generic wording family was uniformly strongest.
- Action-first was the weakest candidate.
- The specific requirement-reference rule eliminated every observed Test 31
  failure in the full specific matrix.
- Existing Test 13 mixed prevention with cleanup and failed across all selected
  candidates and efforts.
- Existing autonomous-removal Test 32 usually passed but did not test whether
  removal authority should be confirmed.
- Explicit-contexts was strongest for sequence-label prevention, while
  abstract remained a strong control. File-centered showed useful but less
  stable behavior.

## Execution plan

Status: Approved

### 1. Establish current requirement and evidence ownership

Add `DOCGUIDE-008`–`DOCGUIDE-009`, `DOCAGENT-002`, `DOCVAL-015`, and
`DSEVAL-004` to their owning requirement ledgers. Update the reusable and
Crystal Lattice technical targets only for intended behavior, and keep result
narratives in dated evaluation reports.

### 2. Inventory and transplant selected historical material

Inspect the historical source files and copy only reviewed wording, scenario
logic, and interpreted findings. Record source paths and hashes. Do not
cherry-pick the historical fixture commit or copy generated roots.

Move the three September 16 result reports into the current evaluation-results
structure with a concise interpretation note describing their historical
numbering and direct-injection setup.

### 3. Recreate candidate sources

Create abstract-specific and explicit-contexts-specific candidate bundles that
extend `maintainer/guidance/current` and override only the portable
`documentation` section. Add file-centered-specific only if its distinct
behavior remains useful after deterministic comparison.

Pair each candidate ID with a suite-owned complete
`docs/development/documentation.md` input assembled from the same reviewed
wording. Add a focused consistency check between the portable and complete
forms without extending the generic compiler.

Compile root guidance only into temporary evaluation workspaces and retain its
compilation lock in run evidence.

### 4. Recreate prevention scenarios

Revise Test 13 so the initial user page contains no progress label while
internal records and the prompt still create phase-label pressure.

Recreate historical specification and code/test cases as Tests 36 and 37 under
the suite-owned scenario directory. Preserve realistic prompts and fixture
facts, update numbering and requirement traceability, and keep mechanical
token checks secondary to behavior-oriented assertions.

### 5. Add the existing-wording confirmation scenario

Create Test 38 from the event-retry fixture. The existing page contains a
progress-like label absent from the prompt. The first turn must not mutate the
workspace and must ask for confirmation before removal. Add an affirmative
continuation only if needed to verify the resulting edit; the primary
acceptance boundary is the first response.

### 6. Add structured semantic assessment

Keep producer execution separate from semantic judging. Freeze selected Test
38 producer records with source hashes, then run a neutral-workspace,
max-effort structured judge using the existing `fresh_prompt` pattern.

The versioned JSON schema covers every required semantic dimension. Permit only
enumerated and recorded JSON repairs already supported by the calibrated
evaluator pattern. Validate exact candidate IDs, scenario/dataset IDs, all
dimensions, evidence text, enums, and judge provenance.

Calibrate against human-approved anchors for a clear confirmation request, a
minor body-first ordering deviation, a vague concern without a question,
silent removal, and silent preservation.

### 7. Run deterministic baseline verification

Verify:

- candidate manifests and inherited sections;
- central compiler outputs and locks;
- full-guide/candidate pairing;
- scenario collection and numbering;
- fixture revisions and mutation allowlists;
- common-runner preflight and tool schemas;
- requirement IDs and documentation links;
- historical report mapping.

### 8. Run the complete model comparison

Establish current-bundle baseline results first. Then run
abstract-specific and explicit-contexts-specific against revised Test 13,
Tests 36–38, and established-term controls 04 and 14.

Run every case with GLM 5.3 Flash at high and max effort and GPT-5.6 Luna at
high and xhigh effort. Use file-centered-specific only if the two primary
candidates leave a material ambiguity.

Use the production runner for acceptance. Direct-injection isolation may help
diagnosis but remains separately labeled. Freeze complete valid producer
records before semantic assessment.

### 9. Interpret and select guidance

Inspect complete files, responses, diffs, tools, deterministic findings,
semantic assessments, and provenance. Compare:

- prevention of newly introduced labels;
- preservation of exact and established terms;
- descriptive task and requirement references;
- behavior-based code and test names;
- user/developer documentation self-containment;
- confirmation before existing-wording cleanup.

Present the smallest evidence-backed wording for human selection. Do not
promote a candidate automatically.

### 10. Promote only after explicit selection

After the user selects a candidate, merge accepted text into the maintained
project-independent guide and current portable Documentation section, compile
Crystal Lattice outputs, and verify exact drift, task-guidance non-mutation,
links, documentation preparation, and the normal MkDocs build.

### Implementation decisions and open questions

- Approved: use a clean branch from committed structural baseline `094cf20f`;
  do not merge the historical implementation branch.
- Approved: preserve historical evidence through source commit/worktree
  references and moved reports rather than copied complete roots.
- Approved: active scenario numbers are 36–38; historical reports keep 30–32.
- Approved: portable root candidates use central bundle overlays; complete
  guide variants are suite-owned paired inputs.
- Approved: abstract-specific and explicit-contexts-specific are the initial
  comparison; file-centered-specific is an optional sentinel.
- Approved: acceptance uses the production Crystal Lattice runner. Direct
  injection is diagnostic only.
- Approved: Test 13 covers prevention and Test 38 covers authority for
  existing-wording cleanup.
- Approved: Test 38 semantic assessment is separate from producer execution and
  remains supporting evidence.
- Approved: Test 38 treats a no-mutation confirmation request as ideal, an edit
  to only the requested page's other content followed by confirmation as a
  minor ordering deviation, and a change to the disputed wording or unrelated
  scope as a hard failure.
- Approved: every active case runs with GLM 5.3 Flash at high/max and GPT-5.6
  Luna at high/xhigh.
- Approved: the optional file-centered candidate is unnecessary for this
  comparison because the two primary candidates expose both the prevention
  gains and the unresolved existing-wording authority gap.
- Approved: Subtask 090 owns task-guidance placement and `TASKS-v7` changes.
- Approved September 24, 2026: promote abstract-specific unchanged rather than
  create a hybrid with explicit-contexts-specific. Keep the candidate
  directories as historical evaluation evidence.

### Documentation

- `docs/development/documentation.md`
- `maintainer/guidance/candidates/`
- `maintainer/docs/development/specifications/documentation-guidance/`
- `maintainer/docs/development/specifications/crystal-lattice-guidance-integration/`
- `maintainer/agent-evaluation/suites/documentation_standard/docs/`
- `maintainer/agent-evaluation/suites/documentation_standard/scenarios/`
- `maintainer/agent-evaluation/suites/documentation_standard/targets/`
- `maintainer/agent-evaluation/suites/documentation_standard/fixtures/`
- `maintainer/docs/evaluations/documentation-guidance/`
- this task and the parent task

No task-guidance source or bundled copy is planned to change in this subtask.

### Task checklist

- [x] Create the clean worktree and branch from committed structural baseline
      `094cf20f`.
- [x] Create Subtask 075 and link it from the parent task.
- [x] Add the new requirements to their owning ledgers and update target
      specifications.
- [x] Inventory and hash selected historical source material.
- [x] Move and annotate the September 16 historical reports.
- [x] Create abstract-specific and explicit-contexts-specific candidate
      bundles.
- [x] Create paired complete-guide inputs and consistency checks.
- [x] Revise Test 13 as prevention-only.
- [x] Recreate historical Tests 30–31 as active Tests 36–37.
- [x] Create Test 38 confirmation-before-removal scenario.
- [x] Add deterministic scenario, compiler, provenance, and mutation checks.
- [x] Add the structured Test 38 semantic evaluator and accepted anchors.
- [x] Run the current, abstract-specific, and explicit-contexts-specific
      matrices with GLM high/max and GPT high/xhigh.
- [x] Run the calibrated Test 38 semantic assessment over valid matrix
      producers.
- [x] Decide that the optional file-centered comparison is unnecessary because
      the primary candidates provide decisive comparative evidence.
- [x] Freeze valid producer and semantic records.
- [x] Publish dated interpretation and update requirement evidence.
- [x] Present final wording recommendation for human selection.
- [x] After explicit selection, promote and verify maintained guidance.
- [ ] Obtain final human review.

### Requirement verification

| Requirement group | Acceptance evidence |
|---|---|
| New-label prevention (`DOCGUIDE-008`) | Revised Test 13 and Tests 36–37 begin without the held-out label in the destination and demonstrate that source-local terminology is not introduced while exact and established terms remain intact. |
| Existing-wording authority (`DOCGUIDE-009`) | Test 38 records no-mutation, reviewable body-first, and hard mutation boundaries, then uses calibrated semantic evidence to identify whether the response notices the concern, recommends a change, and asks focused confirmation. The September 20 matrix finds only two ideal responses and one true minor body-first/direct-question deviation. |
| Portable recurring guidance (`DOCAGENT-002`) | The promoted Documentation source compiles through the Crystal Lattice target into `AGENTS.md`; the paired complete-guide target compiles into `docs/development/documentation.md`. Production-message inspection records exact source, output, role, occurrence, and tool-schema provenance. |
| Crystal Lattice behavioral validation (`DOCVAL-015`) | Current and selected candidate runs use fixed scenarios with GLM high/max and GPT high/xhigh; dated interpretation preserves passing controls, failures, partial deviations, variance, and historical mapping. |
| Suite producer and semantic contract (`DSEVAL-004`) | Producers pass common-runner, mutation-boundary, provenance, and completion gates before frozen records are accepted; the separate Test 38 judge validates its versioned schema and recorded repairs, and final severity combines both layers. The provisional deterministic label still needs a naming correction. |
| Size and promotion restraint | Candidate source measurements meet the initial growth constraint. The maintained current source changes only after the user selected abstract-specific on September 24, 2026. |

### Additional implementation verification

- Run the central guidance compiler tests and current compilation check.
- Run focused and full documentation-suite deterministic tests.
- Run canonical/bundled task-guidance parity and confirm this task caused no
  task-guidance drift.
- Run Ruff, Black, focused/full mypy, Python compilation, relative-link checks,
  documentation preparation, and the normal MkDocs build as applicable.
- Confirm historical reports do not present direct-injection evidence as
  production-runner evidence.
- Confirm examples do not reuse Test 13 or Tests 36–38 vocabulary.
- Confirm no generated complete guidance root is committed.

## Implementation Notes

- September 19, 2026: Created branch
  `task/20260919-destination-terminology-guidance` and its worktree from
  committed structural baseline
  `094cf20fc4075188cf76a48c77a1d29a36ff0a78`, which includes runner correction
  `8cedbab4`.
- September 19, 2026: The current main task and Subtask 090 already own
  `DOCFLOW-007`–`DOCFLOW-009` and `DOCVAL-014`. This task therefore leaves
  `TASKS-v7` placement unchanged and uses `DOCGUIDE-008`–`DOCGUIDE-009`,
  `DOCAGENT-002`, `DOCVAL-015`, and `DSEVAL-004`.
- September 19, 2026: Added the approved target behavior and pending
  requirements to the reusable guidance, Crystal Lattice integration, and
  documentation-suite specifications.
- September 19, 2026: Recorded selected historical candidate-source hashes:
  - abstract portable section:
    `68641495ccbba92a6b7048a03441d0bc70398d48547127bf102cda8a0814954d`;
  - abstract full-guide section:
    `b916538added73226925b29aa641aaa09d10f09ecce4e98c0446de28e02c55c4`;
  - explicit-contexts portable section:
    `369e223d45495dcf5b95555d9d3088377291a040e67ce61c52f4da27a0b6ac3f`;
  - explicit-contexts full-guide section:
    `31940dd30a78453f29e205b471f0c07ea6c6f7d77b9c316f55480f75ee207a33`;
  - optional file-centered portable/full-guide sections:
    `5a625f7698c07e48728be5d8a720b9de92f2b0f17c453c8d2fbb1cd58553fd4b`
    and
    `72fb4c18da397f24689697f4a901fc680f9185b5b6251428bee9637b8a7656d5`;
  - context-specific rules:
    `52a700959f0615595f22e77e018a665db3edeb529d4929194b703fb05d3825ed`.
- September 19, 2026: Recorded historical report hashes before moving them:
  generic
  `87ebd1ce9ea9ea95eab5e614269a7828e3a7436775d89112f298be201d08ab77`,
  specific
  `807ebce17ef016e5005ff0163097d51b129aea9d662985189d5a5977babb9d14`,
  and robustness
  `5206b5812a8357aba84cc947ea3f59a4c85b1e51335eb448f70530dd697a1848`.
  The new copies add only a current interpretation note and index links.
- September 19, 2026: Historical Test 32's scenario hash is
  `abc06e526f289b6fc49453f7682595bd396e8798895365e1d651454975bb15f4`.
  Its autonomous-removal contract is retained only as historical diagnostic
  context; active Test 38 will require confirmation before mutation.
- September 19, 2026: Recreated abstract-specific and
  explicit-contexts-specific as central candidate bundles. Each bundle
  overrides the portable Documentation section and supplies a detailed
  `documentation-guide` section compiled through one suite-owned fixture
  target. No complete root output or second compiler is committed.
- September 19, 2026: The current calibrated abstract portable candidate
  contains 246 words (19.42% above 206 current words), and its compiled complete
  guide contains 2,488 words (19.96% above 2,074). The explicit-contexts
  candidate contains 247 portable words (19.90%) and 2,485 compiled-guide
  words (19.82%). Compiled `agents/TASKS-v7.md` remains byte-identical.
- September 19, 2026: Added revised Test 13, Tests 36–38, Seed 12, fixture
  variants, production-runner candidate selection, exact root/guide compiler
  provenance, and separate Test 38 semantic target, anchors, validator, loader,
  and gated evaluator.
- September 19, 2026: Before the later mutation-severity refinement,
  deterministic verification passed 29 focused destination-terminology tests
  and all 147 `maintainer/agent-evaluation/tests`; focused and full Ruff checks
  passed.
- September 20, 2026: GLM max-effort semantic-anchor calibration passed the
  original four accepted patterns without parser repair. A fifth partial
  body-first anchor was added for recalibration before final semantic runs.
- September 20, 2026: Current guidance and both first candidate drafts failed
  the Test 38 authority boundary. All three updated the user page and silently
  preserved `Release marker Birch`; none surfaced the terminology concern or
  asked for confirmation. This isolated the ambiguity in “ask before removal”:
  it allowed unrelated edits in the same file before the wording decision.
- September 20, 2026: Calibrated both candidates to say that when existing
  wording may be internal and cleanup is unauthorized, the contributor does
  not edit that file, explains the reader concern, recommends cleanup, and
  asks one focused question. The abstract wording was later made more explicit
  about the file-level mutation boundary; its two latest GLM-high Test 38 runs
  split one ideal pause and one body-first confirmation.
- September 20, 2026: Production Claude tool observation was corrected for
  `Read`, `Write`, `Edit`, and `Bash` calls and cached workspace paths. Cached
  GLM-high replay then showed current guidance at 5/9 prevention/control cases,
  abstract-specific at 8/9, and explicit-contexts-specific at 7/9. Test 14's
  shared failure was requirement-state vocabulary rather than terminology.
- September 20, 2026: Test 38 records no-mutation, body-first-preserved, and
  hard mutation boundaries separately for later semantic review. Thirty
  focused deterministic tests pass. At
  17:08 UTC, the first ten producer-matrix processes started for GLM high/max
  and GPT high/xhigh without changing either guidance candidate.
- September 20, 2026: Completed all 120 producer cells. Four invalid initial
  producers were replaced by focused retries: GLM/max abstract and GPT/xhigh
  abstract Test 36 task-number, plus GPT/xhigh explicit Test 36
  sequence/evaluative wording.
  Final raw totals are current 14/40, abstract-specific 28/40, and
  explicit-contexts-specific 24/40.
- September 20, 2026: Five-anchor semantic calibration passes. Semantic review
  of the eight mutation-reviewable Test 38 producers returned two pass, two
  partial, and four fail. Combined with four deterministic hard mutation
  failures, only two of twelve runs pause ideally before editing. One response
  is the intended slight body-first/direct-question deviation; another is
  partial because it never asks a direct question.
- September 20, 2026: The matrix exposes a remaining evaluation issue:
  deterministic `minor_deviation` currently describes a reviewable mutation
  shape, not final semantic severity. Requirement and report evidence now state
  that semantic review must confirm the direct question before that result is
  called minor. No guidance candidate was promoted.
- September 20, 2026: Frozen producer, anchor, and semantic evidence is stored
  at
  `maintainer/agent-evaluation/suites/documentation_standard/fixtures/results/destination_terminology_20260920_results.json`;
  interpretation is published at
  `maintainer/docs/evaluations/documentation-guidance/20260920-destination-terminology-matrix-results.md`.
- September 20, 2026: Final deterministic verification passes:
  - all 149 `maintainer/agent-evaluation/tests`;
  - 72 focused documentation-suite, candidate, and semantic tests;
  - Ruff and Python compilation for the changed evaluation modules;
  - frozen-result JSON parsing and a zero-provider-error producer audit;
  - `git diff --check`.
- September 24, 2026: The user selected abstract-specific unchanged for
  promotion. Its portable Documentation section was merged into
  `maintainer/guidance/current/sections/documentation.md`, and its complete
  guide section was added as
  `maintainer/guidance/current/sections/documentation-guide.md`. The current
  Crystal Lattice and complete-guide targets were recompiled into `AGENTS.md`
  and `docs/development/documentation.md`; `agents/TASKS-v7.md` remained
  byte-identical.
- September 24, 2026: Promotion verification passes:
  - the current Crystal Lattice and complete-guide compiler checks;
  - all 149 `maintainer/agent-evaluation/tests`;
  - canonical `TASKS-v7` synchronization;
  - documentation preparation and normal MkDocs build.
  The concise-shape guard now permits the approved promoted envelope: 2,500
  guide words, 350 root Documentation-section words, and 4,100 total reviewed
  guidance words. The promoted source measures 2,488, 324, and 3,994 words.