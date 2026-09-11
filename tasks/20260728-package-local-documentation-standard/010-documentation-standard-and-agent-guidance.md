Parent Task: tasks/20260728-package-local-documentation-standard/000-main.md

Specification:
`maintainer/specifications/documentation-and-specification-standard/index.md`

Requirement IDs:
`DOCMETA-001`–`DOCMETA-003`, `DOCGUIDE-001`–`DOCGUIDE-006`,
`DOCLOCAL-001`–`DOCLOCAL-002`, `DOCAGENT-001`, `DOCVAL-010`

Baseline requirement and behavioral evidence remains under
`DOCGEN-001`–`DOCGEN-010` and `DOCREP-001`–`DOCREP-007` until the replacement
guidance is delivered and the superseded rows are closed explicitly.

Related Verification:
`tasks/20260728-package-local-documentation-standard/015-agent-evaluation-framework.md`
owns `DOCVAL-005`–`DOCVAL-009` behavioral evidence. Its remaining framework
and matrix refinements are non-blocking for drafting the replacement guidance.
The approved semantic and reasoning-effort follow-up for `DOCVAL-010` remains
pending until this outline is approved.

# Documentation Standard and Agent Guidance

Replace the first documentation-standard implementation with one concise
project-independent guide, one Crystal Lattice addendum, and shorter agent
routing. Emphasize how to write useful documentation, requirements, testing
strategies, and verification while keeping every illustrated file optional.

## Requirements checklist

- [x] The maintainer specification and live requirements record the approved
  September 11 redesign without repurposing the first implementation's stable
  requirement IDs.
- [ ] `docs/development/index.md` routes directly to one project-independent
  guide and one Crystal Lattice addendum.
- [ ] The combined public guidance and root documentation section fit within a
  focused review of at most 30 normal Kindle pages.
- [ ] The project-independent guide begins with an annotated default structure
  and makes clear that every shown file and directory is optional.
- [ ] File roles are introduced once with practical writing guidance, usual
  content, exclusions, and concrete verified examples.
- [ ] Specifications, requirements, tasks, optional progress, and early
  user-documentation drafts have concise, non-duplicated responsibilities.
- [ ] Requirements contain only approved necessary outcomes or constraints,
  and each row records only direct primary evidence.
- [ ] Testing guidance covers test-layer choice, important production
  crossings, non-contractual implementation details, intentional exclusions,
  and focused completion reporting.
- [ ] The Crystal Lattice addendum contains only local paths, package and
  cross-package placement, plugin guidance, maintainer boundaries, publication,
  migration, and compatibility rules.
- [ ] Specification titles and paths describe capabilities rather than using
  portability as a mandatory naming convention.
- [ ] Root `AGENTS.md` contains an approximately 200–300 word summary and routes
  to the two public guidance documents.
- [ ] Behavioral validation tests abstract rule understanding, requirement
  restraint across supported reasoning efforts, testing balance, and focused
  verification reporting without coaching literal forbidden words.
- [ ] Human review confirms the final guidance is clear, coherent,
  proportionate, scannable, and within the approved review-size limit.

## Supporting details

### Approved September 11 redesign

The user approved:

- two substantive public guidance files plus a short development index;
- a flattened public structure at `docs/development/documentation.md` and
  `docs/development/crystal-lattice-documentation.md`;
- an annotated structure and file-role explanation before abstract rules;
- optional documentation and specification files at every level;
- one-page and README-only outcomes when they fit the work;
- practical authoring, examples, requirements, evidence, testing, and
  verification guidance;
- positive writing guidance instead of literal forbidden-word lists;
- package-local specifications and capability-named cross-package
  specifications;
- optional concise progress notes in specifications;
- branch-only `Not implemented` markers for target user documentation drafted
  before implementation;
- optional `testing-strategy.md` when risk or layer complexity justifies it;
- semantic behavioral tests using held-out language and multiple supported
  reasoning efforts.

The original four-page implementation and its behavior results remain useful
baseline evidence. They are not the target of the current plan.

### Scope preserved from the parent task

- Package documentation remains local by default.
- Root development documentation remains limited to repository-wide guidance
  and cross-package behavior with no sensible package home.
- `plugins/docs/` remains the shared plugin-authoring domain.
- `maintainer/` remains non-public guidance-maintenance material.
- Authored sources remain distinct from prepared and built documentation.
- Adoption remains incremental; this redesign does not trigger a broad package
  rewrite or reconstruction of undocumented behavior.

## Implementation Notes

- August 5, 2026: Created the approval package before execution-plan approval:
  - `maintainer/README.md`;
  - the unified documentation/specification meta-specification;
  - its live requirements covering generic and repository-specific outputs;
  - parent/subtask mappings to the new requirement IDs.
- The user approved the meta-specification and bootstrap requirements on
  August 5, 2026. `DOCMETA-001`–`DOCMETA-003` are human verified.
- The user approved execution of subtask 010 on August 5, 2026, including the
  package-entry-point ownership correction assigning Core/application entry
  points to subtasks 030/040.
- Authored the reusable documentation/specification standards and the Crystal
  Lattice repository policy under `docs/development/`.
- Expanded the development hub and updated root `AGENTS.md`, README, and docs
  index routing.
- Static checks found no project-specific terms in the reusable standard pages
  and no broken relative links introduced by 010.
- `python docs_site/scripts/prepare_mkdocs_site.py` and normal `mkdocs build`
  completed successfully. The build reported the six new standards/policy pages
  as omitted from explicit nav; `DOCPUB-005` and subtask 060 own that planned
  navigation update. Existing griffe/autoref warnings remain outside 010.
- No docs-site navigation changes, content migrations, or maintainer-tool
  relocations have been implemented by 010.
- The first implementation plan was approved and executed. The September 11
  redesign plan later superseded it and is `Draft`.
- August 14, 2026: Reviewed the committed subtask 015 changes. The
  documentation meta-specification and applied guidance now also define
  audience/context boundaries, document-reference directions,
  observable-example accuracy, blocked-workflow boundaries, and
  baseline-first behavioral verification.
- Subtask 015 added `DOCGEN-006`, `DOCGEN-007`, `DOCREP-006`, and
  `DOCVAL-005`–`DOCVAL-008`, plus nineteen behavioral consumers over nine
  reusable seeds. This task now maps the new output requirements; 015 continues
  to own behavioral evidence.
- The user's August 14, 2026 direction makes 015's remaining calibration,
  complete one-model matrix, and framework provenance review explicitly
  non-blocking for 010 and later subtasks.
- Refreshed 010 verification against the current committed guidance:
  - generic-standard project-specific term scan passed;
  - relevant relative links resolve; the only reported missing source paths are
    the two pre-existing prepared-site links in `docs/index.md`;
  - `git diff --check` passed for the current standards/specifications;
  - docs-site preparation and normal MkDocs build completed;
  - all standards/repository pages are present in prepared output;
  - `maintainer/` and AGENTS remain excluded from public output;
  - explicit navigation warnings remain assigned to subtask 060, while the
    existing griffe/autoref warnings remain outside 010.
- August 19, 2026: The user approved a terminology follow-up after observing
  that agents copied the standards' generic “artifact” wording into
  specification indexes. Added `DOCGEN-010`, replaced the umbrella term with
  concrete document/file/work-item terminology in the governing specification
  and applied guidance, corrected existing `Artifacts:` specification-index
  headings, and extended Test 21 plus deterministic guidance checks.
- At the user's direction, no subtask 015 deterministic or real-model test was
  run for this follow-up. `DOCGEN-010` and the expanded `DOCVAL-005` coverage
  remain unverified until the recorded focused commands are executed.
- Read-only inspection of all five preserved August 18 Test 21 runs found that
  the GLM baseline, two GLM candidates, and two GPT candidates all generated
  either `## Artifacts` or `## Specification artifacts`. These prior results
  demonstrate the existing behavioral gap, but they cannot verify the revised
  guidance because they predate it.
- Non-test verification for the terminology follow-up completed:
  - static searches found no remaining generic umbrella phrases in the
    governed guidance or documentation meta-specification;
  - no inbound Markdown links retain the renamed generic headings;
  - Python compilation and Ruff checks pass for the changed deterministic and
    behavioral test definitions;
  - changed-page relative-link inspection reports only the two pre-existing
    site-relative links in `docs/index.md`;
  - docs-site preparation and normal MkDocs build complete with the known
    navigation and griffe/autoref warnings;
  - no pytest or real-model command was executed.
- August 19, 2026: The user approved the terminology-section placement.
  The reusable documentation standard now owns the full authored-content rule
  after its document-role table, while the specification standard applies it
  after defining the proportional specification file set. The one-off rerun
  instructions remain in the user handoff rather than persistent evaluation
  documentation.
- September 5, 2026: The user explicitly requested that documentation rules
  remain default agent guidance rather than prevent a different user-directed
  commit order. Added the concise exception to the generic standard, Crystal
  Lattice policy, root `AGENTS.md`, governing specification, and `DOCGEN-002`.
  Test 15 remains a publication-accuracy scenario and now clarifies that its
  prompt does not request a different commit order.
- September 11, 2026: Human review rejected the first implementation as too
  long, repetitive, scattered, terminology-heavy, difficult to navigate, and
  shaped too closely around literal behavior-test vocabulary. The user
  approved the two-file redesign, optional file structure, branch-only
  pre-implementation user-doc markers, and risk-triggered optional testing
  strategy. Created branch `task/20260728-documentation-guide-rewrite` and
  worktree
  `/Users/ferenci84/Dev/Mine/ai-agent-platform-worktrees/20260728-documentation-guide-rewrite`
  from committed `develop` HEAD `f81f3632`; the original dirty worktree and its
  unrelated changes remain untouched. The governing specification and new
  redesign requirements were updated before rewriting public guidance.
- September 11, 2026: The user approved the detailed redesign plan and
  clarified that UI JSON keys are an example rather than the testing rule.
  Generalized the target to avoid exact assertions about any value, structure,
  ordering, or internal call that is outside the required public, persisted,
  interoperability, or otherwise approved behavior.

## Prior execution plan

Status: Superseded on September 11, 2026

Subtask 010 establishes the vocabulary, ownership rules, and root routing that
later assembly, migration, contributor-workflow, and task-guidance subtasks
consume. It does not migrate the legacy Core/application/plugin documents,
change MkDocs package assembly, create `CONTRIBUTING.md`, or modify
`TASKS-v7`.

The repository already has active cross-package specifications under
`docs/development/specifications/` and package implementation documentation
under several `<package>/docs/development/` directories. The work must preserve
those documents and make the new standard describe their relationship rather
than replacing or mass-normalizing them.

### 1. Preserve the current baseline and establish boundaries

1. Treat the existing `docs/development/index.md` as an active specifications
   index, not an empty file to replace.
2. Preserve the current specification trees for notifications, action
   displays, application runtime reload, and Sessions actions.
3. Use current package development indexes as evidence for the intended
   distinction:
   - root cross-package specifications define portable behavior;
   - package development docs explain how one implementation satisfies those
     contracts without redefining them.
4. Do not rewrite existing specifications to match the new template in this
   subtask. Apply the standard prospectively and on touch.
5. Leave these downstream areas to their owning subtasks:
   - package docs registration and prepared-site copying: 020;
   - Core package entry points and Core docs migration: 030;
   - application package entry points and plugin docs migration: 040;
   - navigation/public URL compatibility: 060;
   - `CONTRIBUTING.md`: 065;
   - canonical/bundled `TASKS-v7`: 068.

### 2. Expand the root development index into a hub

Update `docs/development/index.md` without removing its current specification
links.

The page should remain short and contain:

1. A brief explanation that root development docs own repository-wide
   standards and genuinely cross-package contracts.
2. A **Standards** section linking to:
   - `standards/index.md`;
   - `repository/index.md`.
3. A **Cross-package specifications** section preserving the current
   notifications, action-display, runtime-reload, and Sessions-action links.
4. A short pointer explaining that implementation-specific details live under
   the owning package's `docs/development/`.
5. No manually maintained inventory of every package document; package/site
   discovery belongs to later assembly and navigation work.

### 3. Write the reusable documentation standard and repository policy

Create:

- `docs/development/standards/index.md`;
- `docs/development/standards/documentation.md`;
- `docs/development/repository/index.md`;
- `docs/development/repository/documentation.md`.

The generic documentation page is package-neutral and reusable. The repository
page maps it to Crystal Lattice package profiles, paths, shared plugin docs,
agent guidance, site assembly, and migration behavior.

Together they should cover:

1. **Purpose and core rules**
   - author docs beside the owning package;
   - reserve root docs for repository-wide guidance and cross-package
     contracts;
   - never edit `docs_site/prepared/` or `docs_site/dist/`;
   - prefer incremental adoption over filler.
2. **Package profiles**
   - public package/SDK/application/service;
   - small plugin or internal package;
   - shared documentation domain;
   - repository tooling/site support where README plus targeted development
     docs is sufficient.
3. **Documentation responsibilities**
   - README;
   - AGENTS;
   - docs index;
   - user quickstart and other user docs;
   - development index and internals;
   - optional/generated reference.
4. **Ownership decision guide**
   - package-visible behavior belongs with the package;
   - implementation internals belong under that package's development docs;
   - a portable contract spanning multiple packages may live under root
     development specifications;
   - generated-site implementation belongs under `docs_site/`.
5. **Canonical target tree**
   - preserve the approved tree from the parent task;
   - distinguish required, conditional, and optional files.
6. **Authoring and publication boundary**
   - package-local files are canonical;
   - the explicit registry and staging behavior will be implemented by 020;
   - AGENTS is operational guidance and is not public site content by default;
   - generated reference inputs and outputs must not become competing sources.
7. **Adding or changing documentation**
   - update the owning package;
   - add a package index/quickstart only when the profile and available content
     justify them;
   - update links and relevant build inputs;
   - validate examples and claims proportionally.
8. **Moving existing documentation**
   - establish ownership first;
   - move rather than copy full authored content;
   - preserve old public URLs separately through 060;
   - defer uncertain pages instead of reconstructing them.
9. **Adoption on touch**
   - existing packages remain valid while migration is incomplete;
   - no mass placeholder creation;
   - no requirement to retrofit every historical document in this subtask.
10. **Initial repository classification in the repository policy**
    - identify Core and application as public package profiles;
    - identify shared frontend packages and mobile/desktop/bridge/cloud as
      public package/application profiles;
    - identify plugin packages as README-first with inherited
      `plugins/AGENTS.md` by default;
    - identify `plugins/docs/` as a shared documentation domain;
    - make clear that exact public-site registration is owned by 020.

Use tables and compact examples where they improve scanning, but do not turn
the page into an exhaustive package inventory.

### 4. Write the reusable specification standard and repository policy

Create:

- `docs/development/standards/specifications.md`;
- `docs/development/repository/specifications.md`.

The generic page defines the reusable target-spec/live-requirements model. The
repository page maps it to package-local paths, `tasks/`, `AGENTS.md`,
`TASKS-v7`, requirement evidence, and validation.

Together they should document:

1. **When durable specifications are needed**
   - substantive, durable, cross-package, compatibility-sensitive,
     security-sensitive, persisted-data, or public-contract changes;
   - small/local changes may remain task-only.
2. **Default location**
   - package-local
     `<package>/docs/development/specifications/<feature-slug>/`;
   - root `docs/development/specifications/<feature-slug>/` only for genuinely
     cross-package portable behavior without an honest single-package owner.
3. **Specification document roles**
   - `index.md`: scope, links, ownership, and related tasks/specs;
   - `product-spec.md`: problem, users, user-visible behavior, goals,
     non-goals, acceptance examples;
   - `technical-spec.md`: architecture, contracts, data, compatibility,
     migration, failure behavior, security, rollout, verification;
   - `requirements.md`: stable normalized outcomes and evidence;
   - `decisions/NNNN-<slug>.md`: material architecture/design decisions.
4. **Proportional specification file set**
   - the full set is not mandatory for every change;
   - omitted files should be obviously unnecessary from the index/scope,
     not represented by empty placeholders.
5. **Target versus live state**
   - the specification describes the intended target;
   - the specification may temporarily differ from implementation;
   - requirements track live implementation, verification, documentation, and
     evidence;
   - the specification is not evidence that behavior is currently available.
6. **Simple spec-first workflow**
   - small changes update the spec first and normally commit it with the code
     or in the immediately preceding commit;
   - new capabilities create the spec and requirements before implementation;
   - major changes use the same workflow unless a separate target version or
     change spec materially improves clarity;
   - no one version-directory format is mandatory.
7. **Approval and progress**
   - task files track approval by default;
   - specs do not require a lifecycle/status field;
   - domain-specific specs may define custom approval/tracking rules;
   - temporary progress blocks are used only when implementation will span
     more than one commit and target/current divergence is confusing;
   - temporary progress links the task and requirement IDs and is removed when
     all relevant requirements are verified.
8. **Requirement IDs and traceability**
   - stable feature prefix plus sequence;
   - do not recycle accepted IDs;
   - implementation, verification, and documentation states remain separate;
   - evidence may include tests, docs, tasks, PRs, and commits;
   - commit evidence is added when it exists, not predicted.
9. **Relationship to task files**
   - specifications own target behavior/design;
   - requirements own live outcome/evidence tracking;
   - tasks own approval, execution scope, plans, dependencies, findings, and
     completion;
   - avoid divergent requirement paraphrases and duplicated plans.
10. **Relationship to current documentation**
    - public user docs describe current supported behavior;
    - implementation/maintainer docs describe current implementation;
    - either may be edited first in the working tree, but new claims are
      committed with the code that makes them true;
    - future or target-only behavior remains in specifications and
      requirements, not current guides.
11. **Relationship to verification**
   - acceptance/contract tests may reference requirement IDs;
   - ordinary low-level tests need not;
   - machine-readable contracts and examples should be tested directly where
     practical;
   - manual verification is recorded only when a human performs or confirms
     it;
   - Gherkin remains optional.
12. **Living target changes**
   - update specs when implementation discoveries change the accepted target;
   - requirement changes still require approval;
   - use decision records for material design changes;
   - use Git history as the default record for ordinary spec evolution;
   - use explicit target versions only when a major change would otherwise be
     confusing;
   - link superseding versions/specs instead of erasing historical rationale.
13. **Compact examples**
    - include short skeletons for a specification index, requirements table,
      and ADR;
    - use the current root specification set as evidence for terminology, but
      do not copy feature-specific content into the standard.

The page should explicitly state that existing specifications are adopted
incrementally. Current variations, such as a missing product spec or evidence
recorded below rather than inside a requirements table, do not require a mass
rewrite in 010.

### 5. Update root agent routing

Update `AGENTS.md` so it stays concise while the new pages carry explanation.

1. Add the approved **Documentation ownership and workflow** section, adapted
   to current paths.
2. Keep operational rules in AGENTS:
   - start with README, nearest AGENTS, and docs index;
   - user versus development documentation placement;
   - root cross-package exception;
   - generated-output prohibition;
   - specification location and proportional use;
   - stable requirement IDs and task/spec separation;
   - update docs/specs/evidence with behavior;
   - do not invent baselines through broad reconstruction.
3. Link to the repository-policy and generic-standard indexes.
4. Replace explanatory or obsolete documentation-maintenance detail with links
   to the standards, while preserving architecture, package ownership, and
   test commands still needed directly by agents.
5. Update the docs build commands to the current `docs_site` preparation/build
   workflow rather than the obsolete root-level `mkdocs build` shorthand.
6. Generalize the **When to update docs** section around the owning package and
   relevant specifications. Do not point agents at future moved paths before
   subtasks 030/040 complete.
7. Do not add the `CONTRIBUTING.md` route in 010; subtask 065 owns it after that
   file exists.
8. Do not modify `TASKS-v7`; subtask 068 owns developer-message task guidance.

### 6. Update repository documentation entry points

1. Update `docs/index.md` so its development link describes a hub containing
   standards and cross-package specifications, not only the currently listed
   feature specifications.
2. Update the root README documentation section to link:
   - the development hub;
   - reusable standards;
   - repository policy.
3. Correct the README's docs build commands to use
   `docs_site/requirements.txt`, the preparation script, and the
   `docs_site/` MkDocs configuration.
4. Preserve all current product/user documentation links; later migration and
   compatibility updates belong to 030, 040, and 060.
5. Do not edit `docs_site/mkdocs.yml` navigation in this subtask. Root-index
   links make the standards reachable, while 060 owns final navigation and
   public URL treatment.

### 7. Keep package entry-point creation with migration owners

Recommended ownership correction:

- 010 classifies package profiles and defines the entry-point contract.
- 030 creates/refines `core/python/AGENTS.md`, `docs/index.md`, and
  `docs/quickstart.md`.
- 040 creates/refines `application/python/AGENTS.md`, `docs/index.md`, and
  `docs/quickstart.md`.
- Later package adoption occurs on touch or through separately scoped work.

This avoids creating temporary links to legacy locations and then immediately
rewriting the same files in migration subtasks.

To make the subtask checklist accurately reflect this boundary, approval of
this plan should also approve replacing:

> Initial major package roots receive or refine `AGENTS.md`, `docs/index.md`,
> and `docs/quickstart.md`...

with:

> Initial major package roots are classified under the approved profiles, and
> package entry-point creation is assigned to the owning migration subtasks.

The parent-task outcome remains unchanged.

### 8. Verification

Documentation-only verification:

1. Run `git diff --check`.
2. Search the changed files for:
   - contradictory root/package ownership rules;
   - direct instructions to edit `docs_site/prepared/` or `docs_site/dist/`;
   - duplicated or conflicting specification/task definitions;
   - references to future files not created by 010.
3. Validate relative links in:
   - `docs/development/index.md`;
   - generic standard and repository-policy indexes/pages;
   - `docs/index.md`;
   - root README;
   - root AGENTS.
4. Run:

   ```bash
   python docs_site/scripts/prepare_mkdocs_site.py
   (cd docs_site && mkdocs build)
   ```

5. Inspect the prepared and built copies of the development hub and both
   standards pages.
6. Record build warnings and distinguish pre-existing navigation/reference
   warnings from warnings introduced by 010. Global strict-mode cleanup is not
   required here.
7. Ask for human review of:
   - package-profile clarity;
   - the owner decision guide;
   - specification/task separation;
   - requirements/evidence terminology;
   - audience/context and prohibited-reference boundaries;
   - observable first-success behavior;
   - blocked-workflow and completion-honesty rules;
   - whether root AGENTS remains concise enough for recurring agent context.
8. Leave requirements depending on that human review incomplete until the
   review is confirmed.

### 9. Approved terminology follow-up

1. Update the documentation meta-specification and live requirements first,
   adding a stable requirement for concrete terminology.
2. Replace generic umbrella wording in reusable standards, repository policy,
   root agent guidance, review routing, and existing specification indexes.
3. Preserve established technical uses such as build, release, test,
   evaluation, provider-native, and literal `artifacts/` terminology.
4. Synchronize behavioral scenario wording and extend the existing
   specification-creation scenario so it rejects `Artifacts:` headings and
   equivalent generic phrases.
5. Add a deterministic check covering the governed guidance and corrected
   specification indexes.
6. Keep verification pending without running subtask 015 tests in this change,
   and provide exact deterministic and baseline/candidate rerun commands as a
   one-off user handoff rather than persistent package documentation.

### Implementation decisions and open questions

- **Approved parent decisions applied:** package profiles, README/docs-index
  precedence, non-public AGENTS, proportional target specifications,
  requirements-owned live tracking, task-owned approval, traceability
  granularity, generated-output boundaries, and adoption without filler.
- **Recommended ownership decision requiring plan approval:** 010 defines and
  classifies package entry points, while 030/040 create the Core/application
  files. This removes an overlap without changing the parent-task outcome.
- **Root specification exception:** portable cross-package contracts may remain
  in root `docs/development/specifications/`; package-local specifications
  remain the default.
- **Existing-spec migration:** do not normalize existing specifications in
  bulk. Apply the standard prospectively and when a specification is touched.
- **Templates:** use compact inline skeletons in the standard; do not add a
  separate template package or generator in 010.
- **Navigation:** do not change MkDocs nav; 060 owns final navigation and URL
  compatibility.
- **Contributor/task guidance:** do not create `CONTRIBUTING.md` or modify
  `TASKS-v7`; 065 and 068 own those outputs.
- **Behavioral verification:** 015 supplies supporting `DOCVAL-005`–`DOCVAL-008`
  evidence. Its remaining refinements do not block 010 or later subtasks.
- No other requirement questions are open.
- If a package cannot be confidently classified using current manifests,
  READMEs, and ownership, record it for the deferred inventory instead of
  inventing a classification.

### Documentation

- `docs/development/index.md`
- `docs/development/standards/index.md`
- `docs/development/standards/documentation.md`
- `docs/development/standards/specifications.md`
- `docs/development/repository/index.md`
- `docs/development/repository/documentation.md`
- `docs/development/repository/specifications.md`
- `maintainer/README.md`
- `maintainer/specifications/documentation-and-specification-standard/*`
- root `AGENTS.md`
- `docs/index.md`
- root `README.md`

### Task checklist

- [x] Create the simplified maintainer boundary and unified meta-specification.
- [x] Create live requirements for generic and repository-specific outputs.
- [x] Map the parent task and subtasks to meta-specification requirement IDs.
- [x] Preserve existing cross-package specifications and package implementation docs.
- [x] Expand the root development index into a standards/specifications hub.
- [x] Write the documentation structure standard.
- [x] Write the specification-driven development standard.
- [x] Update root agent routing.
- [x] Classify initial package profiles.
- [x] Update root README and docs index links/build guidance.
- [x] Run documentation preparation/build and inspect warnings.
- [x] Map subtask 015 additions and refresh static/build evidence against the
  current committed guidance.
- [x] Apply the approved concrete-terminology follow-up to the specification,
  guidance, existing indexes, scenarios, and test definitions.
- [ ] Run the new deterministic terminology check and focused Test 21
  baseline/candidate evaluation.
- [ ] Obtain human review of clarity and agent-context concision.

### Requirement verification

| Requirement group | Acceptance evidence |
|---|---|
| Development hub | `docs/development/index.md` preserves all active cross-package specification links and exposes reusable standards and repository policy with a concise ownership explanation. |
| Documentation structure | Human inspection confirms the generic page is package-neutral, the repository overlay contains local mappings/exceptions without generic duplication, and document roles, package profiles, ownership, generated-output, migration, and incremental-adoption rules are explicit. |
| Specification workflow | Human inspection confirms target-state specification semantics, requirements-owned live tracking, task-owned approval, simple spec-first commits, optional major-version separation, stable IDs, evidence, ADRs, current-doc coupling, and temporary multi-commit progress rules. |
| Audience and boundary behavior | Human inspection confirms documents use audience-appropriate context, internal provenance does not leak into consumer docs, generated-source and blocked-workflow boundaries remain intact, and observable first-success claims are concrete and current. |
| Concrete terminology | Static inspection confirms the standards, repository policy, agent guidance, and specification indexes name documents, files, specifications, requirements, work items, tests, code, and generated output directly; focused deterministic and Test 21 reruns remain pending by user direction. |
| Behavioral evidence | Subtask 015 maps every `DOCGEN-*` and `DOCREP-*` requirement to executable consumers; this evidence supplements rather than replaces human review and its remaining refinements are non-blocking. |
| Existing specifications | Diff inspection confirms current feature specifications were preserved and no mass conformance rewrite or unsupported claims were introduced. |
| Agent guidance | Root `AGENTS.md` routes agents to package docs and full standards without reproducing the long explanations or preempting `CONTRIBUTING.md`/`TASKS-v7` work. |
| Package profiles | The structure standard classifies initial package categories and assigns Core/application entry-point creation to 030/040 after the ownership correction is approved. |
| Repository entry points | Root README and `docs/index.md` link to the new hub/standards and contain current docs-site build commands. |
| No filler/reconstruction | No empty package trees, placeholder quickstarts, copied legacy pages, or broad code-derived baseline docs are added. |
| Buildability | Preparation and normal MkDocs build complete; links to the new pages work; any warnings are classified as pre-existing or introduced. |

### Additional implementation verification

- Check all new relative links from root README, root AGENTS, and root docs.
- Confirm the standard preserves all approved decisions from the parent task.
- Search for contradictory root documentation-maintenance guidance and update
  or explicitly retain it.
- Inspect the rendered standards for heading depth, table readability, and
  concise examples.
- Confirm generated prepared/dist files remain ignored and are not treated as
  authored changes.

## Execution plan

Status: Approved

This plan replaces the first four-page documentation-standard implementation
with two substantive public guidance files and a shorter root agent section.
It preserves package-local documentation, existing specifications, publication
infrastructure, and bounded migration ownership. It does not reconstruct
package documentation, change product behavior, modify `TASKS-v7`, or complete
the navigation/compatibility work owned by subtask 060.

The target review set is:

- `docs/development/documentation.md`: 1,600–2,000 words;
- `docs/development/crystal-lattice-documentation.md`: 900–1,200 words;
- the root `AGENTS.md` documentation section: 200–300 words;
- `docs/development/index.md`: fewer than 150 words excluding the existing
  cross-package specification list.

The complete human-review bundle should normally remain between 3,000 and
3,600 words and fit within 30 Kindle pages.

### 1. Preserve the baseline and route compatibility

1. Treat the current four substantive pages and subtask 015 results as baseline
   evidence, not text to edit line by line.
2. Write the two replacement pages from the approved outline, copying a current
   sentence only when it is already the clearest expression of the retained
   idea.
3. Update authored inbound links to the new pages.
4. Record these old/new public mappings for subtask 060:

   | Existing route | New destination |
   |---|---|
   | `docs/development/standards/documentation.md` | `docs/development/documentation.md` |
   | `docs/development/standards/specifications.md` | the specification section in `docs/development/documentation.md` |
   | `docs/development/repository/documentation.md` | `docs/development/crystal-lattice-documentation.md` |
   | `docs/development/repository/specifications.md` | the specification section in `docs/development/crystal-lattice-documentation.md` |
   | `docs/development/standards/index.md` | `docs/development/index.md` |
   | `docs/development/repository/index.md` | `docs/development/index.md` |

5. Delete the old pages as authoritative guidance in the same change that
   updates their inbound links. If public compatibility is required before
   subtask 060 can provide redirects, use the smallest clearly
   non-authoritative compatibility pages and exclude them from the human review
   set.
6. Do not copy the uncommitted human-review files from the original dirty
   worktree into this branch; create a new focused review only after the
   replacement pages exist.

### 2. Rewrite the development index

Keep `docs/development/index.md` as a short router:

1. One sentence explaining that the section contains development guidance and
   specifications shared across the repository.
2. Direct links to:
   - **Documentation and specification guide**;
   - **Crystal Lattice documentation conventions**.
3. Preserve the current cross-package specification links.
4. Explain in one sentence that package-specific user and developer
   documentation remains with the package.
5. Remove the intermediate Standards and Repository Policy navigation concepts.

### 3. Write `docs/development/documentation.md`

Use the title **Documentation and specification guide**. Do not describe the
page as reusable, generic, portable, a standard, or a meta-specification.

#### 3.1 Opening and default structure

Open with a brief purpose statement followed immediately by one annotated
structure:

```text
README.md
AGENTS.md
docs/
├── index.md
├── quickstart.md
├── <user-topic>.md
├── development/
│   ├── index.md
│   ├── <developer-topic>.md
│   └── specifications/
│       └── <capability>/
│           ├── index.md
│           ├── product-spec.md
│           ├── technical-spec.md
│           ├── requirements.md
│           ├── testing-strategy.md
│           └── decisions/
└── reference/
```

The annotation immediately states that every line is optional. A project may
use:

- one existing README;
- one standalone documentation or specification page;
- an index and one child page;
- one specification plus requirements;
- separate product, technical, requirements, testing, and decision files when
  their separation improves review.

The guide does not introduce package profiles. For a single-package
repository, the repository root is simply the package location.

#### 3.2 Explain file roles once

Use one compact table followed by short practical subsections where needed.
Each role states:

- who reads it;
- what it normally contains;
- what does not belong there;
- when a separate file helps;
- one small example where the role is otherwise ambiguous.

Cover:

- README;
- AGENTS;
- index;
- quickstart;
- user documentation;
- developer documentation;
- specification;
- requirements;
- testing strategy;
- reference;
- decision record.

Do not redefine these roles later. Later sections link back to the role or use
its established name.

README guidance emphasizes purpose, installation, first successful use, and
routes. Quickstart guidance requires a complete path and a concrete result when
the behavior is observable. User documentation covers available use,
configuration, concepts, recipes, and troubleshooting. Developer documentation
covers current architecture, code entry points, debugging, testing, and
maintenance.

#### 3.3 Explain how to write useful pages

Concentrate the cross-cutting writing rules here:

1. Write for the reader of this page.
2. Introduce terms before using them.
3. Prefer concrete examples and observable outcomes.
4. Verify examples against current code or tests.
5. Keep one primary maintained explanation; link or summarize only what another
   reader needs.
6. Keep user and developer documentation aligned with available behavior.
7. Name the page, file, result, or output being discussed rather than relying
   on vague umbrella labels.

Do not enumerate literal forbidden words or lists of internal planning labels.
Use a single general rule: user documentation explains available behavior in
user language, while planning and implementation tracking stays in
specifications, requirements, tasks, and temporary developer notes.

#### 3.4 Explain specifications, requirements, tasks, and progress

Define the relationship once:

| Record | Responsibility |
|---|---|
| Specification | Intended behavior and important design decisions |
| Requirements | Necessary outcomes and their implementation, verification, and documentation state |
| Task | Approval, plan, execution, findings, and completion |
| User and developer documentation | Available behavior and current implementation |

Then cover:

- when a durable specification helps;
- one-page versus multi-file specifications;
- package/component placement in one short paragraph;
- package-specific refinements of broader behavior;
- specifications leading implementation;
- concise optional implementation notes in a specification when the
  target/current difference would otherwise be confusing;
- user documentation drafted before code on a development branch;
- visible `Not implemented` markers during review;
- removal of those markers before publication;
- keeping durable proposed user text with the specification when implementation
  is not ready.

Do not split the workflow into small/new/major categories. Explain the common
model and use one short example for a simple change and one for an extended
change only if necessary.

#### 3.5 Explain how to write requirements

Keep this section short and concrete:

1. A requirement states one necessary outcome or constraint.
2. If the requirement can fail while the approved task is still complete, it
   is not a requirement.
3. Implementation steps, test tasks, documentation tasks, refactors, possible
   hardening, and low-priority improvements stay in plans, supporting notes,
   questions, recommendations, or follow-ups unless their resulting outcome is
   explicitly required.
4. Higher reasoning effort may discover more useful work but does not enlarge
   the approved requirement set.
5. Stable IDs are used when durable tracking helps.
6. Implementation, verification, and documentation states remain separate.
7. The final column is `Primary evidence`.
8. A row cites the smallest direct test, human confirmation, or documentation
   reference supporting its state.
9. Shared task, pull-request, and commit references are recorded once below the
   table rather than repeated in every row.
10. Longer ID-keyed evidence notes are exceptional.

Include one good concise requirement row and one supporting idea that is
deliberately not promoted to a requirement.

#### 3.6 Explain testing strategy and verification

Lead with:

> Use the least expensive test that proves the requirement without mocking
> away the important boundary.

Cover:

- unit and component tests for local behavior;
- integration tests for meaningful crossings between real components;
- end-to-end, hosted, native, or manual checks when lower layers cannot
  represent the risk faithfully;
- exact value, structure, ordering, or internal-call assertions only when that
  detail is required behavior or part of a public, persisted, or
  interoperability contract;
- avoiding the same assertion at every layer without a reason;
- documenting important omitted tests and why;
- manual verification only when a human performs or directly confirms it.

Explain that `testing-strategy.md` is optional. Use it when important behavior
crosses layers, tests are expensive or manual, credible test approaches have
meaningful tradeoffs, or test exclusions need a durable rationale. Small work
keeps testing in its task or conversational plan.

Provide a small testing-strategy outline:

- behaviors and risks;
- selected test boundary for each;
- manual/hosted/native checks;
- tests intentionally omitted;
- unresolved verification.

Completion-report guidance requires the decisive acceptance evidence first.
Routine formatting, lint, compilation, and broad counts are grouped as
supporting checks or omitted unless they affect the result.

#### 3.7 Finish with placement, links, and generated documentation

Keep this operational section brief:

- place a page with the package or component whose behavior it explains;
- a package may contain behavior shared by several consumers when it defines
  that behavior;
- use a cross-package location only when independently maintained components
  must coordinate and no component defines the complete behavior;
- link focused pages from a nearby README or index;
- edit the maintained source of generated documentation;
- run the normal generator when in scope;
- if generation fails, leave generated output unchanged and report the
  remaining action;
- apply the structure incrementally without reconstructing undocumented
  systems.

### 4. Write `docs/development/crystal-lattice-documentation.md`

Use the title **Crystal Lattice documentation conventions**. Assume the first
guide has already defined every file role and general writing rule.

#### 4.1 Repository map

Show only the paths needed to make local decisions:

- package README, AGENTS, user docs, developer docs, specifications, and
  optional reference;
- root development index and cross-package specifications;
- shared `plugins/docs/`;
- `maintainer/`;
- documentation registry, prepared input, and built output.

Do not maintain a prose table listing every current package.

#### 4.2 Package, plugin, and cross-package placement

State:

- package-specific behavior and implementation documentation stays with the
  package;
- package-specific UX or platform behavior may have its own specification;
- `plugins/docs/` contains guidance shared by plugin authors;
- individual plugin behavior stays with that plugin;
- root cross-package specifications are used only for coordination with no
  sensible package home;
- specification names describe capabilities;
- portability may appear in scope when it is meaningful, but it is not a
  mandatory title or directory prefix.

#### 4.3 Crystal Lattice records and routing

Map:

- specifications to package, root, or maintainer paths;
- requirements to `requirements.md`;
- approval and execution to `tasks/`;
- ordinary agent routing to root and nearest package AGENTS;
- standards-maintenance routing to the maintainer specification and
  requirements.

Keep `maintainer/` to one short subsection. It is not ordinary package-user
context and is not a general shared-test location.

#### 4.4 Publication and generated documentation

Document:

- authored package/root files as maintained sources;
- `docs_site/packages.toml` as the publication registry;
- `docs_site/prepared/` and `docs_site/dist/` as generated;
- AGENTS, tasks, and maintainer material as excluded by default;
- the normal prepare/build commands;
- honest behavior when preparation fails.

#### 4.5 Migration and compatibility

Keep migration local to this addendum:

- move rather than duplicate maintained pages;
- verify only touched claims and examples;
- update inbound links and registry/navigation inputs;
- preserve published routes through subtask 060;
- defer uncertain moves rather than reconstructing broad baselines.

### 5. Reduce root `AGENTS.md`

Replace the current documentation section with approximately 200–300 words.
It should:

1. Tell agents to start with the package README, nearest AGENTS, and docs index.
2. State the package-local default and root cross-package exception.
3. Distinguish user docs, developer docs, specifications, requirements, and
   tasks in one compact paragraph.
4. State that generated documentation is changed through its maintained source.
5. Require incremental, evidence-based documentation rather than reconstructed
   baselines.
6. Route structural documentation work to:
   - `docs/development/documentation.md`;
   - `docs/development/crystal-lattice-documentation.md`.
7. Route changes to the guidance or its evaluation additionally to the
   maintainer specification and requirements.

Do not include:

- file-role detail;
- prohibited-vocabulary lists;
- reference-direction matrices;
- testing taxonomy;
- migration procedure;
- package inventory;
- repeated approval rules.

### 6. Update the specification and requirements after the public rewrite

1. Reconcile the product and technical specifications with the final wording.
2. Mark `DOCGUIDE-*`, `DOCLOCAL-*`, and `DOCAGENT-001` live states using direct
   evidence.
3. Review the first `DOCGEN-*` and `DOCREP-*` rows:
   - preserve their historical implementation and behavioral evidence;
   - mark requirements removed when their specific target was intentionally
     dropped;
   - link retained behavior to the replacement requirement rather than
     repurposing IDs.
4. Keep evidence cells short. Put shared branch/task/commit delivery references
   once below the relevant requirement group.
5. Update the parent task's wording and requirement mapping without rewriting
   unrelated completed workstreams.

### 7. Redesign behavior verification with subtask 015

Prepare the scenario changes after the two draft guidance pages are stable:

1. Preserve useful existing scenarios for generated-source behavior, routed
   reading, plugin/shared placement, and current-versus-target behavior.
2. Replace literal terminology assertions with semantic assessment of whether
   headings and prose name their actual contents.
3. Revise planning-context scenarios so candidate guidance does not enumerate
   fixture words. Use held-out terms such as phase, milestone, tranche,
   rollout, or internal status codes across variants.
4. Add a requirement-restraint scenario:
   - one approved outcome;
   - several useful but unapproved improvements;
   - the same seed and prompt at supported low, medium, and high reasoning
     efforts;
   - acceptance based on preserving approved requirements while retaining
     useful discoveries as questions or recommendations.
5. Add paired testing-strategy scenarios:
   - an over-specification case where non-contractual implementation details
     should not be frozen, using incidental UI JSON keys as one example;
   - an important server/transport/frontend crossing that must not be covered
     only by isolated unit tests.
6. Add a completion-report scenario that foregrounds decisive evidence and
   keeps routine quality checks secondary.
7. Review the existing 21-scenario matrix for redundancy after the new
   scenarios are defined. Do not retain tests merely to preserve the old
   count.
8. Present scenario contracts and the proposed model/reasoning matrix for
   approval before real-model execution.

Subtask 015 owns the evaluation implementation and model runs. Its follow-up
does not block drafting the pages, but final behavioral verification remains
open until the approved revised scenarios run.

### 8. Verify and review

Before human review:

1. Run `git diff --check`.
2. Validate relative file and heading links.
3. Confirm the project-independent page contains no Crystal Lattice names,
   paths, tooling, or maintainer-routing language.
4. Confirm the Crystal Lattice addendum does not restate complete general
   explanations.
5. Check that each file role is defined once and later usages are consistent.
6. Search for old links and conflicting four-page guidance.
7. Run documentation preparation and the normal MkDocs build.
8. Inspect the rendered pages and compatibility treatment.
9. Measure each page, the root AGENTS section, and the full review bundle
   against the approved budgets.
10. Prepare a focused review bundle containing:
    - a short change and agent-evidence summary;
    - the exact root AGENTS section;
    - the two full guidance pages;
    - the short development index.

Human review asks only whether the pages are clear, coherent, proportionate,
scannable, and appropriately concise. Objective link, structure, terminology,
and route checks are completed by the agent before the bundle is sent.

### Implementation decisions and open questions

- **Approved file structure:** `docs/development/documentation.md` and
  `docs/development/crystal-lattice-documentation.md`, routed directly from
  `docs/development/index.md`.
- **Approved optionality:** every illustrated documentation or specification
  file is conditional. One existing page, one standalone page, an index plus
  one page, or a larger tree may each be complete.
- **Approved early-doc behavior:** target-only user documentation may use a
  visible `Not implemented` marker on a development branch, but does not reach
  published current guidance by default.
- **Approved testing-strategy trigger:** `testing-strategy.md` is optional and
  justified by meaningful risk, layer crossings, expensive/manual validation,
  credible test tradeoffs, or important exclusions.
- **Approved terminology direction:** public guidance uses plain file-role
  names and positive writing rules. Maintainer terms remain inside maintainer
  material.
- **Approved specification naming:** capability names are primary;
  cross-package placement or portability does not automatically become a title
  or directory prefix.
- **Behavioral-test ownership:** subtask 015 owns revised scenario
  implementation and model execution; 010 owns the public wording and expected
  behavior.
- **Compatibility ownership:** subtask 060 owns final public redirects and
  navigation. 010 records mappings and avoids competing maintained guidance.
- No unresolved requirement question remains. Local examples and exact
  phrasing can be refined while drafting, provided they preserve this outline.

### Documentation

- `docs/development/index.md`
- `docs/development/documentation.md`
- `docs/development/crystal-lattice-documentation.md`
- root `AGENTS.md`
- root README/docs entry-point links affected by the route change
- `maintainer/specifications/documentation-and-specification-standard/`
- task 010 and the parent task
- subtask 015 scenario definitions after separate approval
- subtask 060 compatibility mapping

### Task checklist

- [x] Create the isolated redesign branch and worktree.
- [x] Record the approved two-file target in the maintainer specification.
- [x] Add new redesign requirements without repurposing baseline IDs.
- [x] Write the detailed replacement outline.
- [x] Obtain user approval of this detailed plan.
- [ ] Draft the project-independent documentation and specification guide.
- [ ] Draft the Crystal Lattice documentation conventions.
- [ ] Reduce root documentation guidance.
- [ ] Update the development index and authored inbound links.
- [ ] Apply or hand off public route compatibility.
- [ ] Reconcile specification and live requirements with the final text.
- [ ] Present revised behavior-scenario contracts for approval.
- [ ] Run static, documentation-build, and approved behavioral verification.
- [ ] Send a review bundle no longer than 30 normal Kindle pages.
- [ ] Obtain final human readability review.
- [ ] Add completion notes and update the parent task.

### Requirement verification

| Requirement group | Acceptance evidence |
|---|---|
| `DOCGUIDE-001` | Source inspection and the focused Kindle review confirm two substantive public pages, a short index, and the approved review-size limit. |
| `DOCGUIDE-002`–`DOCGUIDE-003` | The project-independent guide begins with the optional structure, defines every role once, and provides practical authoring and example guidance without Crystal Lattice context. |
| `DOCGUIDE-004` | Specification/task/requirements/current-doc responsibilities, optional progress, and branch-only early user-doc behavior are explicit and non-duplicated. |
| `DOCGUIDE-005` | Requirements examples contain only necessary outcomes and concise primary evidence; supporting ideas remain outside the requirement set. |
| `DOCGUIDE-006` | Testing guidance and examples select appropriate layers, cover important crossings, reject over-specific tests of non-contractual implementation details, record exclusions, and produce focused completion reporting. |
| `DOCLOCAL-001`–`DOCLOCAL-002` | The Crystal Lattice page maps only local paths and exceptions, preserves plugin and maintainer boundaries, and names specifications by capability. |
| `DOCAGENT-001` | The measured root section is 200–300 words and routes correctly without duplicating the full guide. |
| `DOCVAL-010` | Approved held-out-vocabulary, reasoning-effort, testing-balance, and verification-report scenarios run with preserved results and human interpretation. |

### Additional implementation verification

- Compare section-level concept coverage so no important retained rule is lost
  while removing repetition.
- Check terminology introduction order and later consistency.
- Confirm the guide reads naturally for a single-package project.
- Confirm no illustrated file is accidentally described as universally
  required.
- Verify early `Not implemented` examples cannot be mistaken for permission to
  publish unavailable behavior.
- Inspect requirement examples for outcome clarity and evidence brevity.
- Inspect testing examples for both over-testing and under-testing risks.
- Confirm old pages do not remain competing editable sources.
- Record behavior-test failures and variance without tuning public guidance to
  literal assertion vocabulary.
