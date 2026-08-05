Parent Task: tasks/20260728-package-local-documentation-standard/000-main.md

Specification:
`maintainer/specifications/documentation-and-specification-standard/index.md`

Requirement IDs:
`DOCMETA-001`–`DOCMETA-003`, `DOCGEN-001`–`DOCGEN-005`,
`DOCREP-001`–`DOCREP-005`

# Documentation Standard and Agent Guidance

Create the canonical repository documentation and specification standards,
define package documentation profiles, and update agent routing without adding
boilerplate or reconstructed documentation to every package.

## Requirements checklist

- [x] The unified maintainer meta-specification defines the target and its
  requirements track both reusable and repository-specific output artifacts.
- [x] `docs/development/index.md` provides a concise map to repository-wide
  development documentation.
- [ ] `docs/development/standards/` contains reusable package-neutral
  documentation and specification standards.
- [ ] `docs/development/repository/` maps the generic standards to Crystal
  Lattice paths, package profiles, plugin documentation, tasks, agent guidance,
  publication, and validation without duplicating the generic explanations.
- [x] Root `AGENTS.md` contains concise routing and update guidance and points to
  the effective repository policy, generic standards, and maintainer
  specification only when an agent is changing the standards themselves.
- [x] The standard does not require placeholder pages, duplicated boilerplate,
  or broad reverse engineering of undocumented packages.
- [x] Initial major package roots are classified under the approved profiles,
  and package entry-point creation is assigned to the owning migration
  subtasks.
- [x] The approved decision register in the parent task remains reflected in
  the authored standard and remains reviewable.

## Supporting details

### Approved model

The full rationale, research references, package profiles, documentation roles,
specification convention, target/current-state model, and approved decision
register are in:

- `tasks/20260728-package-local-documentation-standard/000-main.md`

The standard should preserve the distinction between:

- concise repository/package routing in `AGENTS.md`;
- first-use and installation guidance in README and quickstart;
- package-user documentation in `<package>/docs/`;
- contributor and internals documentation in
  `<package>/docs/development/`;
- root cross-package guidance in `docs/development/`;
- generated reference and site outputs.

### Proposed root `AGENTS.md` text

Use this as the baseline, adapting links and wording only as necessary:

```markdown
## Documentation ownership and workflow

Documentation is authored next to the package or subsystem that owns it.

- Start package work by reading the package `README.md`, nearest `AGENTS.md`,
  and `docs/index.md` when present.
- Keep `README.md` concise: purpose, installation, first use/build/test, and
  pointers to detailed documentation.
- Put package-user documentation under `<package>/docs/`.
- Put package internals, contributor workflows, architecture, and
  specifications under `<package>/docs/development/`.
- Keep root `docs/` for repository-wide guidance and genuinely cross-package
  contracts. Do not use it as the default location for package documentation.
- Treat package-local files as the source of truth. `docs_site/prepared/` and
  `docs_site/dist/` are generated outputs and must not be edited directly.
- Before implementing a substantive new capability, create or update the
  owning package's specification under
  `docs/development/specifications/<feature>/`.
- Use stable requirement IDs for important acceptance behavior and record
  implementation, verification, documentation, task, and delivery evidence.
  Keep execution steps in `tasks/`; do not duplicate the task plan in a spec.
- Update specifications when behavior changes during implementation. Update
  user documentation, tests, and requirements evidence before completion.
- Do not invent a documentation baseline by reconstructing large areas of
  unfamiliar code. Document facts verified during the current work and record
  larger documentation gaps for later migration.

See:

- `docs/development/repository/index.md`
- `docs/development/standards/index.md`
```

### Package entry-point principle

Do not create nearly empty `AGENTS.md`, `docs/index.md`, or
`docs/quickstart.md` across every plugin. The approved package profiles permit
README-only small packages and inherited parent guidance.

For a major package that lacks the full structure, use existing README and
verified documentation to create concise routing pages. Do not fabricate
long-form content merely to complete the shape.

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
- The execution plan is `Approved`.

## Execution plan

Status: Approved

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
3. **Artifact responsibilities**
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
3. **Artifact roles**
   - `index.md`: scope, links, ownership, and related tasks/specs;
   - `product-spec.md`: problem, users, user-visible behavior, goals,
     non-goals, acceptance examples;
   - `technical-spec.md`: architecture, contracts, data, compatibility,
     migration, failure behavior, security, rollout, verification;
   - `requirements.md`: stable normalized outcomes and evidence;
   - `decisions/NNNN-<slug>.md`: material architecture/design decisions.
4. **Proportional artifact set**
   - the full set is not mandatory for every change;
   - omitted artifacts should be obviously unnecessary from the index/scope,
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
   - whether root AGENTS remains concise enough for recurring agent context.
8. Leave requirements depending on that human review incomplete until the
   review is confirmed.

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
- [ ] Obtain human review of clarity and agent-context concision.

### Requirement verification

| Requirement group | Acceptance evidence |
|---|---|
| Development hub | `docs/development/index.md` preserves all active cross-package specification links and exposes reusable standards and repository policy with a concise ownership explanation. |
| Documentation structure | Human inspection confirms the generic page is package-neutral, the repository overlay contains local mappings/exceptions without generic duplication, and artifact roles, package profiles, ownership, generated-output, migration, and incremental-adoption rules are explicit. |
| Specification workflow | Human inspection confirms target-state specification semantics, requirements-owned live tracking, task-owned approval, simple spec-first commits, optional major-version separation, stable IDs, evidence, ADRs, current-doc coupling, and temporary multi-commit progress rules. |
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
