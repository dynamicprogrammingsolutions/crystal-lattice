# Plugin Terminology And Docs Entrypoint Alignment

Align repo-level documentation outside the root `AGENTS.md` so plugin terminology, built-in plugin location, and plugin-doc entrypoints stay consistent with the updated root guidance from task `050`.

## Requirements checklist

- [x] Audit repo docs that still describe repo-root `plugins/` as merely optional or describe `core/python/plugins` as the built-in plugin directory.
- [x] Align plugin terminology across the affected docs with:
  - built-in plugin projects → repo-root `plugins/`
  - core-packaged plugins → `core/python/plugins`
- [x] Promote `plugins/docs/` as the current plugin-docs home in the affected docs.
- [x] Keep `docs/plugins/development.md` referenced as an older/general overview where appropriate.
- [x] Update only the docs that are directly inconsistent with the terminology changes from task `050`.

Parent Task: `tasks/20260524-test-and-agents-cleanup/000-main.md`

Depends On: `tasks/20260524-test-and-agents-cleanup/050-root-agents-fact-audit-and-structure-refresh.md`

## Why this exists

Task `050` updates the root `AGENTS.md`, but the investigation already showed repo-level fallout in other docs:

- `README.md:282-293`
  - already promotes `plugins/docs/*`
- `README.md:379-390`
  - still describes `core/python/plugins` as built-in and `plugins/` as optional
- `plugins/AGENTS.md:1-15`
  - currently describes `plugins/` as optional plugin repositories
- `plugins/docs/AGENTS.md:132-138`
  - already frames `docs/plugins/development.md` as a general overview rather than the primary current doc set

This follow-up should keep those repo docs aligned with the updated root terminology without mixing that broader doc sweep into task `050`.

## Likely files to inspect

- `README.md`
- `plugins/AGENTS.md`
- `plugins/docs/index.md`
- `plugins/docs/AGENTS.md`
- `docs/plugins/development.md`

## Notes

- Keep the distinction clear that repo-root `plugins/` includes built-in plugin projects, templates, and shared docs.
- Avoid over-correcting into language that implies every subtree under `plugins/` is a runtime-loaded built-in plugin package.

## Execution plan

Added during task completion.

1. Re-audit the doc set already identified by this task:
   - `README.md`
   - `plugins/AGENTS.md`
   - `plugins/docs/index.md`
   - `plugins/docs/AGENTS.md`
   - `docs/plugins/development.md`
2. Update only the docs that are directly inconsistent with task `050` so terminology matches:
   - built-in plugin projects -> repo-root `plugins/`
   - core-packaged plugins -> `core/python/plugins`
3. Promote `plugins/docs/` and especially `plugins/docs/index.md` as the current plugin-docs entrypoint in the affected docs, while keeping `docs/plugins/development.md` positioned as an older/general overview.
4. Keep wording careful so it does not imply that every subtree under `plugins/` is a runtime-loaded plugin package.
5. Re-read the changed docs together and run a lightweight validation pass so this task stays separate from the setup/install guidance cleanup tracked in `052`.

## Completion Notes

Added during task completion.

- Updated `README.md` so it now:
  - points readers to `plugins/docs/index.md` before individual plugin-doc pages,
  - keeps `docs/plugins/development.md` labeled as an older/general overview,
  - describes `core/python/plugins` as core-packaged plugins,
  - describes repo-root `plugins/` as the home of built-in plugin projects for the current runtime layout, plus templates and shared docs.
- Updated `plugins/AGENTS.md` so it no longer describes repo-root `plugins/` as optional and now points contributors first to `plugins/docs/index.md`.
- Expanded `plugins/docs/index.md` into a clearer docs entrypoint by adding framing text plus links for feature and application plugin docs, while keeping the older overview linked.
- Updated `docs/plugins/development.md` to explicitly position it as an older/general overview and to point readers to the current `plugins/docs/index.md` entrypoint.
- Inspected `plugins/docs/AGENTS.md` during the audit and left it unchanged because its guidance was already aligned with task `050`.
- Validation completed:
  - reread the changed sections in all touched docs,
  - ran `git diff --check` with no reported formatting issues.