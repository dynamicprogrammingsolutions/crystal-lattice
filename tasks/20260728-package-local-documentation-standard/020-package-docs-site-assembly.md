Parent Task: tasks/20260728-package-local-documentation-standard/000-main.md

Depends On:

- `tasks/20260728-package-local-documentation-standard/010-documentation-standard-and-agent-guidance.md`

Specification:
`maintainer/docs/development/specifications/crystal-lattice-guidance-integration/index.md`

Requirement IDs:
`DOCPUB-001`–`DOCPUB-003`, partial `DOCPUB-005`, `DOCVAL-001`, partial
`DOCVAL-003`

# Package Documentation Site Assembly

Extend the existing MkDocs preparation pipeline so explicitly registered
package-local documentation is assembled into stable generated site paths with
focused automated coverage.

## Requirements checklist

- [x] A repository-owned package documentation registry defines package ID,
  title, source root, site destination, included sources, and development-doc
  publication behavior.
- [x] `docs_site/scripts/prepare_mkdocs_site.py` assembles registered package
  documentation under `docs_site/prepared/packages/<package-id>/`.
- [x] The assembler generates `docs_site/prepared/packages/index.md` from
  registry titles and destinations as the stable package documentation catalog.
- [x] `docs/index.md` is preferred as a package landing page; README is used as
  a fallback when no package docs index exists.
- [x] Package `docs/` content is copied recursively while preserving a
  predictable site-relative structure.
- [x] `AGENTS.md` is excluded from public site output by default.
- [x] The assembler detects duplicate package IDs, destination collisions, and
  invalid/missing configured sources with actionable errors.
- [x] Package-relative and repository-relative links are handled consistently
  for prepared pages.
- [x] Existing plugin development docs, built-in plugin README generation,
  default config generation, site-only source overlays, and ignored generated
  output continue to work.
- [x] Focused automated tests cover registry and assembly behavior.
- [x] `docs_site/README.md` explains package registration, authoring sources,
  generated destinations, and local verification commands.
- [x] The landing page's visible documentation link uses the configured public
  documentation URL rather than the repository README.
- [x] Locally built and served landing and documentation sites pass a
  Playwright smoke test covering the cross-site Docs link, package catalog, and
  a representative package landing page.

## Supporting details

### Existing mechanism

The repository already uses:

- `docs_site/scripts/prepare_mkdocs_site.py`
- `docs_site/mkdocs.yml`
- `docs_site/prepared/`
- `docs_site/source/`
- `docs_site/scripts/build_mkdocs_site.py`

The task extends this mechanism. It must not add a parallel `docs_sites/`
directory or treat generated prepared files as authoring sources.

### Approved registry direction

Use an explicit registry, preferably:

```text
docs_site/packages.toml
```

An illustrative entry may define:

```toml
[[package]]
id = "core-python"
title = "Core Python SDK"
source = "core/python"
destination = "packages/core-python"
include_readme = true
include_docs = true
publish_development = true
```

The exact schema may be refined during implementation, but it must keep site
identity, source ownership, and publication policy explicit.

### Landing-page behavior

Approved precedence:

1. If `<package>/docs/index.md` exists and `include_docs` is enabled, use it as
   the package site's `index.md`.
2. Otherwise, if README inclusion is enabled, transform `<package>/README.md`
   into the package site's `index.md`.
3. Do not emit two competing package landing pages by default.
4. If preserving a README snapshot is valuable, its separate site path must be
   an explicit registry option rather than implicit duplication.

### Proposed generated shape

```text
docs_site/prepared/
└── packages/
    ├── core-python/
    │   ├── index.md
    │   ├── quickstart.md
    │   ├── events.md
    │   ├── development/
    │   └── reference/
    └── application-python/
        ├── index.md
        ├── quickstart.md
        ├── configuration.md
        └── development/
```

### Current repository findings

- The preparation script currently removes `docs_site/prepared/` before it
  copies root docs, site-only overlays, shared plugin docs, built-in plugin
  READMEs, and the generated default configuration reference.
- Registry validation must therefore happen before the current destructive
  setup, and full assembly should use a temporary staging tree so any later
  copy or generation failure also leaves the previous prepared tree intact.
- The script has one README link normalizer that sends unresolved repository
  content to GitHub, plus a separate plugin-doc replacement helper. It does not
  yet know which root or package-local source pages have prepared-site
  destinations.
- No focused tests currently own the docs-site preparation script.
- The repository supports Python 3.10. TOML parsing can use `tomllib` on Python
  3.11+ with the existing project convention of a conditional `tomli`
  dependency for Python 3.10.
- The repository policy classifies Core, application, shared frontend/tool
  packages, mobile/desktop applications, and bridge/cloud services as public
  package profiles. Individual plugins already have a separate generated
  built-in-plugin README path and should not be duplicated through the package
  registry.
- Core and application currently have README files and package development
  docs but no `docs/index.md`; this provides a real first use of README
  fallback before their migration subtasks add package indexes.
- Subtask 060, not this task, owns final MkDocs navigation, LLM section
  curation, old public URL compatibility, and deployment workflow path
  triggers.
- The authored standards and repository-policy outputs from dependency 010 are
  present. Its remaining human wording review does not change the approved
  registry, landing-page, publication, or generated-output boundaries used by
  this task.

## Execution plan

Status: Approved

This subtask will add one explicit package-publication registry and extend the
existing preparation program. It will not create another docs tree, move
authored documentation, curate final navigation, preserve old public URLs, or
change deployment triggers.

### 1. Define the registry and initial publication set

Add `docs_site/packages.toml` with a versioned top-level format and repeated
`[[package]]` entries. Each entry will require:

- `id`: lowercase URL-safe package identity;
- `title`: non-empty public display name;
- `source`: repository-relative package root;
- `destination`: repository-site-relative output, required to match
  `packages/<id>`;
- `include_readme`: whether README may supply the landing page;
- `include_docs`: whether the package `docs/` tree is published;
- `publish_development`: whether `docs/development/` is included.

Register the public package roots already classified by repository policy:

- `core/python`;
- `application/python`;
- `packages/frontend-sdk`;
- `packages/frontend-sdk-react`;
- `packages/frontend-rn-components`;
- `packages/tool-host-node`;
- `packages/react-native-mac-text-view`;
- `mobile/crystal-lattice-control-rn`;
- `desktop/crystal-lattice-control-desktop-rn`;
- `bridge-elixir`;
- `cloud-orchestrator`.

Enable `include_docs` only where a package docs tree currently exists. Use the
approved default of publishing current development docs for those packages.
Do not register individual `plugins/*` packages because the existing
`built-in-plugins/` generator remains their publication mechanism.

Generate `docs_site/prepared/packages/index.md` from the validated registry.
The page will use registry titles as link labels, link each entry to
`<id>/index.md`, and use deterministic registry order so the public catalog is
stable and reviewable. The generated catalog is the landing page for
`/packages/`; package pages remain under `/packages/<id>/`.

Use `tomllib` with a conditional `tomli` fallback for Python 3.10 and add the
conditional docs-tooling dependency. Reject unknown keys so registry typos do
not silently change publication policy.

### 2. Parse and preflight all configured inputs

Introduce a small immutable registry-entry type and a preparation-specific
exception whose messages identify the entry, field, path, or conflicting
destination.

Before creating or removing any prepared output:

1. Parse the complete registry and validate its schema version and value types.
2. Require unique package IDs, source roots, and destinations.
3. Reject empty/invalid IDs or titles, absolute paths, `..` traversal,
   non-normalized paths, paths outside the repository, and destination nesting
   that could overlap another package.
4. Require every source root to be a directory, every enabled README to exist,
   and every enabled docs source to be a directory.
5. Require at least one included input and disallow
   `publish_development = true` when docs publication is disabled.
6. Reject package destinations that collide with root docs, site-only
   overlays, or fixed generated output.
7. Precompute every package source-to-output mapping and reject duplicate
   output paths before copying.
8. Reserve `packages/index.md` for the generated catalog and reject any source
   or destination that would overwrite it.
9. Keep `maintainer/`, task/plan domains, and prepared/dist trees outside valid
   public package sources.

The root-docs then site-overlay precedence is an existing intentional layer and
will remain supported; package destinations may not rely on that overwrite
behavior.

### 3. Make preparation transactional and parameterizable

Refactor preparation helpers to accept a repository root and output root so
focused tests can use temporary repositories without mutating the real
prepared tree.

The production flow will:

1. load and preflight the registry;
2. assemble every current and new output into a temporary sibling staging
   directory;
3. run root docs, site overlays, package assembly, shared plugin copying,
   built-in plugin README generation, and default-config generation against
   that staging root;
4. replace `docs_site/prepared/` only after all stages succeed, with rollback
   if final replacement fails;
5. clean temporary/backup directories on both success and failure.

This preserves the current ordering and generated outputs while satisfying the
repository rule that failed preparation does not leave a partial new tree.

### 4. Assemble registered package docs

For each validated entry:

1. Copy included `docs/` content recursively to the configured destination,
   preserving relative directories and non-Markdown assets.
2. Exclude every file named `AGENTS.md`, including nested copies.
3. Exclude the complete `docs/development/` subtree when
   `publish_development` is false.
4. If an included `docs/index.md` exists, use it as destination `index.md`.
5. Otherwise transform the enabled package README into destination `index.md`.
6. Fail with an actionable message when neither configured source can produce
   a landing page.
7. Do not emit a second README page implicitly. A future separate README
   snapshot would require an explicit registry field and separate approval.

The copy plan will be deterministic through sorted traversal. Markdown is
rewritten during copying; other files retain their content.

After package pages are assembled, generate the package catalog from the same
validated entries. No second package inventory will be maintained in MkDocs
configuration or an authored root page during this subtask.

### 5. Normalize links through one source/output map

Generalize the current README link handling into a helper that receives the
source page, prepared destination, and complete public source-to-output map.
Use it for package Markdown and existing generated README pages while retaining
the plugin-doc heading/path compatibility replacements.

For each Markdown link or image target:

- preserve external URLs, absolute site URLs, mail/tel links, and local
  fragments;
- preserve fragments and optional Markdown link titles;
- resolve package-relative targets from the authored source page;
- recognize repository-relative targets consistently;
- rewrite targets that map to a prepared root, package, generated-plugin, or
  generated-reference page as relative prepared-site links;
- send repository files that are not published to their GitHub source URL;
- never produce site links to excluded development docs, `AGENTS.md`,
  maintainer content, tasks, plans, or generated source inputs.

The mapping will include root `docs/`, site-only source overlays, registered
package pages, shared plugin docs, generated built-in-plugin README pages, and
the generated default-config reference. Existing special handling for the
default config will become a mapping entry rather than package-specific logic.

### 6. Add focused automated coverage

Add `docs_site/tests/test_prepare_mkdocs_site.py` using pytest and temporary
repository trees. Refactoring for injected roots will let tests exercise the
production functions directly rather than duplicate the assembler.

Cover:

- valid registry loading and retention of all required metadata;
- duplicate IDs, sources, and destinations;
- invalid types, unknown keys, traversal, missing roots/README/docs, invalid
  development policy, nested destinations, and fixed-output collisions;
- validation and assembly failure leaving an existing prepared sentinel tree
  unchanged;
- `docs/index.md` precedence over README and README fallback without duplicate
  landing pages;
- generated package-catalog titles, links, order, and reserved-path collision
  behavior;
- recursive nested docs/assets and deterministic output;
- nested `AGENTS.md` exclusion and both development-publication modes;
- same-package, cross-package, root-doc, generated-reference, and unpublished
  repository link behavior, including fragments and link titles;
- current root-doc/site-overlay copying, shared plugin docs, built-in plugin
  README pages, and generated default-config output.

Include nearby `DOCPUB-001`–`DOCPUB-003` and `DOCVAL-001` identifiers on the
acceptance-level tests without adding IDs to every helper test.

### 7. Repair and smoke-test the landing-to-docs route

Update the landing page's existing visible `Docs` navigation link to use the
shared `docsUrl` value from `landing_page/src/config/publicUrls.ts`. Preserve
the current build-time `PUBLIC_CRYSTAL_LATTICE_DOCS_URL` override and external
link behavior; do not introduce a second URL configuration path.

Add a small Playwright smoke program under docs-site test tooling and a
development-only requirements file so the verification is reproducible
without adding Playwright or pytest to production MkDocs dependencies. The
smoke program will accept landing/docs base URLs and verify:

1. the landing page loads without browser console or page errors;
2. its visible Docs link resolves to the configured local docs origin;
3. following that link loads the documentation overview;
4. `/packages/` loads the generated package catalog;
5. every catalog entry has a usable package route; and
6. a representative README-fallback package page renders successfully.

Build both static sites with local public URL variables, serve the landing site
on `127.0.0.1:4321` and docs on `127.0.0.1:8001`, run the smoke program against
the real HTTP servers, and stop the temporary servers after verification.

### 8. Document the maintained workflow and current behavior

Update `docs_site/README.md` to:

- identify package-local files and `docs_site/packages.toml` as maintained
  sources;
- document every registry field and validation rule;
- explain landing precedence, recursive copying, development publication, and
  default exclusions;
- distinguish package destinations from shared plugin and generated reference
  destinations;
- document the generated `/packages/` catalog;
- state that prepared/dist trees are generated;
- provide focused test, preparation, normal build, and local serve commands.
- document the Playwright development dependency and two-site smoke command.

Update the publication section of
`docs/development/repository/documentation.md` from future-task wording to the
delivered registry behavior, using repository-policy vocabulary rather than
task or requirement IDs.

After implementation, update the maintainer requirements ledger and task
records with actual test/build evidence. Do not expose that internal evidence
in the public docs-site README or repository policy.

### Implementation decisions and open questions

- Approved decisions applied here are the explicit TOML registry,
  `docs/index.md` precedence, README fallback, publication of development docs
  by default, package output under `packages/<id>/`, and default `AGENTS.md`
  exclusion.
- The registry will enforce `destination = "packages/<id>"`. Keeping the field
  explicit preserves reviewable public-site policy while preventing a
  configured destination from violating this subtask's required output shape.
- The initial registry follows the public package classifications already
  approved in dependency 010. Plugin packages remain on the existing generated
  built-in-plugin path to avoid duplicate publication.
- The registry is also the only maintained package-catalog inventory. The
  generated `/packages/` page makes `title` user-visible without duplicating
  package metadata.
- Existing plugin-development and built-in-plugin URLs will not move here.
  Navigation, LLM grouping, old-route compatibility, and workflow triggers
  remain assigned to subtask 060.
- Link rewriting prefers prepared-site destinations only for known published
  sources; unpublished repository files remain source links rather than
  becoming broken site routes.
- Pytest tests will live with docs-site tooling and use the repository's normal
  Python development environment. Pytest and Playwright will be documented in
  a development-only requirements file rather than production MkDocs
  dependencies.
- The landing-page repair reuses its existing public docs URL configuration.
  It does not otherwise change landing-page content, design, or deployment.
- The user approved the package catalog, landing-link repair, Playwright smoke
  verification, and execution of this adjusted plan.
- No requirement questions or material design decisions remain open. Local
  helper names and decomposition may be adjusted during implementation without
  changing this plan.

### Documentation

- `docs_site/README.md`
- `docs_site/packages.toml`
- `docs/development/repository/documentation.md`
- `landing_page/README.md` if its local cross-site verification instructions
  require clarification
- `maintainer/docs/development/specifications/crystal-lattice-guidance-integration/requirements.md`
- this subtask and the parent task for implementation/completion evidence

### Task checklist

- [x] Add and populate the explicit package registry.
- [x] Parse and preflight registry/source/output policy before mutation.
- [x] Make preparation transactional and injectable for tests.
- [x] Add package landing selection and recursive docs assembly.
- [x] Generate the registry-driven package catalog.
- [x] Enforce development and non-public exclusions.
- [x] Generalize prepared-site/source link normalization.
- [x] Preserve root docs, overlays, plugin docs, built-in plugins, and default config.
- [x] Add focused registry, assembly, failure-safety, and compatibility tests.
- [x] Update docs-site and repository-policy documentation.
- [x] Repair the landing-page Docs link and add cross-site Playwright smoke coverage.
- [x] Run focused tests, production preparation, and normal MkDocs build.
- [x] Build and serve both sites and run the Playwright smoke test.
- [x] Update requirements/task evidence and append completion notes.

### Requirement verification

| Requirement group | Acceptance evidence |
|---|---|
| `DOCPUB-001` registry | The committed TOML registry contains every required policy field for the approved initial package set; focused tests load it and reject malformed, duplicate, escaping, missing, or colliding entries before output mutation. |
| `DOCPUB-002` landing and recursive assembly | Temporary-tree tests demonstrate docs-index precedence, README fallback, no implicit duplicate landing, nested docs/assets, deterministic destinations, and actionable missing-input errors. |
| Package catalog | Tests confirm `/packages/` is generated solely from registry titles/destinations in deterministic order and links to every registered package landing page. |
| `DOCPUB-003` exclusions | Tests demonstrate recursive `AGENTS.md` exclusion, development-policy exclusion, rejection of non-public source domains, omission of unregistered content, and no publication mapping for maintainer/task/plan inputs. |
| Link behavior | Tests compare same-package, cross-package, root-doc, generated-reference, and GitHub-source targets, including fragments and titles, with their expected prepared-page links. |
| Transactional behavior | Tests preserve a sentinel prepared tree across registry/preflight and copy/generation failures, while a successful run replaces it with the complete new tree. |
| Existing pipeline compatibility | Focused tests and production inspection confirm root docs, site overlays, shared plugin development docs, built-in plugin pages, and default-config reference remain present and generated from their current sources. |
| `DOCVAL-001` automated coverage | `python -m pytest docs_site/tests -q` collects the focused tests and exits successfully. |
| Landing/docs integration | A production-style Astro build configured for the local docs origin and the normal MkDocs build are served over HTTP; Playwright follows the visible landing-page Docs link, loads `/packages/`, and opens representative catalog entries without browser errors. |
| Maintainer documentation | `docs_site/README.md` accurately documents registration, maintained inputs, generated destinations, exclusions, and verification; repository policy states current behavior without internal task context. |
| Production boundary | Preparation and a normal MkDocs build exit successfully; generated prepared/dist changes remain ignored; warnings introduced by this subtask are fixed while broader warning classification remains with subtask 070. |

### Additional implementation verification

- Run `python -m pytest docs_site/tests -q`.
- Run `python docs_site/scripts/prepare_mkdocs_site.py`.
- Inspect README-fallback and docs-index package output under
  `docs_site/prepared/packages/`, plus a package with nested development docs.
- Confirm recursive output contains no `AGENTS.md` and no unregistered package
  content.
- Run `(cd docs_site && mkdocs build)` without refreshing committed reference
  snapshots.
- Build the landing page with
  `PUBLIC_CRYSTAL_LATTICE_DOCS_URL=http://127.0.0.1:8001`.
- Serve landing output on port 4321 and docs output on port 8001, then run the
  Playwright cross-site smoke test and stop both servers.
- Compare package-page links in prepared Markdown and representative built
  routes.
- Run `git diff --check`.
- Confirm `git status` does not show generated prepared/dist files as tracked
  source changes.

## Implementation Notes

- Added the versioned registry with eleven package entries matching the public
  package profiles approved by repository policy.
- Refactored preparation around an immutable validated plan and injected
  repository/output roots. All output is assembled in a temporary sibling tree
  and replaces the prior prepared tree only after successful completion.
- Generalized Markdown links through one source-to-output map covering root
  docs, site overlays, package docs, shared plugin docs, built-in-plugin
  READMEs, and generated default configuration.
- Added the registry-driven `/packages/` catalog requested during plan review.
- Repaired the landing navigation's Docs link to consume the existing
  `PUBLIC_CRYSTAL_LATTICE_DOCS_URL` configuration.
- The first browser run exposed missing package Markdown companions for the
  page-level LLM actions. Added package patterns to the existing `llmstxt`
  configuration. Final navigation and LLM information-architecture curation
  remain assigned to subtask 060.
- Playwright's `networkidle` condition was unsuitable for `mkdocs serve`
  because live reload keeps a connection open. The smoke boundary uses normal
  page load plus explicit page/heading/route assertions.
- Material's optional GitHub repository/release metadata requests return 404
  for the configured repository and predate this change. The smoke test ignores
  only those external metadata URLs while continuing to fail on local 4xx/5xx
  responses, browser page errors, and other console errors.

## Completion Notes

Implemented the registered package documentation assembly, generated package
catalog, landing-to-docs link repair, focused automated tests, and live
cross-site browser verification.

Requirement evidence:

- `DOCPUB-001`: `docs_site/packages.toml` records ID, title, source,
  destination, included inputs, and development publication for eleven public
  packages. Registry tests cover required/unknown fields, invalid values,
  duplicate IDs/sources/destinations, traversal, non-public roots, and
  collisions.
- `DOCPUB-002`: preparation emits `/packages/` and each
  `/packages/<package-id>/`, prefers package docs index, falls back to README,
  recursively preserves docs/assets, normalizes links, and reports invalid
  inputs through `PreparationError`.
- `DOCPUB-003`: recursive `AGENTS.md` exclusion, configurable development-doc
  exclusion, non-public source rejection, and generated-tree inspection passed.
- `DOCVAL-001` package-assembly portion: all 14 focused pytest tests passed.
- Partial `DOCVAL-003`: Playwright followed the configured landing-page Docs
  link, loaded the docs overview and package catalog, verified all eleven
  package routes, and rendered the Core README-fallback page.

Verification performed:

- `python -m pytest docs_site/tests/test_prepare_mkdocs_site.py -q`:
  14 passed.
- `ruff check docs_site/scripts/prepare_mkdocs_site.py
  docs_site/tests/test_prepare_mkdocs_site.py
  docs_site/tests/smoke_sites.py`: passed.
- `python docs_site/scripts/prepare_mkdocs_site.py`: passed against the
  production repository.
- Generated-tree inspection found eleven package landing pages, the package
  catalog, expected development docs, all existing generator outputs, and no
  package `AGENTS.md`.
- Local-URL Astro production build: 5 pages built successfully.
- Local-URL normal MkDocs build: passed. Existing Griffe indentation and
  mkdocs-autorefs `"content"` warnings remain. MkDocs also reports package and
  other pages omitted from explicit navigation; final nav is owned by subtask
  060.
- `docs_site/dist/packages/index.md` and package Markdown companions were
  generated for page-level LLM actions.
- Landing preview on `127.0.0.1:4321` and MkDocs serve on
  `127.0.0.1:8001` passed `docs_site/tests/smoke_sites.py`; both temporary
  servers were stopped after the test.
- `git diff --check` passed, and prepared/dist outputs remain ignored.

Plan deviations and findings:

- Package Markdown was added to existing `llmstxt` generation after realistic
  browser verification found otherwise-broken page-level Markdown preloads.
  This is generation compatibility, not final navigation curation.
- No authored package documentation was migrated or rewritten. Final MkDocs
  navigation, old-route compatibility, deployment triggers, and migration link
  updates remain with subtask 060 and later migration/verification subtasks.

## Post-completion follow-up

Status: Approved

The user requested implementation of the headed-Playwright usability
assessment findings and a repeat assessment after correction. This follow-up
reopens only the site-structure, navigation, generated catalog, landing-link,
and accessibility portions of the completed task.

Major package-authored documentation indexes remain owned by migration
subtasks 030 and 040. This follow-up must not create competing generated or
authored replacements for those package sources.

### Requirements checklist

- [x] Package documentation is reachable from the docs overview and a visible
  primary Packages navigation section.
- [x] Registered package landing pages have active package-navigation context
  and a clear route back to the generated package catalog.
- [x] The package catalog groups related packages and gives each package a
  concise registry-owned summary.
- [x] Primary navigation uses concise audience-oriented categories and does not
  enumerate every built-in plugin globally.
- [x] The mobile documentation drawer remains understandable and does not
  expose the prior exhaustive built-in-plugin list.
- [x] The landing page exposes the configured documentation link at desktop
  and phone widths.
- [x] Cross-site navigation does not unexpectedly force a new tab.
- [x] Visible documentation theme controls have explicit accessible names and
  keyboard activation where the upstream label controls do not provide them.
- [x] Search and package navigation are verified at desktop, narrow-laptop,
  and mobile widths.
- [x] Focused tests, builds, live Playwright smoke checks, and a new headed
  screenshot assessment pass.
- [x] Screenshots and repeat-assessment findings are recorded without adding
  generated captures to tracked source.

### Execution checklist

- [x] Extend registry metadata and generated catalog presentation.
- [x] Reorganize MkDocs navigation and add package context.
- [x] Add the package route to the docs overview.
- [x] Correct responsive landing-page documentation access.
- [x] Improve generated theme-control accessibility.
- [x] Update focused tests and maintenance documentation.
- [x] Build and smoke-test both sites.
- [x] Run headed Playwright at desktop, 1024 px, and phone widths.
- [x] Record follow-up evidence and remaining downstream work.

### Follow-up implementation and verification

- Extended each registry entry with a catalog group and one-sentence summary.
  The generated catalog now presents four user-oriented groups while retaining
  the registry as the only maintained package inventory.
- Reorganized MkDocs navigation into Overview, Guides, Packages, Plugin
  Development, Reference, Development, and Website. Registered package pages
  now retain active Packages context and specific browser/navigation titles.
- Added a package-catalog route to the docs overview and removed individual
  built-in-plugin pages from global navigation. The built-in-plugin index
  remains under Plugin Development and continues to expose every generated
  plugin page.
- Added visible desktop and mobile landing-page Docs links plus a footer route.
  All use the configured docs origin and remain in the current tab.
- Added a generated docs accessibility enhancement for navigation, search, and
  palette labels. The live smoke test confirms explicit names, focusability,
  and Enter-key activation for the mobile drawer and visible theme control.
- Updated package assembler tests, docs-site/landing maintenance guidance,
  repository publication policy, and live requirements evidence.

Verification:

- Focused package preparation tests: 14 passed.
- Ruff and `git diff --check`: passed.
- Production preparation and local-URL Astro build: passed.
- Normal MkDocs build: passed with the same pre-existing Griffe and
  mkdocs-autorefs warnings. Generated built-in-plugin leaves and selected
  package development details are intentionally reached from owning indexes
  rather than enumerated in global navigation.
- Live Playwright smoke: passed desktop/mobile Docs routing, same-tab behavior,
  overview/catalog reachability, grouped catalog and all eleven routes, active
  package navigation, real-keystroke search, keyboard drawer/theme controls,
  LLM Markdown companions, and local browser-error checks.
- Headed Chromium reassessment covered 1440×1000, 1024×768, and 390×844.
  No tested page had horizontal overflow. Search returned 77 matching
  documents for “Core Python SDK,” including the Core package.
- Fresh screenshots are under ignored
  `artifacts/docs-site-usability-reassessment/`; no generated capture is a
  tracked documentation source.

Remaining downstream work:

- The Core README fallback remains approximately 14,000 pixels tall at the
  desktop assessment viewport and exposes 47 table-of-contents links. Subtask
  030 owns its concise package-authored docs index and quickstart.
- Application package entry points and migration remain with subtask 040.
- Public URL compatibility and deployment path triggers remain with subtask
  060; its navigation work should start from the structure delivered here
  rather than restore the prior exhaustive menu.
