Parent Task: tasks/20260728-package-local-documentation-standard/000-main.md

Depends On:

- `tasks/20260728-package-local-documentation-standard/010-documentation-standard-and-agent-guidance.md`
- `tasks/20260728-package-local-documentation-standard/020-package-docs-site-assembly.md`

Specification:
`maintainer/specifications/documentation-and-specification-standard/index.md`

Requirement IDs:
`DOCREP-002`, `DOCREP-004`, `DOCMIG-002`, `DOCPUB-006`

# Application and Plugin Documentation Migration

Create application package documentation entry points and relocate
ownership-clear application configuration, terminal/runtime development, and
shared plugin overview documentation with bounded verification.

## Requirements checklist

- [ ] `application/python` has package documentation entry points required by
  the approved public-package profile.
- [ ] `docs/plugins/application-config.md` is relocated to
  `application/python/docs/configuration.md` or another approved
  application-owned path.
- [ ] Configuration keys and examples touched by the move are checked against
  current config loading, default configuration, or existing tests.
- [ ] `docs/plugins/development.md` is relocated to `plugins/docs/overview.md`
  or another approved shared-plugin location.
- [ ] The shared plugin overview remains an overview and points to current
  detailed plugin docs instead of duplicating them.
- [ ] Root `DEVELOPMENT.md` is inspected and either relocated to root
  cross-package development docs, moved under application development docs, or
  retained/deferred with explicit rationale.
- [ ] Existing `plugins/docs/AGENTS.md` guidance is updated to reflect the new
  canonical overview location and repository documentation standard.
- [ ] Existing inbound links and public paths are recorded for subtask 060.
- [ ] No broad application configuration or plugin system rewrite is performed
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

Status: Draft

1. Add concise `application/python/AGENTS.md`, `docs/index.md`, and
   `docs/quickstart.md` using the existing README and verified docs.
2. Move application configuration documentation and spot-check touched
   configuration claims.
3. Move the older/general plugin overview into `plugins/docs/`, update its role
   and links, and preserve detailed current plugin pages.
4. Inspect `DEVELOPMENT.md` scope and referenced paths, then choose the
   approved root/application destination or defer with rationale.
5. Update relevant package and plugin agent guidance.
6. Record inbound links and public compatibility requirements for subtask 060.

### Implementation decisions and open questions

- Application ownership of configuration docs and shared `plugins/docs/`
  ownership of the plugin overview are approved.
- The final location of `DEVELOPMENT.md` is a bounded design decision:
  - use root `docs/development/` if it remains substantially cross-package;
  - use `application/python/docs/development/` if it primarily describes the
    terminal/runtime application;
  - defer rather than force a misleading owner.
- No requirement questions are open.

### Documentation

- `application/python/AGENTS.md`
- `application/python/docs/index.md`
- `application/python/docs/quickstart.md`
- `application/python/docs/configuration.md`
- `plugins/docs/overview.md`
- root or application development destination for `DEVELOPMENT.md`
- updated plugin documentation routing

### Task checklist

- [ ] Create application package entry points.
- [ ] Move and verify application configuration guide.
- [ ] Move and normalize shared plugin overview.
- [ ] Classify and handle root `DEVELOPMENT.md`.
- [ ] Update package/plugin agent guidance.
- [ ] Record inbound links and compatibility needs.

### Requirement verification

| Requirement group | Acceptance evidence |
|---|---|
| Application entry points | README/AGENTS/docs index/quickstart provide concise installation, first-run, detailed-doc, and development routes. |
| Configuration guide | Touched keys and examples align with current config loader/default config or focused existing tests. |
| Plugin overview | Canonical shared overview lives under `plugins/docs/` and points to current detailed pages without duplicating them. |
| Development guide ownership | Completion notes record destination and bounded verification, or explicit defer rationale. |

### Additional implementation verification

- Run focused config parsing/schema tests only where moved claims require them.
- Search all links to old configuration/plugin/development paths.
- Inspect generated application and plugin docs output from the site assembler.
