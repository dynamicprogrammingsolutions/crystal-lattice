Parent Task: tasks/20260728-package-local-documentation-standard/000-main.md

Depends On:

- `tasks/20260728-package-local-documentation-standard/010-documentation-standard-and-agent-guidance.md`
- `tasks/20260728-package-local-documentation-standard/015-agent-evaluation-framework.md`

Specification:
`maintainer/specifications/documentation-and-specification-standard/index.md`

Requirement IDs:
`DOCGUIDE-008`–`DOCGUIDE-009`, `DOCAGENT-002`, `DOCFLOW-007`,
`DOCVAL-014`, `DSEVAL-004`

# Source Wording and Destination Terminology

Ensure that maintained files use terminology and references appropriate to
their own role and available context instead of treating wording from a
conversation or another source as an automatic name. Add the smallest useful
project-independent guidance, concise recurring agent and task instructions,
and behavioral evidence across the important destination boundaries.

## Requirements checklist

### Preserved functional requirements

- [ ] When creating or adding maintained content, the project-independent
      documentation guide prevents wording, labels, examples, or organization
      from a conversation, task, specification, or other source from becoming
      new destination terminology merely because it was available to the
      author.
- [ ] Terms are reused when exact wording is required, already established for
      the destination, or introduced and explained there; otherwise the
      destination names the underlying behavior, component, condition, or
      outcome in terms available to its reader or maintainer.
- [ ] The project-independent guide concisely applies the general rule to task
      files, specifications, requirements, decisions, source code, tests,
      developer documentation, user documentation, filenames, identifiers,
      links, and commit or pull-request titles.
- [ ] Task files may retain useful conversational wording when they define it
      and remain understandable without the conversation; cross-task
      references use descriptive full paths instead of unexplained ordinal
      shorthand.
- [ ] Specifications, requirements, and decisions use descriptive references
      to each other and to tasks without turning source-local labels into
      normative domain terminology or copying canonical text into competing
      definitions.
- [ ] Source and test names describe the behavior they implement or verify.
      Requirement IDs may provide traceability in acceptance or contract tests
      and explanatory code comments when the surrounding text states the
      relevant behavior.
- [ ] Developer documentation may use specification terminology and link
      specifications or requirements, but introduces the terms it needs and
      explains current implementation without requiring the linked source.
- [ ] User documentation uses terms meaningful to product users, explains
      supported behavior within user documentation or public reference, and
      does not depend on internal task, requirement, decision, or development
      context. A developer-documentation link remains an optional labeled
      reference.
- [ ] The portable Documentation section compiles a concise version of the
      general rule into root `AGENTS.md`, covering maintained prose, filenames,
      identifiers, tests, comments, and commit or pull-request titles. Source,
      compilation, runtime delivery, and observed use remain separate
      provenance.
- [ ] Canonical and bundled task guidance contain the task-file-specific rule
      through the synchronization boundary owned by
      `tasks/20260728-package-local-documentation-standard/068-task-guidance-specification-alignment.md`.

### New or changed functional requirements

- [ ] Prevention of new terminology transfer is the primary rule and is
      verified separately from cleanup of wording already present in a
      maintained file.
- [ ] Existing wording is not silently removed merely because the terminology
      rule would have prevented introducing it. When a request touches content
      containing a potentially internal or progress label but does not
      authorize its removal, the agent identifies the concern, recommends the
      destination-appropriate change, and asks one focused confirmation
      question before editing.
- [ ] Test 13 continues to exercise partial major-change documentation, but
      its initial user documentation contains no phase, stage, milestone, or
      other progress label. The prompt supplies internal phase wording, and the
      acceptance boundary verifies that the agent does not introduce that
      organization into current user documentation.
- [ ] A separate existing-wording scenario begins with an internal-looking
      label already present in user documentation. The first agent response
      leaves files unchanged, explains the ambiguity, recommends whether to
      remove or translate the label, and asks the user to confirm the removal.
- [ ] The confirmation scenario has a structured model-assisted semantic
      assertion for notice, recommendation, explicit confirmation, focused
      question quality, no completion claim, and no silent decision. Model
      assessment remains supporting evidence and does not replace deterministic
      mutation/provenance checks or human review.

### Non-functional requirements

- [ ] The requirement, public rule, and recurring agent instruction remain
      broader than any one source category, destination type, or observed
      vocabulary mistake and do not teach a list of prohibited words.
- [ ] Before public or recurring guidance changes, preserved behavioral runs
      sample varied source terms, destination boundaries, supported models,
      and reasoning efforts and retain complete files, diffs, responses, tool
      behavior, and provenance for inspection.
- [ ] Initial behavioral assessment uses semantic and human inspection before
      finalizing deterministic assertions. Mechanical token or path checks are
      secondary regression backstops.
- [ ] Existing seeds and scenarios are reused only when their established
      facts and mutation boundaries exercise the new concern with minimal
      change; a new seed is added only when reuse would make the situation
      ambiguous or unrealistic.
- [ ] Test 13 retains its user-documentation and partial-state boundary while
      removing pre-existing phase labels from the user-page fixture; historical
      Test 13 results remain evidence for the older mixed setup but are not
      acceptance evidence for the revised prevention-only scenario.
- [ ] Active terminology scenarios, requirement IDs, and result references do
      not collide with the integrated requirement-quality work. Historical run
      IDs and dated results retain their original numbers with an explicit
      mapping to the renumbered active scenarios.
- [ ] Semantic assertions use a versioned hidden target, structured JSON
      schema, deterministic validation, source-hashed producer records,
      narrowly documented parser repairs, separate judge provenance, and
      frozen results suitable for later reproduction.
- [ ] Implementation starts from a clean branch based on the committed
      structural tip of
      `/Users/ferenci84/Dev/Mine/ai-agent-platform-worktrees/20260728-documentation-guide-rewrite`
      and selectively transplants reviewed terminology material without
      merging this old branch, copying its complete compiled roots, or
      rerunning unrelated requirement-quality and root-guidance matrices.
- [ ] Initial additions to each maintained guidance file remain below 20% of
      that file's integrated pre-change size. Root recurring documentation
      guidance also remains within its approved approximate 200–300-word
      range.
- [ ] Guidance is expanded beyond the initial concise candidate only when
      paired model evidence shows that a shorter general rule and compact
      destination applications remain materially misinterpreted.
- [ ] The Crystal Lattice conventions page remains limited to repository paths,
      local exceptions, publication, generation, and migration;
      project-independent destination terminology rules are not placed there.

## Requirement questions

None. A later observation that would change the required destination
boundaries, recurring instruction surfaces, or 20% initial-growth constraint
requires user approval before changing this checklist.

## Approved scope decisions

- The rule applies to all relevant source context and maintained destinations,
  not only common task or sequencing terminology.
- The project-independent guide owns both the general rule and concise
  applications to the file roles it already defines.
- The Crystal Lattice conventions remain limited to local paths and
  repository-specific exceptions.
- Behavioral observation across varied terms, destinations, models, and
  reasoning efforts precedes guidance changes and final assertion design.
- Initial additions remain below 20% per guidance file; more text requires
  paired evidence that the concise candidate remains insufficient.

## Proposed revised scope decisions

These decisions reflect the September 17–18, 2026 direction and become approved
only after the revised execution plan is accepted:

- New-label prevention and existing-label cleanup are separate behavior and
  test boundaries.
- Test 13 becomes prevention-only by removing pre-existing phase labels from
  its initial user documentation.
- Existing ambiguous terminology is not silently removed. The agent recommends
  the cleanup and asks confirmation when the request has not authorized it.
- The existing-wording confirmation response receives separate structured
  semantic assessment using the calibrated producer/dataset/judge pattern from
  the documentation-guide-rewrite worktree.
- A new branch starts from the committed documentation-guide-rewrite structural
  tip. Only reviewed terminology requirements, candidate wording, scenario
  behavior, and historical interpretation are transplanted; this old branch
  and its obsolete compiler/output layout are not merged.
- The active terminology scenarios move to Tests 36–38, and this task's
  validation requirements use `DOCVAL-014` and `DSEVAL-004`.

## Scope

In scope:

- the reusable terminology target under
  `maintainer/docs/development/specifications/documentation-guidance/`;
- the Crystal Lattice compilation, task-guidance, and validation refinement
  under
  `maintainer/docs/development/specifications/crystal-lattice-guidance-integration/`;
- the documentation-suite producer and semantic-evaluation contract under
  `maintainer/agent-evaluation/suites/documentation_standard/docs/development/`;
- `docs/development/documentation.md`;
- portable Documentation candidate sections under
  `maintainer/guidance/candidates/`, compiled into temporary root
  `AGENTS.md` files through the central compiler;
- the task-specific addition to canonical and bundled `TASKS-v7` through
  `tasks/20260728-package-local-documentation-standard/068-task-guidance-specification-alignment.md`;
- suite-owned scenarios, semantic targets, frozen records, and narrowly
  justified test consumers under
  `maintainer/agent-evaluation/suites/documentation_standard/`;
- dated interpretation under
  `maintainer/docs/evaluations/documentation-guidance/`;
- deterministic suite support needed for provenance, model/reasoning
  selection, and secondary assertions;
- requirement and task evidence for the new Subtask 075.

Out of scope:

- substantive additions to
  `docs/development/crystal-lattice-documentation.md`;
- a repository-wide rename or cleanup of historical wording;
- a global forbidden-word linter;
- changes to product behavior or package APIs;
- rewriting unrelated behavioral scenarios;
- replacing semantic and human review with token matching;
- copying the old branch's complete compiled guidance roots or task-local
  compiler into the new structure;
- merging or rebasing this old implementation branch into the structural
  branch;
- branching from uncommitted structural changes;
- resolving task-guidance source synchronization independently from subtask
  `tasks/20260728-package-local-documentation-standard/068-task-guidance-specification-alignment.md`.

## Supporting details

### Existing guidance and evidence

The current project-independent guide already says to introduce terms, prefer
product/package/interface vocabulary, and write for the destination reader.
It does not explicitly distinguish the relevance of source information from
the suitability of its wording or organization in a destination.

Historical Test 13 demonstrates an important mixed failure mode: a model can
preserve internal organization already present in user documentation while
also receiving new phase wording from the prompt. That evidence remains useful
for diagnosis, but it cannot distinguish failure to prevent a new label from
failure to clean up an existing one. Revised Test 13 isolates prevention and a
separate confirmation scenario owns existing-wording cleanup.

The existing suite also provides two promising reusable fixture families:

- Seed 05 and Tests 09/26 create specifications, requirements, decisions,
  filenames, and headings from an approved task.
- Seed 06/Test 10 and Seed 07/Test 11 mutate source and tests, with Seed 06
  also containing requirements and current documentation.

Tests 04 and 14 use `portable` as an established contract concept, so they
cannot by themselves prove that an evaluative use of the same word was
translated correctly. Their prior outputs may still reveal naming behavior,
but adding a new assertion to them is justified only when it does not confuse
an established domain term with source-local wording.

### September 18 structural findings

- `maintainer/specifications/` has been removed. Reusable guidance and Crystal
  Lattice integration now have separate specifications under
  `maintainer/docs/development/specifications/`.
- Human-readable evaluation reports now belong under
  `maintainer/docs/evaluations/documentation-guidance/`.
- Documentation-suite scenarios, targets, operational documentation, and
  frozen machine-readable evidence are owned by
  `maintainer/agent-evaluation/suites/documentation_standard/`.
- Portable root and task guidance now have maintained source under
  `maintainer/guidance/`, with bundle overlays, project-owned targets,
  deterministic compilation locks, and manual promotion.
- The suite's common runner now requires the normal Crystal Lattice
  system-message feature, the selected Codex or Claude instruction template,
  matching tool package, workspace AGENTS loading, and conditional canonical
  task guidance. Direct injection is a distinct diagnostic setup.
- The new structure already owns Tests 30–35, `DOCGUIDE-007`,
  `DOCVAL-011`–`DOCVAL-013`, `DOCAGENT-003`–`DOCAGENT-004`, and Subtask 067.
- The other worktree's committed structural tip is `02f557b5`, but it
  currently has uncommitted runner-fidelity corrections across evaluator,
  suite-documentation, result, and task files. A new branch must wait for a
  committed clean base rather than using that dirty state.
- Rebasing this branch would conflict across deleted specification paths,
  moved scenario/result paths, the central compiler, requirement IDs, task
  numbering, and evaluator delivery semantics. A selective clean transplant
  has a smaller modification surface and clearer provenance.

### Migration options considered

- **Migrate the existing branch:** not recommended. A rebase or merge would
  spend most of the work resolving obsolete generated roots, a duplicate
  compiler, deleted specification paths, moved scenario/report paths, and
  conflicting IDs before the terminology behavior could be reviewed.
- **Start immediately from committed tip `02f557b5`:** possible but not
  recommended while the structural worktree has uncommitted runner-fidelity
  corrections. It would require another reconciliation before meaningful
  producer evidence could run.
- **Start a clean branch from the next committed structural tip and transplant
  selected material:** recommended. It preserves the new ownership and runner
  contracts, keeps historical evidence reachable in the old branch, and
  carries only material that contributes to final behavior or interpretation.

### Initial guidance candidates

These candidates are evaluated in order after the observation matrix. Exact
editing may shorten them further while preserving the meaning and size limits.

#### Candidate A: general rule and recurring agent instruction

The project-independent guide initially adds only four general rules:

1. A request or source can define an intended outcome without defining the
   names used in another maintained destination.
2. Wording, labels, examples, and organization from conversations and other
   records are source context.
3. Exact wording is retained when required or established by the product,
   interface, or domain—not merely because it already appears in a file.
4. Other terminology is introduced and explained or translated into the
   behavior, component, condition, outcome, or relationship meaningful to the
   destination.

Root `AGENTS.md` initially uses the earlier concrete wording:

> Treat wording from prompts, conversations, tasks, plans, and review comments
> as source context, not automatically as terminology for maintained output.
> Preserve the intended behavior, but unless exact wording is explicitly
> required or the term is an established contract, name files, headings,
> identifiers, tests, comments, documentation, specifications, user-visible
> text, and commit or pull-request titles using concepts defined by the
> destination domain. Translate quality directions and conversation-local
> shorthand into concrete behavior.

This replaces less precise sentences inside the consolidated documentation
section. It does not create another policy block and does not cause that
section to exceed 300 words.

Candidate A deliberately omits file-role examples and the task-guidance
addition. Its run should show which boundaries the general rule can handle
without further explanation.

#### Candidate B: concise file-role applications

After Candidate A is evaluated, add a short application section immediately
after the four general rules:

- A different example label demonstrates that task-local wording remains
  local; elsewhere use the task's descriptive title and full path.
- Specifications, requirements, and decisions use domain terms. Link IDs with
  descriptions and paths; source descriptions become requirements only when
  their observable meaning is required.
- Source and tests name behavior; a requirement ID is accompanied by an
  explanation of the invariant or assertion.
- Developer documentation introduces needed specification terms and explains
  current implementation without requiring linked internal records.
- A different example grouping demonstrates that user documentation translates
  internal labels into delivered capabilities and omits internal future work.
- Headings, filenames, identifiers, and commit or pull-request titles name
  destination behavior instead of unexplained source labels.

The corresponding task-guidance candidate is:

> A task file must stand alone without the conversation. It may retain wording
> introduced by the user when preserving that wording matters, but define it
> and distinguish it from the stable behavior or component name. Use
> descriptive task content and full relative paths for cross-task references.

The task-guidance alignment work may shorten this further while preserving the
rule and canonical-to-bundled synchronization.

### Proposed behavioral scenarios

The observation phase may reduce or combine these scenarios, but the initial
coverage target is:

The initial held-out prompt variants include:

- `Task 010` as conversation-only ordinal shorthand;
- `Stage A` as a source-local sequence label;
- `portable` and `useful` as evaluative descriptions when the fixture does not
  establish them as functional requirements or domain terms.

These words appear in scenario prompts, fixtures, assertions, and results, not
in agent-visible candidate guidance. Each variant explicitly establishes
whether the term is shorthand, an evaluation, an exact requested name, or an
existing contract term so semantic review does not guess its intended role.

1. **Retained Test 13 — current user documentation**
   - Keep its prompt, fixture, and expected behavior unchanged.
   - Run the integrated baseline with both the established GLM and GPT
     profiles at supported low, high, and max reasoning efforts.
   - Inspect whether current user documentation inherits any unexplained
     source terminology or organization, including synonyms not present in
     guidance.
2. **Proposed Test 30 — terminology across specification records**
   - Reuse Seed 05 with small branch variants.
   - Keep offline synchronization as the established capability.
   - Vary source-local ordinal shorthand, a lettered sequence label, and
     evaluative descriptions in the conversation or approved task.
   - Inspect the task, specification directory and filenames, headings,
     requirements, decisions, links, and response.
   - Require retained task wording to be defined; other destinations use
     capability terms and descriptive complete references.
3. **Proposed Test 31 — source and test naming**
   - Reuse Seed 06 and add only a branch-local current developer page when
     needed, preserving its path-policy task, requirement, source, tests, and
     user documentation.
   - Vary the same source-term classes independently rather than combining
     every phrase in one prompt.
   - Inspect source filenames, public and private function names, test
     filenames, test names, comments, requirement evidence, developer
     documentation, and response.
   - Require behavior-based names and explanatory requirement references.
4. **Exact or established terminology control**
   - Use one variant in which the user explicitly requires a name, or the
     fixture already establishes the term as part of its contract.
   - Reuse Tests 04 or 14 as evidence that `portable` remains valid when it
     actually names the shared contract, provided their other scenario
     assertions remain unchanged.
   - Require that term to be preserved, demonstrating that the rule is
     context-sensitive rather than a generic renaming instruction.

Tests 04, 10, 11, 14, 22, and 26 are inspected during baseline review. They
receive new assertions only if an existing prompt already creates the same
pressure and the output demonstrates a relevant mistake; their established
purpose is not broadened merely to avoid a new scenario number.

Expected candidate discrimination:

- Candidate A should be sufficient for direct naming choices: specification
  headings and paths, source functions, test files, test names, comments, and
  delivery records should not adopt source-local labels or evaluative
  descriptions as unexplained names.
- Candidate B should add the context needed for task-local definitions,
  descriptive task/requirement/decision references, developer-documentation
  independence, user-documentation independence, and the retained Test 13
  case.
- If Candidate A already passes a harder case, retain that result as evidence
  that the general rule was sufficient; Candidate B must not make it regress.

### Concurrent documentation follow-up

The parallel branch `task/20260914-guidance-follow-up-rewrites` currently
contains committed root-guidance consolidation, revised behavioral
calibration, and task-guidance subtask updates. Before execution, rebase this
subtask onto the integrated `develop` result and reassess exact file sizes,
Test 13 behavior, guidance hashes, and the canonical task-guidance mechanism.
Do not overwrite or independently reproduce that branch's work.

## Implementation Notes

- September 14, 2026: The user approved the Draft plan and authorized
  implementation through the first baseline test result.
- Rebased this worktree from `develop` revision `65beac9d` onto the complete
  committed guidance follow-up at `cebd8727`. The autostash reapplied the
  approved task and specification changes without conflicts.
- No public guide, root agent instruction, task guidance, behavioral scenario,
  fixture, or executable assertion has changed in this subtask.
- Recorded the integrated pre-change sources:
  - root `AGENTS.md`: SHA-256
    `cca0fa6571724eb33a45c5cc73c22b39e9fc949a0d888b78108de68b4eeb67fd`;
  - root documentation policy block: 289 words, SHA-256
    `8784760a550a4338a4a188fa077aeb35ac6608cbe3091ec6b38a00654d1142bc`;
  - `docs/development/index.md`: 118 words, SHA-256
    `360499e5cf5aa476c9a08d16c90a29f634ad4b77fb0587d9a1bb867bc62a2a75`;
  - `docs/development/documentation.md`: 2,055 words, SHA-256
    `1616fe8d5d34684a76b1f9a8ae51f7f7705d2608a7e472151a6748a61dc5a008`;
  - `docs/development/crystal-lattice-documentation.md`: 959 words, SHA-256
    `9dfb5117f599980eef621972200d79a75024c8213f54344fe2c3dcb030a01100`;
  - canonical `agents/TASKS-v7.md`: 1,273 words, SHA-256
    `0840dd79e15cdb335496f7876fb4f98976f818c748d9858f17d841be294ac232`;
  - bundled `TASKS_v7.md`: 1,453 words, SHA-256
    `11894d337de6685191a5adc622963a9a8fd526be302f439eb71658e84234276b`.
- Task-only initial growth ceilings are 411 words for the
  project-independent guide and 254 words for current canonical task guidance.
  The root policy remains subject to the stricter 300-word ceiling, allowing
  at most 11 net words unless existing text is replaced. The Crystal Lattice
  conventions have no planned addition. Task-guidance measurements will be
  recalculated after the synchronization work is integrated.
- First baseline result, GLM high effort:
  - command: Test 13 with `AGENT_EVAL_PROFILE=glm`,
    `AGENT_EVAL_GUIDANCE_VARIANT=candidate`, and fresh branch cache label
    `source-wording-baseline-test13-glm-high-1`;
  - integrated pre-change guidance SHA-256:
    `d428bd65eb69bf4406ef7637540d28283bcc14078b3f25d633024275b50fd086`;
  - seed run:
    `20260914T175117.316420Z-seed-09-partial-major-change-39dc3fd6`;
  - branch run:
    `20260914T175237.316313Z-13-partial-major-change-18b7b76b`;
  - model: `glm-5.3-flash:cloud`, reasoning effort `high`;
  - result: 11 of 12 deterministic findings passed. Phase 2 code, tests,
    requirements, current capability description, pending later behavior, and
    temporary specification progress were otherwise correct.
  - failing destination: the README changed to “Sync v2 currently supports
    Phase 1 local change capture and Phase 2 queued uploads with stable
    idempotency keys,” copying source-local labels into current user
    documentation instead of describing the capabilities directly.
  - the completion response repeated the same labels in its headings and
    summary. The response remains useful semantic evidence, but it is not
    treated as a maintained-output failure because its reader has the current
    conversation.
  - the guidance-neutral seed emitted one invalid shell call with a string
    `command` instead of the required string array. The tool returned a
    recoverable error; the model continued, completed the seed with no changed
    paths, and the branch executed normally. This setup noise did not cause the
    behavioral failure.
  - pytest exited with one failed test in 114.21 seconds, as expected from the
    retained user-documentation assertion. No provider errors or branch
    execution errors were recorded.
- Completed the valid Test 13 baseline matrix against guidance SHA-256
  `d428bd65eb69bf4406ef7637540d28283bcc14078b3f25d633024275b50fd086`:
  - GLM low, run
    `20260914T190047.540279Z-13-partial-major-change-4560b06c`: retained
    `Phase 1` and `Phase 2` in the README;
  - GLM high, run
    `20260914T175237.316313Z-13-partial-major-change-18b7b76b`: retained
    `Phase 1` and `Phase 2`;
  - GLM max, run
    `20260914T190047.611246Z-13-partial-major-change-526be27c`: retained both
    labels and added unavailable Phase 3 conflict resolution;
  - GPT low, run
    `20260914T190721.197808Z-13-partial-major-change-b32ce765`: translated
    local capture but retained `Phase 2 upload queuing`;
  - GPT high, run
    `20260914T190906.452302Z-13-partial-major-change-6545e004`: retained
    Phase 1/2 labels and added Phase 3 conflict resolution as a target;
  - GPT max, run
    `20260914T190906.559475Z-13-partial-major-change-549b7c2c`: retained
    Phase 1/2 labels and added Phase 3 conflict resolution as pending.
- All six valid runs implemented and verified Phase 2 correctly but failed the
  current-user terminology boundary. Four failed only or primarily through
  source-label retention; GLM max and GPT high/max also exposed unavailable
  behavior. The model responses repeated the same labels and are retained for
  interpretation without becoming a separate acceptance failure.
- Added focused `AGENT_EVAL_REASONING_EFFORT` selection without changing Test
  13's prompt, fixture, mutation boundary, or behavioral assertions. Explicit
  effort now reaches GLM through provider request options and GPT through the
  reasoning extension's configuration input. Thirty-three deterministic tests,
  Ruff, and Python compilation pass.
- The first GPT-low attempt incorrectly passed effort through generic request
  options and was rejected by the OpenAI Responses SDK. That setup run is
  excluded from behavioral evidence. The provider-specific mapping was fixed
  and the fresh GPT-low result above completed normally.
- Added specification-owned Tests 30–31 and Seed 12:
  - Test 30 reuses Seed 05 with `Task 010`, `Stage A`, and
    `useful, portable` task variants and inspects task, specification,
    requirements, decisions, paths, headings, package developer index, and
    response.
  - Seed 12 defines an established `is_terminal` API and a pending display
    label behavior whose new Python function name is intentionally unspecified.
  - Test 31 uses the same three source-term classes and inspects the selected
    function name, test names, comments, requirement evidence, current
    developer documentation, and response while preserving established
    names.
- Initial high-effort model observations:
  - GLM Test 30 retained `Task 010` and `Stage A` in specification or
    requirement references; its response also used the local terms, while its
    evaluative-wording variant
    used offline-synchronization terminology.
  - GPT Test 30 retained `Task 010` and `Stage A` in specification records and
    promoted `portable` into a target requirement or developer-index
    description.
  - Both models chose behavior-based source and test identifiers in Test 31.
    GLM retained `Task 010` in developer documentation, and some GPT/GLM
    samples used bare `STATUS-002` comments without explaining the assertion.
    Responses often used the conversation's local labels, which is recorded
    but not treated as a maintained-file failure.
  - Both models' evaluative-wording Test 31 variants used behavior-based
    function and test names and avoided the evaluative words in maintained
    identities.
- Calibrated the scenarios from complete artifacts:
  - specification checks now inspect complete non-task specification records
    and the package developer index rather than headings and requirement rows
    alone;
  - code/test checks distinguish identifiers and Python comments from ordinary
    evaluative prose, inspect current developer and requirement text for
    ordinal/sequence labels, and retain responses for semantic review;
  - a requirement reference must carry explanatory label/status behavior on
    the same comment or docstring line rather than relying on a nearby function
    name;
  - the status-label fixture now specifies `KeyError` for unknown values, and
    the consumer independently executes the selected function to verify the
    required behavior rather than requiring literal strings in source.
- Completed the low/high/max sequence-label matrix on both GLM and GPT:
  - every valid Test 30 run retained `Stage A` in a specification record,
    developer index, or requirement provenance;
  - Test 31 source and test identifiers remained behavior-based; GLM max plus
    GPT high/max exposed bare requirement-ID comments, while other failures
    were confined to conversation responses and are no longer acceptance
    failures;
  - one initial GPT-max Test 30 stream ended with an incomplete chunked read
    and is excluded; fresh run
    `20260914T205731.278668Z-30-source-terms-in-specification-records-sequence-label-d51b48d4`
    completed and reproduced the terminology failure.
- Deterministic support now validates both model effort mappings, all
  multi-prompt scenario pages, fixture source paths, baseline-runnable status
  packages, source-term branch variants, and collection. Thirty-four focused
  deterministic tests pass.
- September 15, 2026: completed the behavioral matrix for the concise rewrite
  at combined guidance SHA-256
  `0d68a1ac858c7ba1e8da9338bcb455c88abe14e000680732b7f68c2811ae58a0`.
- High-effort GLM results:
  - Test 13 failed because current user documentation retained internal
    progress grouping;
  - Test 30 passed the task-number and evaluative-wording variants and failed
    the sequence-label variant;
  - all three Test 31 source/test variants passed;
  - Tests 04 and 14 passed, preserving the established portable contract term.
- High-effort GPT results:
  - Test 13 passed for the first time;
  - Test 30 passed the task-number and evaluative-wording variants and failed
    the sequence-label variant;
  - all three Test 31 source/test variants passed;
  - Tests 04 and 14 preserved the established portable contract terminology
    but failed their older mechanical expectation that target documentation
    state remain `Pending` rather than `Documented`. Those failures are not
    terminology regressions.
- Selected low/max sentinel results:
  - GLM low: Test 13 failed and the sequence-label Test 30 variant passed;
  - GLM max: Test 13 failed and the sequence-label Test 30 output was
    semantically valid under the destination name `offline-delivery`;
  - GPT low: Test 13 and the sequence-label Test 30 variant both failed;
  - GPT max: Test 13 failed and the sequence-label Test 30 variant passed.
- Corrected one narrow Test 30 assertion after complete artifact review. A
  package specification named `offline-delivery` is valid destination-domain
  terminology, so the test now requires a package specification index rather
  than requiring the path itself to contain `sync`. Replaying the preserved
  GLM-max artifact then passed.
- Current-rewrite conclusion before Option A:
  - behavior-based source/test names and explanatory requirement comments are
    stable at high effort on both models;
  - task-number and evaluative wording are handled at high effort by both
    models in the latest sample;
  - sequence-label behavior remains effort-sensitive and is the main
    cross-record weakness;
  - Test 13 remains model/effort-sensitive, passing GPT high but failing GLM
    high and both models at low/max.
- Applied the approved Option A rewrite:
  - defined input material and maintained destination before the general rules;
  - paired each of four general rules with one explicitly marked portable
    example;
  - used example vocabulary distinct from held-out scenario terms;
  - kept six destination-specific instructions in a separate application
    section;
  - added one different compact example to root `AGENTS.md`.
- Option A combined guidance SHA-256:
  `3a4c51039aa48823665334c73129e3ecb01aa299539639c57566b661ab549c4c`.
  The project-independent guide is 2,200 words, 145 words or 7.06% above the
  integrated baseline. Root documentation guidance is 294 words. The Crystal
  Lattice addendum remains unchanged.
- Added deterministic coverage for definition-before-use, exactly four marked
  portable-guide examples, one root example, separation of examples from
  destination instructions, and lexical separation from held-out scenario
  terms. Thirty-five deterministic tests pass.
- Option A high-effort results:
  - GLM: Tests 04 and 14, Test 30 evaluative wording, and Test 31 sequence and
    evaluative wording passed. Test 13, Test 30 task-number and sequence-label,
    and Test 31 task-number failed.
  - GPT: Test 04, Test 30 sequence and evaluative wording, and Test 31
    task-number and evaluative wording passed. Test 13, Test 14's legacy
    `Pending` status assertion, Test 30 task-number, and Test 31 sequence-label
    failed.
  - Both Test 14 outputs preserved the established portable contract term; the
    GPT mechanical failure was unrelated documentation-state vocabulary.
- Option A low/max sentinels:
  - GLM low: Test 13 and Test 30 sequence-label failed;
  - GLM max: Test 13 failed and Test 30 sequence-label passed;
  - GPT low: Test 13 and Test 30 sequence-label failed;
  - GPT max: both sentinels passed.
- Complete artifact inspection found no general improvement over the preceding
  concise rewrite. Option A improved guidance structure and prevented example
  vocabulary from matching held-out prompts, but the failure distribution
  moved between models and efforts.
- The two Option A Test 31 failures used requirement IDs without explaining
  the assertion: GLM used bare `# STATUS-002` comments, while GPT placed
  `STATUS-002` in test function names. The preceding concise rewrite had an
  application-specific explanatory-comment example and passed all Test 31
  variants on both models. This supports keeping generic examples separate
  while allowing narrowly justified examples beside non-obvious specific
  instructions.
- Added the dated result:
  `maintainer/specifications/documentation-and-specification-standard/agent-behavior-verification/20260915-example-backed-terminology-results.md`.
- Final focused verification after Option A:
  - 35 deterministic documentation-standard tests passed;
  - the eight revised extended branches collected successfully;
  - Ruff, Black, Python compilation, and `git diff --check` passed;
  - all relative file targets in 14 changed Markdown files resolved;
  - no behavioral evaluation process remained running.
- Task-guidance parity, documentation preparation, and MkDocs build were not
  run because subtask 068 has not applied the canonical/bundled task-guidance
  change. The combined verification checklist remains incomplete for that
  reason.
- September 16, 2026: replaced the proposed runtime candidate renderer with
  committed complete fixture sets under
  `maintainer/agent-evaluation/suites/documentation_standard/fixtures/destination_terminology_guidance_sets/`.
  The suite continues to use its existing current-guidance or explicit
  directory selection; no production or general evaluation runtime changed.
- Added a fifth `contextual` wording family. It defines context as where
  wording comes from, where it is used, and its audience; distinguishes source
  context; and uses explicit file or record language where context alone would
  be ambiguous.
- Added a small deterministic fixture compiler and generated 11 complete
  roots: the committed checkpoint plus generic and specific forms of five
  wording families. The output contains 77 files and is approximately 812 KB.
  Every set includes the six supported guidance paths and a stable manifest.
- Renamed the fixture directory, deterministic test, test plan, review record,
  and index links so their destination-terminology scope is explicit.
- Removed the hardcoded Git revision from the compiler, manifests, and tests.
  `option-a-checkpoint` is a maintained snapshot fixture used only to compile
  the candidate sets. Repository-current behavior continues to use the
  evaluator's normal `candidate` guidance source.
- Completed semantic inspection of every compiled root policy and guide
  section, all checkpoint diffs, and all generic/specific diffs. Review found
  and corrected excessive marker-removal spacing, an abstract initial context
  definition, and one awkward line wrap. Independent human review and
  first-real-branch provenance checks remain pending.
- Added six deterministic fixture tests covering reproducible compilation,
  manifest and `GuidanceSource` agreement, changed-file boundaries,
  generic/specific pairing, shared held-out examples, and contextual
  definition-before-use.
- Fixture-preparation verification:
  - all 78 `maintainer/agent-evaluation/tests` passed;
  - focused and full Ruff checks passed;
  - focused mypy passed;
  - Black reformatted the two new Python files and its focused check then
    passed;
  - `compile.py --check`, Python compilation, Markdown links, fixture
    whitespace, and `git diff --check` passed.
- Full package mypy still reports two pre-existing assignment errors at
  `maintainer/agent-evaluation/tests/test_documentation_standard_suite.py:377`
  and `:378`. The new compiler and fixture test are type-clean.
- No real-model evaluation or temporary parallel launcher was started during
  fixture preparation.
- Added focused Test 32 for remediation rather than prevention. Its event SDK
  user page begins with `Milestone Cedar`, while the prompt does not contain
  that term. The test requires removal, preserved current behavior, exclusion
  of target-only replay, no replacement progress heading, and one-page scope.
- Completed the high-effort generic comparison across five guidance sets and
  both providers:
  - all ten Test 32 candidate runs had matching manifest hashes and correct
    injection provenance;
  - all 90 Tests 04/13/14/30/31 branches completed without provider errors;
  - one stalled GLM file-centered process was excluded after seven branches,
    and its two missing Test 31 branches completed in a focused retry;
  - no generic wording was uniformly strongest across both providers;
  - every generic candidate failed Test 13 on both providers;
  - abstract was strongest for Test 30, while contextual and explicit-contexts
    were strongest for GLM Test 31;
  - action-first was weakest overall and uniquely failed GLM Test 32.
- Recorded the generic matrix in
  `maintainer/specifications/documentation-and-specification-standard/agent-behavior-verification/20260916-destination-terminology-generic-results.md`.
- Completed the paired high-effort specific comparison:
  - all ten specific Test 32 runs passed;
  - all 90 Tests 04/13/14/30/31 branches completed without provider errors;
  - the specific section eliminated every Test 31 failure across both
    providers and all wording families;
  - explicit-contexts showed the strongest Test 30 improvement;
  - abstract remained the strongest overall terminology candidate;
  - Test 13 failed for every candidate on both providers;
  - GPT control failures remained documentation-state differences rather than
    terminology regressions.
- Selected abstract-specific, explicit-contexts-specific, and
  file-centered-specific for high repeats and low/max sentinels.
- Recorded the specific matrix in
  `maintainer/specifications/documentation-and-specification-standard/agent-behavior-verification/20260916-destination-terminology-specific-results.md`.
- Completed fresh high repeats and low/max sentinels for abstract-specific,
  explicit-contexts-specific, and file-centered-specific:
  - Test 13 failed in all 24 selected candidate/provider/effort samples;
  - all 36 full-matrix and repeat Test 31 samples passed after the specific
    requirement-reference rule was added;
  - Test 32 passed 27 of 28 specific samples, with one low-effort GLM run
    adding excluded replay behavior as a limitation;
  - Test 30 remained stochastic, with explicit-contexts strongest for sequence
    labels and file-centered strongest in the fresh high repeat;
  - two GPT abstract max-effort attempts exhausted the default 30-tool budget
    and were excluded; the unchanged branch completed and passed with an
    explicit budget of 50.
- Recorded the robustness evidence in
  `maintainer/specifications/documentation-and-specification-standard/agent-behavior-verification/20260916-destination-terminology-robustness-results.md`.

## Execution plan

Status: Draft

The revised plan below supersedes Sections 1–10 for all remaining work.
Sections 1–10 are retained afterward as the historical plan that produced the
September 15–16 fixture and behavioral evidence. Execution of the revised plan
waits for explicit approval.

### Current revised plan

#### 1. Preserve and map historical evidence

1. Keep commit `ef936892` and the September 15–16 generic, specific, and
   robustness results as historical evidence for the pre-reconciliation
   baseline.
2. Treat the currently uncommitted Test 32 mutation/removal scenario and its
   runs as exploratory evidence. Do not use them as acceptance evidence for
   the new confirmation-before-removal requirement.
3. Add an explicit historical-to-active mapping rather than rewriting run IDs
   or dated evidence:
   - historical Test 30 -> active Test 36;
   - historical Test 31 -> active Test 37;
   - historical Test 32 -> superseded exploratory removal behavior;
   - active Test 38 -> confirmation before removing existing terminology.
4. Record that historical Test 13 mixed prevention with cleanup because its
   user page already contained phase wording. Revised Test 13 starts from a
   user page without progress labels.

#### 2. Start from the new ownership and compilation structure

Use
`/Users/ferenci84/Dev/Mine/ai-agent-platform-worktrees/20260728-documentation-guide-rewrite`
as a read-only reference. The September 18 structure moves maintainer
specifications and reports, gives the documentation suite ownership of its
scenarios and targets, and introduces `maintainer/guidance/` as the source and
compiler boundary.

Prefer a new independent branch rather than rebasing or merging this branch:

1. Wait until the other worktree's pending runner-fidelity corrections are
   committed. Record that exact commit as the structural base; do not branch
   from its dirty working tree.
2. Create a new worktree and branch from the committed structural tip, or from
   `develop` if that tip has already been integrated:
   - proposed branch:
     `task/20260918-destination-terminology-guidance`;
   - proposed worktree:
     `/Users/ferenci84/Dev/Mine/ai-agent-platform-worktrees/20260918-destination-terminology-guidance`.
3. Add a new subtask at
   `tasks/20260728-package-local-documentation-standard/075-destination-terminology-guidance.md`.
   Subtask 067 is already owned by requirement-quality calibration in the new
   structure, so the current task file remains historical planning evidence
   rather than being copied wholesale.
4. Update the parent task's subtask list and requirement mapping in the new
   branch.
5. Do not cherry-pick `ef936892` or merge this branch. Its 96-file fixture
   commit reproduces complete roots using an obsolete compiler and ownership
   layout, creating more conflicts than useful history.

#### 3. Transplant only durable material

Carry forward:

1. The approved requirement distinctions:
   - prevention of newly introduced source-local labels;
   - separate authority and confirmation for existing wording;
   - destination-specific reference and naming rules;
   - semantic assessment as supporting evidence.
2. The useful candidate wording sources:
   - abstract;
   - explicit-contexts;
   - file-centered only as a possible sentinel;
   - the concise specific-rule section.
3. The behavioral ideas and reviewed assertions from historical Tests 30–31,
   renamed to Tests 36–37.
4. The revised Test 13 prevention-only design.
5. The existing-label observations from historical Test 32, but not its
   autonomous-removal acceptance rule or implementation.
6. The September 16 generic, specific, and robustness reports as historical
   interpretation, moved under
   `maintainer/docs/evaluations/documentation-guidance/` with a concise current
   note explaining their old numbering and direct-injection setup.
7. The decisions and rationale from this task needed to understand candidate
   selection, rejected alternatives, and the prevention/removal split.

Recreate in the new structure rather than copying:

1. Portable root candidates as ordinary bundle overlays under
   `maintainer/guidance/candidates/`, each extending
   `maintainer/guidance/current` and overriding only the portable
   `documentation` section.
2. Full project-independent guide variants as suite-owned evaluation inputs
   paired to the same candidate IDs. They are not compiler outputs.
3. Active scenario pages under
   `maintainer/agent-evaluation/suites/documentation_standard/scenarios/`.
4. Semantic targets under
   `maintainer/agent-evaluation/suites/documentation_standard/targets/`.
5. Deterministic and real-model consumers using the suite's common Crystal
   Lattice runner, production system-message feature, matching Codex/Claude
   tools, normal workspace `AGENTS.md` loading, and conditional canonical task
   guidance.
6. Frozen producer/judge records under the suite's `fixtures/` tree and dated
   human interpretation under `maintainer/docs/evaluations/`.
7. Requirement rows in their new owners:
   - reusable terminology behavior in
     `maintainer/docs/development/specifications/documentation-guidance/requirements.md`;
   - Crystal Lattice compilation, task-guidance, and validation integration in
     `maintainer/docs/development/specifications/crystal-lattice-guidance-integration/requirements.md`;
   - suite mechanics and semantic-evaluation requirements in
     `maintainer/agent-evaluation/suites/documentation_standard/docs/development/requirements.md`.

Leave behind:

1. The ten complete compiled guidance roots.
2. The task-local destination-terminology compiler and its deterministic test.
3. Old central `maintainer/specifications/` paths and mixed
   specification/result/scenario indexes.
4. The active Test 32 autonomous-removal assertion.
5. Action-first and contextual candidate families unless later evidence
   establishes a distinct remaining question.
6. Old root/full-guide snapshots already represented by commit `ef936892` and
   the historical reports.

#### 4. Reconcile IDs and active scenario numbers

1. Preserve the new structure's ownership of:
   - Tests 30–35;
   - `DOCGUIDE-007`;
   - `DOCVAL-011`–`DOCVAL-013`;
   - `DOCAGENT-003`–`DOCAGENT-004`;
   - Subtask 067.
2. Use:
   - Test 36: source terms in specification records;
   - Test 37: source terms in code and tests;
   - Test 38: confirmation before removing existing terminology.
3. Use the still-available IDs:
   - `DOCGUIDE-008`: prevention and destination-specific terminology;
   - `DOCGUIDE-009`: existing-wording notice and confirmation;
   - `DOCAGENT-002`: concise portable root terminology instruction;
   - `DOCFLOW-007`: task-guidance terminology and reference behavior;
   - `DOCVAL-014`: Crystal Lattice behavioral validation;
   - `DSEVAL-004`: suite-owned producer/semantic assertion contract.
4. Historical dated result pages retain Tests 30–32 and their original run
   IDs. New pages provide the explicit mapping to Tests 36–38.

#### 5. Make Test 13 prevention-only

1. Change the sync-engine fixture's initial README to describe only current
   capability in user language, with no `Phase`, `Stage`, milestone, task ID,
   or requirement ID.
2. Keep phase terminology in the internal task/specification/requirements and
   branch prompt so the request still creates realistic source pressure.
3. Preserve the partial-implementation behavior:
   - Phase 2 implementation and evidence become current;
   - later conflict resolution stays pending internally;
   - one target specification remains.
4. Assert that the final README explains delivered capability without
   introducing the prompt's phase organization or internal future boundary.
5. Treat all pre-reconciliation Test 13 runs as historical mixed-scenario
   evidence and establish a fresh integrated-guidance baseline for the revised
   fixture.

#### 6. Replace autonomous cleanup with confirmation-before-removal

1. Redesign the event SDK branch as active Test 38:
   - the existing user page contains a progress-like label not present in the
     prompt or current product vocabulary;
   - the user requests an otherwise ordinary documentation update;
   - removal of the existing label is not explicitly authorized.
2. The first agent turn must:
   - make no file changes;
   - notice and identify the existing label as potentially internal or
     inappropriate for the page;
   - recommend a destination-appropriate replacement or removal;
   - ask one focused question confirming whether to remove it;
   - avoid claiming that the documentation update is complete.
3. Keep an optional continuation after an affirmative user response only if
   needed to verify the resulting edit. The acceptance boundary requested here
   is the first confirmation-seeking response.
4. Do not require a literal question sentence, fixed vocabulary, or direct
   repetition of the hidden semantic target.

#### 7. Add separate structured semantic assessment

Adopt the technique used by the documentation-guide-rewrite worktree without
copying its requirement-quality domain model or datasets.

1. Producer runs remain ordinary terminology tests and record:
   - response;
   - changed paths;
   - guidance/model/effort provenance;
   - source run ID and source-record hash;
   - deterministic no-mutation and completion findings.
2. Freeze selected Test 38 producer outputs into a small
   destination-terminology dataset. Do not call a judge inline from every
   producer test.
3. Add a versioned hidden target and JSON-only evaluator schema covering:
   - existing label noticed;
   - ambiguity explained;
   - removal/translation recommendation;
   - explicit confirmation requested;
   - question focused and actionable;
   - no silent decision;
   - no completion claim.
4. Run a separate neutral-workspace semantic evaluator with GLM at max effort
   using the existing `fresh_prompt` pattern.
5. Reuse the proven parsing discipline:
   - strip an optional JSON fence;
   - extract one JSON object;
   - permit only enumerated, recorded repairs such as a trailing comma or
     missing candidate-closing brace;
   - reject other malformed output.
6. Deterministically validate schema version, dataset/scenario IDs, exact
   candidate set, all required semantic dimensions, enums, evidence, and
   evaluator provenance.
7. Calibrate against human-approved anchor responses representing a clear
   confirmation request, a vague mention without a question, silent removal,
   and silent preservation.
8. Record judge results and parser repairs separately. Model judgment is
   supporting evidence; human review remains required.

#### 8. Recreate the smallest useful candidate set

1. Recreate abstract-specific and explicit-contexts-specific as candidate
   bundle overlays that override only the portable `documentation` section.
2. Pair each candidate ID with one suite-owned
   `docs/development/documentation.md` variant assembled from the same reviewed
   wording source. Add a deterministic consistency check between the portable
   and full-guide forms without inventing a second general compiler.
3. Retain file-centered as a sentinel only if its different behavior still
   adds diagnostic value after deterministic inspection.
4. Do not rerun action-first or the full five-by-two candidate matrix unless
   the smaller comparison leaves a material ambiguity.
5. Keep examples lexically separate from Tests 13, 36, 37, and 38.
6. Compile candidate root guidance with `maintainer.guidance` into temporary
   workspaces. Do not commit complete compiled root trees.

#### 9. Run the revised behavioral comparison

1. Establish the exact structural-base current bundle, target, full guide, and
   canonical task-guidance hashes before candidate evaluation.
2. Run prevention scenarios separately:
   - revised Test 13 for user-documentation phase-label prevention;
   - Test 36 for specification/task-reference terminology;
   - Test 37 for code, tests, and requirement-reference terminology;
   - Tests 04/14 as established-term controls.
3. Run Test 38 separately as an existing-wording authority/confirmation
   scenario.
4. Start with both providers at high effort. Add low/max sentinels only for
   boundaries showing variance or a distinct failure.
5. Use the suite's common Crystal Lattice runner for acceptance evidence:
   - compile workspace `AGENTS.md` from the selected bundle and Crystal Lattice
     target;
   - load it through the production system-message feature;
   - preserve the standard Codex or Claude model-family message and matching
     tool package;
   - use canonical task guidance through `include_tasks` only when the
     scenario requires it;
   - verify source hashes, occurrence counts, delivery role/strategy, and shell
     schema before the model call.
6. A direct-injection wording-isolation run may be used diagnostically, but it
   is labeled as injection evidence and cannot replace the production-runner
   acceptance result.
7. Run the semantic evaluator only after producer records are frozen and
   complete.
8. Inspect complete files, responses, diffs, tool behavior, deterministic
   findings, semantic assessments, and provenance. Do not substitute judge
   output for artifact inspection.
9. Do not rerun the documentation-guide-rewrite worktree's requirement-quality
   or root-guidance model matrices.

#### 10. Calibrate guidance from the separated evidence

1. The primary public and root rule says what to do when creating or adding
   content: preserve required behavior and established terms, but do not
   introduce source-local labels or organization as destination names.
2. A separate existing-wording instruction says not to silently normalize a
   maintained page. When cleanup is not already authorized, identify the
   concern, recommend the change, and ask confirmation.
3. Keep the evidence-backed requirement-reference rule and explanatory
   assertion example.
4. Refine the task-reference rule only as needed to prevent an otherwise
   descriptive link from being followed by a local number, stage, or nickname.
5. Add a current-user-documentation prevention example only when revised Test
   13 evidence shows the concise rule remains insufficient. Use wording
   different from all behavioral fixtures.

#### 11. Verify and present for approval

1. Run central guidance compiler checks, documentation-suite deterministic
   tests, candidate/full-guide consistency checks, task-guidance parity, Ruff,
   Black, focused/full type checks, maintained-link checks, documentation
   preparation, and the normal MkDocs build as applicable.
2. Add new dated result pages. Preserve September 15–16 pages as historical
   evidence and document the active-number mapping.
3. Update the reusable guidance, Crystal Lattice integration, and suite-owned
   requirements; dated evaluation index; new Subtask 075; and parent status
   without marking model judgment human verified.
4. Present:
   - the exact structural base and selective transplant inventory;
   - revised prevention and confirmation scenarios;
   - deterministic and semantic assertion design;
   - paired model results;
   - recommended final guidance wording;
   - remaining human decisions.

### Historical executed plan

### 1. Reconcile the integrated baseline

1. Rebase the isolated worktree after the committed
   `task/20260914-guidance-follow-up-rewrites` result is integrated into
   `develop`, or explicitly reconcile its commits if the user chooses another
   delivery order.
2. Record the exact baseline revision and hashes for root `AGENTS.md`,
   `docs/development/documentation.md`, the Crystal Lattice conventions,
   canonical and bundled `TASKS-v7`, relevant scenario contracts, and
   executable consumer modules.
3. Measure each guidance file and calculate its 20% initial-growth ceiling.
   Preserve the stricter root `AGENTS.md` 200–300-word target.
4. Confirm the canonical task-guidance source and synchronization mechanism
   selected by
   `tasks/20260728-package-local-documentation-standard/068-task-guidance-specification-alignment.md`
   before planning an edit to either v7 copy.

### 2. Observe behavior before changing guidance

Preserve prompts, fixtures, outputs, and provenance. Do not begin by adding
new forbidden-token assertions.

1. Re-run Test 13 against the integrated pre-change guidance on both
   `glm-5.3-flash:cloud` and the established GPT profile at supported low,
   high, and max reasoning efforts. Inspect the README, specification,
   requirements, task, response, and tool sequence for every run.
2. Add exploration-only branch variants over existing seeds:
   - a Seed 05 variant that introduces source-local ordinal, sequence, and
     evaluative terms while requesting the already-defined specification
     capability;
   - a Seed 06 or Seed 07 variant that introduces the same classes of terms
     while requesting a code and regression-test change.
3. Start the new variants with both established profiles at high effort. Run
   the full low/high/max effort set on both GLM and GPT for at least one
   multi-destination variant. Expand the full effort matrix to the remaining
   variants only where initial outputs show variance or a distinct mistake.
4. Inspect complete changed files and responses for:
   - unexplained conversational wording in task requirements or headings;
   - bare ordinal references in specifications, requirements, or decisions;
   - source-local adjectives or labels in specification paths and titles;
   - leaked terms in source filenames, function names, test filenames, test
     names, comments, or identifiers;
   - developer documentation that assumes unintroduced specification context;
   - user documentation that assumes internal records or source organization;
   - inappropriate suppression of an exact requested or established term.
5. Record recurring behaviors by source class and destination boundary before
   selecting final scenario contracts or candidate wording.

### 3. Calibrate the smallest scenario set

1. Keep Test 13 as the current-user-documentation scenario with its prompt and
   expected behavior unchanged. Update traceability only as needed for the
   new requirements.
2. Reuse Seed 05 for a specification/requirements/decision/filename scenario
   when the observation confirms that its existing facts and mutation scope
   are sufficient.
3. Reuse Seed 06 or Seed 07 for a source/test naming scenario when one can
   exercise function and test names without adding unrelated product behavior.
4. Add assertions to an existing consumer instead of creating a new numbered
   scenario only when the existing prompt already creates the relevant
   pressure and the new assertion checks the same behavioral outcome.
5. Add a new seed only if the existing fixtures make the source term an actual
   domain requirement, omit a necessary destination, or require broad
   artificial fixture changes.
6. Include a control case in which exact wording is explicitly required or is
   already established, preventing the rule from degenerating into automatic
   renaming.
7. Define semantic review dimensions first. Add narrow mechanical backstops
   for observed paths, identifiers, references, or tokens only after inspecting
   the model results.

### 4. Add Candidate A

Candidate A contains only the two initial additions.

1. Add the four general rules from `Initial guidance candidates` to
   `docs/development/documentation.md`.
2. Integrate the concrete root `AGENTS.md` candidate into the consolidated
   documentation section rather than adding another policy block.
3. Keep the root documentation section at approximately 200–300 words by
   replacing less precise wording instead of appending another paragraph.
4. Do not yet add file-role applications, examples, or task-guidance wording.
5. Confirm that neither initial addition enumerates the held-out prompt terms.

### 5. Evaluate Candidate A

1. Run Test 13 and the selected cross-record and code/test scenarios with the
   same prompts, fixtures, models, reasoning efforts, and assertions used for
   the baseline observations.
2. Inspect full files, diffs, responses, and tool sequences before reducing
   results to pass/fail.
3. Identify which simple naming and terminology choices Candidate A corrects
   and which cross-record or self-containment cases remain difficult.
4. Preserve passing, failing, and mixed results without changing the prompts
   or adding candidate-specific token assertions.

### 6. Add Candidate B

After Candidate A evidence is recorded:

1. Add the six concise file-role applications from
   `Initial guidance candidates` immediately after the four general rules in
   `docs/development/documentation.md`.
2. Keep reference forms descriptive:
   - task references use full paths;
   - requirement and decision references pair their stable identifier with a
     concise description and direct link;
   - tests or code comments that cite a requirement also explain the behavior;
   - user documentation omits internal tracking identifiers;
   - developer documentation may use a descriptive linked reference but
     remains understandable without opening it.
3. Through the canonical source and synchronization mechanism owned by
   `tasks/20260728-package-local-documentation-standard/068-task-guidance-specification-alignment.md`,
   add the task-guidance candidate after its Candidate A comparison is
   preserved.
4. Keep task guidance concise and route detailed applications to the
   project-independent guide instead of reproducing them.
5. Do not add the project-independent applications to the Crystal Lattice
   conventions page.

### 7. Evaluate Candidate B

1. Run the unchanged scenario set again with the same models, reasoning
   efforts, prompts, fixtures, and assertions.
2. Inspect complete outputs before comparing the Candidate A and Candidate B
   results.
3. Confirm that the final candidate:
   - selects destination-appropriate terminology across the exercised
     boundaries;
   - preserves explained task-local wording where appropriate;
   - preserves explicit exact names and established domain terms;
   - uses descriptive complete references;
   - does not merely substitute one unexplained source label for another.
4. Candidate B must cover the harder task-handoff, record-reference,
   developer-documentation, and user-documentation cases, including Test 13.
5. Add more public guidance only when repeated paired results identify a
   shared misunderstanding not already covered by the concise general rule or
   the six applications.
6. Preserve mixed results and model/effort variance. Do not tune prompts or
   weaken assertions to manufacture a candidate pass.

### 8. Apply the approved example-backed rewrite

This step is distinct from the earlier experimental Candidate A.

1. Complete and record the behavioral matrix for the current concise rewrite
   before changing guidance again.
2. Introduce the roles of input material and maintained destination before the
   general rules so later references are unambiguous.
3. Pair each general rule with one explicitly marked portable example. The
   examples illustrate individual transfers rather than enumerate destinations
   or prohibited terms.
4. Use example wording that is lexically separate from held-out behavioral
   prompts and is not specific to Crystal Lattice.
5. Keep destination-specific instructions in a separate application section;
   do not present them as examples.
6. Add one compact example to the recurring root instruction without
   duplicating the complete guide.
7. Rerun the unchanged behavioral matrix and inspect complete artifacts before
   deciding whether any further wording is justified.

### 9. Verify and record evidence

1. Run focused deterministic tests for fixtures, guidance sources, model and
   reasoning profiles, scenario collection, mutation allowlists, provenance,
   and any secondary assertions.
2. Run the calibrated documentation-guidance routine group and the focused
   second-model sentinels required by the observed boundaries.
3. Run task-guidance parity and affected task-guidance evaluation after
   `tasks/20260728-package-local-documentation-standard/068-task-guidance-specification-alignment.md`
   applies the canonical edit.
4. Run `git diff --check`, relative-link checks, documentation preparation,
   and the normal MkDocs build.
5. Measure net additions against the integrated pre-change files and record
   any evidence-backed exception before expanding beyond 20%.
6. Add a dated behavioral-results report rather than rewriting historical
   result files.
7. Update live requirement evidence without treating model evaluation as
   human verification.
8. Present the changed guidance and representative before/after outputs for
   explicit human review.

### 10. Compare versioned generic and specific guidance

The checkpoint before this comparison is commit
`ebde9ab0c1b0a098104accb86815e53612938e3e`. Do not edit the public
`AGENTS.md` or documentation guide while testing wording alternatives.

Complete committed guidance sets, their maintained source sections, and the
destination-terminology test plan live under
`maintainer/agent-evaluation/suites/documentation_standard/fixtures/destination_terminology_guidance_sets/`.

1. Compile complete candidate roots from the maintained
   `option-a-checkpoint` fixture and commit the resulting directories for later
   reproduction. Tests select either current repository guidance or one
   supplied guidance-set directory.
2. Compare five general-wording families:
   - the current abstract grouping terms as a control;
   - explicit action-first wording;
   - wording centered on each file, its readers, and interfaces;
   - an explicit list of maintained contexts;
   - a concise `context` form that defines context, source context, and
     audience before use.
3. Compile every family in both generic-only and comprehensive-specific modes.
4. Run, inspect, and record every generic-only candidate before starting any
   comprehensive-specific run.
5. Keep prevention and remediation in separate scenarios:
   - Tests 30 and 31 verify that terms do not enter new records;
   - a new focused scenario verifies removal of a term already present in an
     edited current page;
   - Test 13 remains unchanged as broader combined integration coverage.
6. Use the same examples, prompts, fixtures, tools, assertions, and profiles
   across wording candidates. Example boundary descriptions remain in
   maintainer analysis only and are not included in injected guidance.
7. Use temporary task-local orchestration to run up to five processes per
   provider concurrently, with no more than ten total and no duplicate
   provider/candidate/mode/effort/cache combination. Do not commit the launcher
   unless it proves a reusable, non-trivial capability.
8. Compare each specific candidate directly with its generic counterpart.
   Specific rules should improve model or effort variants that did not respond
   to the corresponding generic wording.
9. Test the selected generic and specific candidates with fresh high-effort
   repeats and low/max sentinels before proposing a public-file update.
10. Update the master files only after behavioral comparison and human
    selection. Consolidate overlapping public prose rather than copying the
    longer experimental specific version wholesale.
11. Keep task-guidance changes as a later comparison through subtask 068.
12. Verify compiled sets mechanically and through complete human review.
    Confirm the recorded manifest and injection provenance during the first
    real-model branch for each set before running the rest of its matrix.

### Implementation decisions and open questions

- **Proposed September 17 direction, awaiting approval:** make prevention of
  newly introduced source-local labels the primary terminology rule, isolate
  existing-wording cleanup in a confirmation-before-removal scenario, and use
  a separate structured semantic evaluator for that response.
- Proposed: Test 13 keeps its partial-implementation workflow but starts from
  user documentation without phase/stage terminology.
- Proposed: active Tests 30–32 move to 36–38 because the integrated
  documentation-guide worktree owns requirement-quality Tests 30–35.
- Proposed: this task's terminology validation ID moves from `DOCVAL-011` to
  `DOCVAL-014`, with suite mechanics under `DSEVAL-004`; the integrated
  requirement-quality and root-guidance work keeps `DOCVAL-011`–`DOCVAL-013`.
- **Proposed September 18 structural migration:** create a clean independent
  branch from the committed documentation-guide-rewrite structural tip and a
  new Subtask 075. Transplant reviewed terminology material manually; do not
  merge, rebase, or cherry-pick this old branch.
- Proposed: represent portable root wording as central compiler candidate
  overlays and full-guide wording as paired suite-owned evaluation inputs.
  Compile temporary outputs for tests instead of committing complete roots.
- Proposed: use the documentation suite's production Crystal Lattice runner
  for acceptance evidence. Direct injection remains diagnostic wording
  isolation and is labeled accordingly.
- Proposed: semantic evaluation follows the other worktree's producer/frozen
  dataset/hidden target/separate max-effort judge/schema validation pattern,
  but uses a small destination-terminology-specific schema and accepted
  anchors.
- **Approved follow-up direction (September 15, 2026):** retain the
  rule/example structure, but test whether explicitly naming requests, tasks,
  specifications, files, code, tests, and documentation is more effective than
  the grouping terms `input material`, `destination`, and `artifact`.
- Approved: preventing a term from entering a new record and removing a term
  already present in edited content are separate rules and receive separate
  focused tests.
- Approved: examples cover varied boundaries with wording natural to the
  originating context. Boundary labels used during analysis do not appear in
  public examples.
- Approved: all generic-only candidates are run and recorded before the
  comprehensive specific-rule section is injected. Each wording family is
  then tested both without and with that same specific section.
- Approved: task and requirement references are specific rules, not changes to
  a generic example. Task-file guidance about retaining and referencing task
  terms remains a later improvement through subtask 068.
- Approved: root `AGENTS.md` candidates may contain several concise examples
  covering prevention, remediation, and preservation, while the complete root
  documentation policy remains at most 300 words.
- Historical decision: September 16 candidates were complete isolated
  guidance roots compiled from a maintained snapshot fixture. The September 18
  Draft migration replaces that representation with central candidate bundles,
  paired full-guide inputs, and temporary compilation.
- **Historical simplification (September 16, 2026; superseded for new work):**
  the old branch used a task-local deterministic compiler and committed
  complete roots. Preserve commit `ef936892` for reproduction, but do not
  transplant that compiler or its generated trees.
- Approved: deterministic fixture tests do not pin a Git commit. Historical
  provenance belongs in task and result records; current repository guidance
  remains a separate selectable source.
- Approved: add a fifth wording family that defines `context`, `source
  context`, and `audience`, then uses those terms where repeating every
  concrete context would be longer or less clear.
- Approved: empirical consistency review includes complete generated-file and
  pairwise-diff inspection plus provenance confirmation in the first real
  branch for each set; mechanical generation checks alone are insufficient.
- Approved: hosted execution may use up to five concurrent evaluations per
  provider, ten total.
- Approved: parallel-launch code remains temporary and uncommitted unless it
  develops a reusable, non-trivial capability.
- **Initial decision (approved September 15, 2026): choose Option A.** Define
  input material and maintained destination before the rules, pair each general
  rule with an explicitly marked portable example, and keep
  destination-specific instructions in a separate application section.
  Examples are deliberately incomplete and use wording different from
  held-out evaluation terms. This Option A is unrelated to the earlier
  experimental Candidate A.
- Considered Option B: four rules followed by one combined worked example.
  Not selected initially because one transformation may leave some rules
  abstract and encourage overgeneralization from a single case.
- Considered Option C: keep rules and destination instructions together, with
  examples in a separate later subsection. Not selected initially because the
  distance between rule and example weakens the clarification and makes an
  example catalog more likely to grow.
- Approved: the requirement and general rule apply to all source context and
  destination terminology, not one common category of source wording.
- Approved: both the general rule and concise file-role applications belong in
  the project-independent guide. The Crystal Lattice page remains a local
  paths and exceptions addendum.
- Historical decision: Test 13 remained unchanged for the September 15–16
  matrices. The September 17 Draft plan supersedes that fixture choice if
  approved, while preserving the old runs as mixed prevention/removal
  evidence.
- Approved: initial evaluation observes complete artifacts across multiple
  models and reasoning efforts before final assertions or guidance wording are
  selected.
- Approved: each guidance file's initial addition remains below 20%; root
  recurring guidance also stays within approximately 200–300 words.
- Approved: mechanical checks are secondary to semantic and human inspection.
- Recommended: reserve no fixed count of new scenarios before observation.
  The expected minimum is Test 13 plus one specification/record case and one
  source/test case, using existing seeds where they remain realistic.
- Recommended: this task owns the target, project-independent/root wording,
  scenario contracts, and evidence. The task at
  `tasks/20260728-package-local-documentation-standard/068-task-guidance-specification-alignment.md`
  owns canonical/bundled task-guidance delivery and synchronization.
- No unresolved requirement question changes the requested outcome. Approval
  is required for the revised execution plan before repository files other
  than this task are changed.

### Documentation

- `docs/development/documentation.md`
- portable Documentation candidate sections and manifests under
  `maintainer/guidance/candidates/`
- temporary compiled root `AGENTS.md` outputs and compilation locks as
  evaluation evidence, not committed maintained roots
- canonical `agents/TASKS-v7.md`
- bundled task guidance through
  `tasks/20260728-package-local-documentation-standard/068-task-guidance-specification-alignment.md`
- reusable target and requirements under
  `maintainer/docs/development/specifications/documentation-guidance/`
- Crystal Lattice refinement and requirements under
  `maintainer/docs/development/specifications/crystal-lattice-guidance-integration/`
- suite scenarios, semantic targets, full-guide candidate inputs, frozen
  records, and operational documentation under
  `maintainer/agent-evaluation/suites/documentation_standard/`
- dated historical and revised result reports under
  `maintainer/docs/evaluations/documentation-guidance/`
- deterministic evaluator and compiler-consumer tests under
  `maintainer/agent-evaluation/tests/`
- a focused destination-terminology semantic evaluator, hidden target, frozen
  producer dataset, accepted anchors, and result freezer under
  `maintainer/agent-evaluation/suites/documentation_standard/`
- new
  `tasks/20260728-package-local-documentation-standard/075-destination-terminology-guidance.md`
  and the parent task

No substantive Crystal Lattice conventions change is planned.

### Task checklist

#### Historical old-branch work

- [x] Create the isolated worktree and branch.
- [x] Add this subtask to the documentation-standard workstream.
- [x] Update the target specification and add live pending requirements.
- [x] Reconcile the integrated guidance-follow-up baseline.
- [x] Record exact guidance hashes, sizes, and growth ceilings.
- [x] Run and inspect the pre-change Test 13 model/effort matrix.
  - [x] Preserve and inspect GLM and GPT low/high/max results.
- [x] Run and inspect exploratory specification/record variants.
- [x] Run and inspect exploratory source/test naming variants.
- [x] Select the minimum useful scenario and assertion set.
- [x] Add Candidate A's four project-independent general rules.
- [x] Add Candidate A's concise root `AGENTS.md` rule.
- [x] Run and inspect the Candidate A high-effort comparison.
- [x] Add Candidate B's six concise file-role applications.
- [ ] Apply Candidate B's task-specific rule through
  `tasks/20260728-package-local-documentation-standard/068-task-guidance-specification-alignment.md`.
- [x] Run and inspect the Candidate B matrix.
- [x] Expand guidance only if repeated evidence requires it.
- [x] Record the approved Option A and considered Options B–C.
- [x] Complete and record the behavioral matrix for the current rewrite.
- [x] Apply the approved Option A example-backed rewrite.
- [x] Rerun and inspect the unchanged matrix after Option A.
- [ ] Run deterministic, task-guidance, link, preparation, and build checks.
- [x] Record dated evidence and update live requirement state.
- [x] Commit the verified Option A checkpoint.
- [x] Create versioned general and root guidance candidate sources.
- [x] Create the shared comprehensive specific-rule candidate.
- [x] Draft the split generic/specific candidate test plan.
- [x] Record the five-process-per-provider execution limit.
- [x] Obtain review of the candidate wording, version layout, and test plan.
- [x] Move candidate sources beside the documentation-standard tests.
- [x] Give the fixture path, test plan, review, and deterministic test explicit
  destination-terminology names.
- [x] Add the defined-context wording family.
- [x] Implement deterministic candidate compilation.
- [x] Remove Git-revision coupling from the compiler and tests.
- [x] Compile the checkpoint and ten complete candidate fixture roots.
- [x] Add deterministic compiler, manifest, pairing, and example checks.
- [x] Complete semantic review of every compiled root and pairwise diff.
- [ ] Obtain independent human review of the compiled fixtures.
- [x] Add the focused inherited-terminology remediation scenario.
- [x] Run and record all generic-only candidates.
- [x] Run and record all comprehensive-specific candidates.
- [x] Repeat the strongest candidates across selected reasoning efforts.

#### Clean-branch migration and revised evaluation

- [ ] Wait for the documentation-guide-rewrite worktree's pending
      runner-fidelity changes to be committed and record the exact structural
      base commit.
- [ ] Create the proposed independent worktree and
      `task/20260918-destination-terminology-guidance` branch from that clean
      structural base.
- [ ] Create Subtask 075 in the new structure and add it to the parent task.
- [ ] Record the carry-forward, recreate, and leave-behind inventory before
      copying any old-branch material.
- [ ] Reserve Tests 30–35, `DOCGUIDE-007`, `DOCVAL-011`–`DOCVAL-013`,
      `DOCAGENT-003`–`DOCAGENT-004`, and Subtask 067 for their new-structure
      owners.
- [ ] Add `DOCGUIDE-008`–`DOCGUIDE-009`, `DOCAGENT-002`, `DOCFLOW-007`,
      `DOCVAL-014`, and `DSEVAL-004` to the correct reusable, integration, and
      suite-owned requirement ledgers.
- [ ] Recreate active terminology Tests 36–38 under the suite-owned scenario
      paths and preserve the old Test 30–32 mapping only in historical reports.
- [ ] Recreate abstract-specific and explicit-contexts-specific as central
      candidate bundle overlays with paired full-guide inputs; add
      file-centered only if it remains diagnostically useful.
- [ ] Move the September 16 reports into the maintainer evaluation-results
      structure with a concise interpretation note; do not copy old compiled
      roots or the task-local compiler.
- [ ] Make Test 13 prevention-only by removing progress labels from its initial
      user documentation.
- [ ] Replace autonomous removal Test 32 with Test 38's no-mutation,
      confirmation-seeking first response.
- [ ] Add and calibrate the structured destination-terminology semantic
      evaluator and accepted response anchors.
- [ ] Verify every producer uses the common production Crystal Lattice runner,
      matching model-family tools, compiled workspace AGENTS, and conditional
      canonical task guidance; label direct injection as diagnostic only.
- [ ] Run the revised structural baseline and smallest useful candidate matrix
      without rerunning unrelated requirement-quality/root matrices.
- [ ] Freeze revised producer and semantic results with source hashes and
      parser-repair, compilation, and instruction-delivery provenance.
- [ ] Select and apply the final public guidance.
- [ ] Obtain human review.

### Requirement verification

| Requirement group | Acceptance evidence |
|---|---|
| New-label prevention (`DOCGUIDE-008`) | Revised Test 13 and Tests 36–37 begin without the held-out label in the destination, then demonstrate that prompt/task terminology is not introduced into user documentation, specification records, source, or tests while explicit and established names remain intact. |
| File-role applications (`DOCGUIDE-008`) | Source inspection and scenario outputs demonstrate defined task wording, descriptive complete record references, behavior-based code/test names, self-contained developer documentation, and user documentation independent of internal records. |
| Existing-wording authority (`DOCGUIDE-009`) | Test 38 starts with an existing ambiguous label, leaves the workspace unchanged on the first turn, and receives deterministic plus calibrated semantic evidence that the agent notices the concern, recommends a destination-appropriate change, and asks focused confirmation. |
| Portable root guidance (`DOCAGENT-002`) | The accepted portable Documentation section contains the concise rule, compiles through the Crystal Lattice target, and is observed through the production system-message path with exact source, compilation, and delivery provenance. |
| Task guidance (`DOCFLOW-007`) | Canonical and bundled v7 guidance match through `tasks/20260728-package-local-documentation-standard/068-task-guidance-specification-alignment.md`; generated task files define retained conversational terms and use descriptive full references without reproducing the complete public guide. |
| Crystal Lattice behavioral validation (`DOCVAL-014`) | Revised prevention and existing-wording producers compare the current structural baseline and selected candidates across the approved profiles and efforts without rerunning unrelated matrices; dated interpretation preserves failures, passing controls, and historical mapping. |
| Suite producer and semantic contract (`DSEVAL-004`) | Tests 13 and 36–38 use the common production runner, exact compilation and delivery provenance, repeat-pinned deterministic producer records, and a separately versioned Test 38 judge whose schema and repairs validate before its findings count as supporting evidence. |
| Minimal growth | Measured initial net additions remain below 20% for every touched guidance file, and any later expansion is linked to repeated paired failures. |

### Additional implementation verification

- Confirm the project-independent guide remains free of Crystal Lattice paths
  and package names.
- Confirm the Crystal Lattice conventions do not become a second copy of the
  project-independent terminology rules.
- Inspect specification paths, document headings, task headings, function
  names, test filenames, test names, comments, requirement evidence labels,
  and user/developer prose in representative outputs.
- Confirm a term that is an established domain concept in one fixture is not
  rejected merely because the same word was source-local in another.
- Confirm exact user-requested names remain unchanged in the control case.
- Confirm the evaluation workspace and shell cannot read sibling worktrees
  before treating model output as guidance evidence.