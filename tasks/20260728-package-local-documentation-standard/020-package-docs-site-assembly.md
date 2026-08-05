Parent Task: tasks/20260728-package-local-documentation-standard/000-main.md

Depends On:

- `tasks/20260728-package-local-documentation-standard/010-documentation-standard-and-agent-guidance.md`

Specification:
`maintainer/specifications/documentation-and-specification-standard/index.md`

Requirement IDs:
`DOCPUB-001`–`DOCPUB-003`, `DOCVAL-001`

# Package Documentation Site Assembly

Extend the existing MkDocs preparation pipeline so explicitly registered
package-local documentation is assembled into stable generated site paths with
focused automated coverage.

## Requirements checklist

- [ ] A repository-owned package documentation registry defines package ID,
  title, source root, site destination, included sources, and development-doc
  publication behavior.
- [ ] `docs_site/scripts/prepare_mkdocs_site.py` assembles registered package
  documentation under `docs_site/prepared/packages/<package-id>/`.
- [ ] `docs/index.md` is preferred as a package landing page; README is used as
  a fallback when no package docs index exists.
- [ ] Package `docs/` content is copied recursively while preserving a
  predictable site-relative structure.
- [ ] `AGENTS.md` is excluded from public site output by default.
- [ ] The assembler detects duplicate package IDs, destination collisions, and
  invalid/missing configured sources with actionable errors.
- [ ] Package-relative and repository-relative links are handled consistently
  for prepared pages.
- [ ] Existing plugin development docs, built-in plugin README generation,
  default config generation, site-only source overlays, and ignored generated
  output continue to work.
- [ ] Focused automated tests cover registry and assembly behavior.
- [ ] `docs_site/README.md` explains package registration, authoring sources,
  generated destinations, and local verification commands.

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

## Execution plan

Status: Draft

1. Define and parse the explicit package registry using standard-library
   facilities where practical.
2. Validate registry entries before mutating the prepared directory.
3. Add package assembly after the existing base/site source setup while
   preserving current plugin/default-config generators.
4. Implement landing-page precedence and README fallback.
5. Copy package docs recursively with clear exclusions.
6. Reuse and generalize existing link-normalization helpers instead of adding
   package-specific ad hoc rewriting.
7. Add focused tests around temporary package trees and generated destinations.
8. Update docs-site maintenance documentation.

### Implementation decisions and open questions

- Explicit registry, `docs/index.md` precedence, README fallback, and default
  `AGENTS.md` exclusion are approved.
- The precise TOML field names and internal helper decomposition are local,
  reversible implementation choices.
- If preserving current public plugin URLs conflicts with the new package
  destination, preserve current behavior here and resolve public routing in
  subtask 060.

### Documentation

- `docs_site/README.md`
- `docs_site/packages.toml` comments or a documented registry schema
- Relevant root documentation-structure examples

### Task checklist

- [ ] Define registry schema.
- [ ] Parse and validate registry.
- [ ] Add package landing-page selection.
- [ ] Add recursive package docs assembly.
- [ ] Generalize link normalization.
- [ ] Add collision and invalid-source errors.
- [ ] Preserve existing generated docs behavior.
- [ ] Add focused tests.
- [ ] Update docs-site README.

### Requirement verification

| Requirement group | Acceptance evidence |
|---|---|
| Registry | Tests load valid entries and reject duplicates, invalid destinations, and missing required sources. |
| Landing behavior | Tests demonstrate `docs/index.md` precedence and README fallback without duplicate implicit landings. |
| Recursive assembly | Tests compare a representative nested package docs tree with generated destinations. |
| Exclusions | Tests confirm `AGENTS.md` and unregistered content are not published. |
| Compatibility | Existing plugin-development, built-in-plugin, default-config, and site-overlay outputs remain present after preparation. |
| Documentation | `docs_site/README.md` explains source-of-truth and generated paths accurately. |

### Additional implementation verification

- Run the focused preparation tests.
- Run `python docs_site/scripts/prepare_mkdocs_site.py`.
- Inspect representative package output under `docs_site/prepared/packages/`.
- Confirm `git status` does not show generated prepared/dist files as tracked
  source changes.
