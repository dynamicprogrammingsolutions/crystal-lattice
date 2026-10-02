Parent Task: tasks/20260728-package-local-documentation-standard/000-main.md

Depends On:

- `tasks/20260728-package-local-documentation-standard/010-documentation-standard-and-agent-guidance.md`
- `tasks/20260728-package-local-documentation-standard/020-package-docs-site-assembly.md`

Specification:
`maintainer/docs/development/specifications/crystal-lattice-guidance-integration/index.md`

Requirement IDs:
`DOCREP-002`, `DOCREP-004`, `DOCMIG-002`, `DOCPUB-006`

# Application and Plugin Documentation Migration

Create application package documentation entry points and relocate
ownership-clear application configuration, terminal/runtime development, and
shared plugin overview documentation with bounded verification.

## Requirements checklist

- [x] `application/python` has package documentation entry points required by
  the approved public-package profile.
- [x] `docs/plugins/application-config.md` is relocated to
  `application/python/docs/configuration.md` or another approved
  application-owned path.
- [x] Configuration keys and examples touched by the move are checked against
  current config loading, default configuration, or existing tests.
- [x] `docs/plugins/development.md` is relocated to `plugins/docs/overview.md`
  or another approved shared-plugin location.
- [x] The shared plugin overview remains an overview and points to current
  detailed plugin docs instead of duplicating them.
- [x] Root `DEVELOPMENT.md` is inspected and either relocated to root
  cross-package development docs, moved under application development docs, or
  retained/deferred with explicit rationale.
- [x] Existing `plugins/docs/AGENTS.md` guidance is updated to reflect the new
  canonical overview location and repository documentation standard.
- [x] Existing built-in plugin README pages retain stable generated landing
  pages, and existing public plugin-local `docs/` content is assembled beneath
  the corresponding plugin destination with `AGENTS.md` excluded.
- [x] Every published plugin-local docs tree has an index route from its
  generated plugin landing page, using an authored `docs/index.md` when present
  and a generated catalog when it is absent.
- [x] Existing plugin-local documentation is boundedly inspected for public
  suitability; sensitive/internal content is excluded explicitly rather than
  blindly copied, and uncertain broad content is deferred.
- [x] Existing inbound links and public paths are recorded for subtask 060.
- [x] No broad application configuration or plugin system rewrite is performed
  solely to relocate documentation.

## Supporting details

### Candidate pages

- `docs/plugins/application-config.md`
- `docs/plugins/development.md`
- `DEVELOPMENT.md`
- `application/python/README.md`
- `application/python/agent_terminal_app/AGENTS.md`
- `plugins/AGENTS.md`
- `plugins/docs/AGENTS.md`
- `plugins/docs/index.md`

### Existing guidance added by subtask 015

Subtask 015 already updated `plugins/docs/AGENTS.md` so a new focused shared
plugin page must be linked from `plugins/docs/index.md` and, when it refines one
canonical guide, from that guide as well.

Preserve this rule while relocating the general plugin overview. Treat it as
the current baseline rather than overwriting `plugins/docs/AGENTS.md` from an
older task description.

### Plugin publication baseline

Subtask 020 generates one landing page from every `plugins/*/README.md`, but it
does not currently assemble package-local plugin `docs/` trees. Existing trees
include current development documentation and specifications under packages
such as `cloud-agent-app`, `openai_responses`, and `kimi-tools`.

This task extends the existing built-in-plugin output rather than registering
the same plugin twice through a second package destination:

```text
built-in-plugins/<plugin-id>/
├── index.md                 # README landing page
└── docs/
    ├── index.md             # authored index or generated catalog
    └── ...                  # recursively assembled public plugin docs
```

Subtask 060 owns final menu placement, breadcrumbs, and active ancestry for
these routes after all migrations establish their canonical destinations.

### Ownership rationale

- Application configuration is resolved and applied by `agent_app` and the
  terminal/runtime package, making `application/python` the natural owner.
- The older/general plugin development page is explicitly subordinate to the
  current shared docs under `plugins/docs/`, so it belongs in that shared
  domain.
- Root `DEVELOPMENT.md` spans Core application-layer and terminal behavior.
  Its final location should follow its actual scope after a bounded path and
  terminology check.

### Verification boundary

Verify only:

- configuration keys and paths directly documented in moved sections;
- current links to plugin guides and package-loading documentation;
- file paths and event terms used in `DEVELOPMENT.md`;
- package install/build/test commands used by new entry points.

Do not comprehensively audit the entire configuration system or plugin runtime.

## Execution plan

Status: Approved

1. Add concise `application/python/AGENTS.md`, `docs/index.md`, and
   `docs/quickstart.md` using the existing README and verified docs.
2. Move application configuration documentation and spot-check touched
   configuration claims.
3. Move the older/general plugin overview into `plugins/docs/`, update its role
   and links, and preserve detailed current plugin pages.
4. Inspect `DEVELOPMENT.md` scope and referenced paths, then choose the
   approved root/application destination or defer with rationale.
5. Update relevant package and plugin agent guidance.
   Preserve the focused-page index/canonical-guide backlink rule added by
   subtask 015.
6. Extend built-in-plugin preparation so existing public plugin-local docs are
   copied recursively under each generated plugin landing, with authored-index
   precedence, generated catalog fallback, link normalization, exclusions, and
   focused tests.
7. Inspect the current plugin docs trees for public suitability without
   reverse-engineering plugin behavior or rewriting target specifications as
   current user guides.
8. Record inbound links, deep plugin routes, and public compatibility
   requirements for subtask 060.

### Implementation decisions and open questions

- Application ownership of configuration docs and shared `plugins/docs/`
  ownership of the plugin overview are approved.
- The final location of `DEVELOPMENT.md` is a bounded design decision:
  - use root `docs/development/` if it remains substantially cross-package;
  - use `application/python/docs/development/` if it primarily describes the
    terminal/runtime application;
  - defer rather than force a misleading owner.
- No requirement questions are open.
- Existing plugin README destinations remain stable. Plugin-local docs are
  nested beneath the same destination to avoid duplicate package identities.
- The user approved execution of this revised plan, including plugin
  publication completeness, after the site-structure review.

### Documentation

- `application/python/AGENTS.md`
- `application/python/docs/index.md`
- `application/python/docs/quickstart.md`
- `application/python/docs/configuration.md`
- `plugins/docs/overview.md`
- root or application development destination for `DEVELOPMENT.md`
- updated plugin documentation routing
- `docs_site/scripts/prepare_mkdocs_site.py`
- focused docs-site preparation tests

### Task checklist

- [x] Create application package entry points.
- [x] Move and verify application configuration guide.
- [x] Move and normalize shared plugin overview.
- [x] Classify and handle root `DEVELOPMENT.md`.
- [x] Update package/plugin agent guidance.
- [x] Assemble and index public plugin-local docs.
- [x] Add plugin publication and exclusion tests.
- [x] Record inbound links and compatibility needs.

### Requirement verification

| Requirement group | Acceptance evidence |
|---|---|
| Application entry points | README/AGENTS/docs index/quickstart provide concise installation, first-run, detailed-doc, and development routes. |
| Configuration guide | Touched keys and examples align with current config loader/default config or focused existing tests. |
| Plugin overview | Canonical shared overview lives under `plugins/docs/` and points to current detailed pages without duplicating them. |
| Plugin package docs | Generated plugin landing pages link an authored or generated docs index; focused tests prove recursive copying, link handling, and `AGENTS.md` exclusion. |
| Development guide ownership | Completion notes record destination and bounded verification, or explicit defer rationale. |

### Additional implementation verification

- Run focused config parsing/schema tests only where moved claims require them.
- Search all links to old configuration/plugin/development paths.
- Inspect generated application and plugin docs output from the site assembler.
- Inspect the existing `cloud-agent-app`, `openai_responses`, and `kimi-tools`
  plugin docs trees and record any excluded or deferred content.

## Implementation Notes

- Added `application/python/AGENTS.md`, a package docs index, and a tested
  first-success HTTP quickstart.
- Moved application configuration to
  `application/python/docs/configuration.md` and verified path placeholders,
  mixin behavior, plugin enablement, and the documented `/api/hello` response
  against focused tests.
- Moved the general plugin overview to `plugins/docs/overview.md`, linked it
  from the shared plugin index, and updated package/root guidance and source
  references.
- Classified root `DEVELOPMENT.md` as application/terminal implementation
  guidance and moved it to
  `application/python/docs/development/terminal-and-http-features.md`.
- Extended built-in-plugin preparation so plugin-local docs are copied under
  `built-in-plugins/<plugin-id>/docs/`. README landing pages remain stable and
  link the plugin docs index. An authored `docs/index.md` wins; otherwise the
  assembler generates a heading-based catalog.
- Inspected the existing `cloud-agent-app`, `openai_responses`, and
  `kimi-tools` docs. They contain public user/development guidance and target
  specifications, not credential values or private operational material, so
  no current page was excluded. `AGENTS.md` remains recursively excluded.
- Existing task/evidence links inside development specifications remain
  development context. They were not copied into user guides by this work.

## Completion Notes

Completed the application and plugin documentation migration without a broad
configuration or plugin-system rewrite.

Verification:

- Docs-site preparation tests: 15 passed, including plugin recursive copying,
  generated-index fallback, authored-index precedence, link rewriting, and
  `AGENTS.md` exclusion.
- Focused application config/plugin behavior:
  `test_application_layer_config.py`, `test_application_layer_plugins.py`, and
  `test_plugin_is_enabled.py`: 32 passed.
- Documented quickstart response:
  `test_get_api_hello_matches_python_bonjour_shape`: passed.
- Production `prepare_mkdocs_site.py`: passed.
- Normal MkDocs build: passed with the repository's existing Griffe and
  mkdocs-autorefs warnings. Absolute root-site link notices are informational.
- Local-URL Astro build and live landing/docs Playwright smoke: passed,
  including the generated cloud-agent plugin docs index and deep authoring
  guide.
- Generated LLM Markdown companions exist for application quickstart/config
  and representative plugin-local docs.
- Repository search found no remaining live references to
  `docs/plugins/application-config.md`, `docs/plugins/development.md`, or root
  `DEVELOPMENT.md` outside task/archive history.
- Ruff and `git diff --check`: passed.

Compatibility mappings for subtask 060:

- source `docs/plugins/application-config.md` and public
  `/plugins/application-config/` move to
  `application/python/docs/configuration.md` and
  `/packages/application-python/configuration/`;
- source `docs/plugins/development.md` and public `/plugins/development/` move
  to `plugins/docs/overview.md` and `/plugin-development/overview/`;
- root `DEVELOPMENT.md` moves to
  `application/python/docs/development/terminal-and-http-features.md`; no
  prepared-site route existed for the root file, but repository links were
  updated.

Remaining work:

- Subtask 060 owns compatibility pages, complete plugin/deep-page menu
  reachability, breadcrumbs, active ancestry, Getting Started, and deployment
  triggers.
- Plugin-local generated catalogs intentionally expose current authored
  documentation without inventing package-specific user indexes. Packages may
  replace generated catalogs with authored `docs/index.md` on touch.
