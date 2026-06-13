# Root AGENTS Fact Audit And Structure Refresh

Audit the root `AGENTS.md` for factual correctness beyond testing guidance, then update the root file so it matches the current repo structure, runtime terminology, plugin layout, and documentation entrypoints. Keep this task focused on investigation, fact-checking, terminology, and the main root `AGENTS.md` update. If the work branches into broader consistency updates across other files, split those into follow-up subtasks numbered `051`, `052`, and so on.

## Requirements checklist

- [x] Audit the stated facts in root `AGENTS.md` across architecture, directories, plugin terminology, docs references, and setup guidance.
- [x] Update root `AGENTS.md` so repo-root `plugins/` is described as the built-in plugin directory used by the current runtime layout.
- [x] Rename `core/python/plugins` in root guidance from “built-in plugins” to `core-packaged plugins`.
- [x] Make clear that `core/python/plugins` is kept primarily for tests, compatibility, and some package-local/core features, and that new plugins should not be placed there without explicit user consent.
- [x] Promote `plugins/docs/` as the current plugin-docs home and demote `docs/plugins/development.md` to older/general-overview status.
- [x] Refresh the main project-area list to include additional important directories such as `desktop/crystal-lattice-control-desktop-rn` and `packages/`.
- [x] Keep `evaluations/` out of the main project-area list for this pass.
- [x] Add a separate section for less central or auxiliary directories with brief descriptions.
- [x] Correct any misleading root setup/workflow guidance that would send contributors to the wrong location or mental model.
- [x] Split any broader follow-up work that requires additional files or deeper investigation into new subtasks `051+` rather than absorbing it into `050`.

Parent Task: `tasks/20260524-test-and-agents-cleanup/000-main.md`

## User decisions already made

- Use `core-packaged plugins` as the approved term for `core/python/plugins`.
- Keep `plugins/` as the built-in plugin directory in root guidance.
- Treat `core/python/plugins` as an older core-packaged location that still exists for tests, compatibility, and some package-local/core features.
- New plugins should not be placed under `core/python/plugins` without explicit user consent.
- Promote `plugins/docs/` over `docs/plugins/development.md`.
- Include `desktop/` and `packages/` in the main project-area list.
- Do not promote `evaluations/` into the main project-area list in this pass.
- Less important directories may be listed separately with short descriptions.

## Findings already verified before implementation

### 1. Built-in plugin terminology is wrong in root `AGENTS.md`

Root `AGENTS.md` currently treats `core/python/plugins` as the built-in plugin location:

- `AGENTS.md:17`
- `AGENTS.md:79-83`
- `AGENTS.md:168-171`
- `AGENTS.md:197-200`
- `AGENTS.md:217`
- `AGENTS.md:239-243`

That no longer matches runtime behavior:

- `core/python/agent_app/config.py:19-27`
  - `_default_builtin_plugins_dir()` resolves built-in plugins to repo-root `plugins/`.
- `application/python/README.md:248-250`
  - `BUILTIN_PLUGINS` points at bundled plugin sources in binary installs.
- `application/python/README.md:683-684`
  - the binary bundle includes sanitized built-in plugin project directories from repo-root `plugins/`.

Repo-root `plugins/` also contains the active built-in plugin projects used by current default configs and bundled runtime layout.

### 2. Root plugin docs references are stale in emphasis

Root `AGENTS.md` currently points to:

- `docs/plugins/development.md` as the plugin guide
- `plugins/docs/provider-plugins.md` as the canonical provider guide

Current repo shape is broader:

- `plugins/docs/index.md`
  - current shared plugin-docs index
- `README.md:282-293`
  - root README already promotes the richer `plugins/docs/*` pages
- `plugins/docs/AGENTS.md:132-138`
  - explicitly says `docs/plugins/development.md` should remain as a general overview and should not be treated as the primary replacement for newer shared docs

Conclusion:

- `plugins/docs/` should be promoted as the main current plugin-docs home
- `docs/plugins/development.md` should still be referenced, but as an older/general overview

### 3. Application plugins are now a first-class plugin type and root `AGENTS.md` does not mention them

- `core/python/agent_app/app_plugins.py:3-12`
  - defines the `ApplicationPlugin` protocol and explains that application plugins operate at the application layer
- `plugins/docs/application-plugins.md:1-10`
  - documents application plugins as a dedicated plugin category

Root `AGENTS.md` plugin-development summary currently only describes:

- provider plugins
- provider extensions
- feature plugins
- tool plugins

The root guide should be updated so contributors are not steered away from the application-plugin path when that is the correct layer.

### 4. Setup wording in root `AGENTS.md` is misleading for repo development

Current root setup section says:

- `cd core/python && pip install -e ".[dev]"` as “Core + plugins”
- `cd application/python && pip install -e .`

Problems:

- repo-root plugin packages are not installed by `core/python[dev]`
- application source-install guidance in `application/python/README.md:75-88` installs local `core/python` first
- the current wording can imply that editable local core/application/plugin development is covered when it is not

This should be corrected in root `AGENTS.md`, even if broader README fallout is delegated.

### 5. The main project-area list in root `AGENTS.md` is incomplete

Root `AGENTS.md` currently highlights:

- core
- application
- mobile
- bridge
- cloud orchestrator
- plugins
- examples/tests

But the repo also has other active first-class surfaces:

- `desktop/crystal-lattice-control-desktop-rn`
  - active desktop frontend; see `desktop/crystal-lattice-control-desktop-rn/README.md:1-16`
- `packages/`
  - shared frontend/tool-host packages used by mobile and desktop

The user requested that these be added to the main project-area list.

### 6. Less central directories should be documented separately, not mixed into the main product map

The user explicitly wants less important directories to be listed separately.

Candidate examples to consider for a short auxiliary section:

- `evaluations/`
  - shared evaluation framework; see `evaluations/AGENTS.md:1-18`
- `tasks/`
  - task handoff files
- `test_dir/`
  - ad hoc local scratch/test workspace
- `plans/` / `plan/`
  - planning notes and older work artifacts
- `artifacts/`, `build/`, `dist/`, `tmp/`
  - generated or working outputs

This section should stay brief and should not turn into a full repo inventory.

## Scope guard for this task

This task should directly update the root `AGENTS.md` and capture the fact-checked terminology and structure there.

If the investigation shows that other files now need coordinated updates, do not silently expand `050` into a broad multi-file cleanup. Instead:

1. identify the branch of work,
2. create a new follow-up subtask such as:
   - `tasks/20260524-test-and-agents-cleanup/051-...`
   - `tasks/20260524-test-and-agents-cleanup/052-...`
3. add it to `tasks/20260524-test-and-agents-cleanup/000-main.md`,
4. note the relationship clearly in the task files.

Examples of likely follow-up branches:

- root README consistency fallout
- `plugins/AGENTS.md` terminology alignment
- plugin docs landing-page reshaping beyond root `AGENTS.md`
- setup/install guidance cleanup across multiple READMEs

## Suggested implementation steps

1. Re-read the current root `AGENTS.md` end-to-end and classify each major section as accurate, misleading, stale, or incorrect.
2. Rewrite the top-level overview and architecture sections so the project map reflects the current important repo areas.
3. Replace the current plugin terminology:
   - built-in plugins → repo-root `plugins/`
   - core-packaged plugins → `core/python/plugins`
4. Add clear contributor steering for `core/python/plugins`:
   - still present
   - used for tests/compatibility/some package-local features
   - not the default destination for new plugin work
5. Promote `plugins/docs/` as the current plugin-docs home and reposition `docs/plugins/development.md` as a general overview.
6. Update the plugin-development summary so it includes `ApplicationPlugin` and does not overstate older assumptions about where plugin implementations belong.
7. Correct misleading setup/workflow guidance where the root file currently implies broader editable install coverage than it actually provides.
8. Add a short auxiliary-directories section separate from the main project list.
9. Decide whether any discovered fallout belongs in `050` or should be split into `051+` subtasks.
10. Validate the final root `AGENTS.md` against:
   - actual repo layout
   - `BUILTIN_PLUGINS` runtime behavior
   - current plugin docs organization
   - active desktop/shared-package surfaces

## References worth checking during execution

- `AGENTS.md`
- `README.md`
- `plugins/AGENTS.md`
- `plugins/docs/index.md`
- `plugins/docs/AGENTS.md`
- `plugins/docs/application-plugins.md`
- `docs/plugins/development.md`
- `core/python/agent_app/config.py`
- `core/python/agent_app/app_plugins.py`
- `application/python/README.md`
- `desktop/crystal-lattice-control-desktop-rn/README.md`
- `evaluations/AGENTS.md`

## Execution plan

Added during task completion.

1. Re-audit the current root `AGENTS.md` against the verified repo/runtime facts already captured in this task.
2. Rewrite the project overview and architecture sections so the main repo areas reflect current reality, including `desktop/` and `packages/`, while keeping `evaluations/` out of the main list for this pass.
3. Replace the outdated plugin taxonomy with:
   - built-in plugins → repo-root `plugins/`
   - core-packaged plugins → `core/python/plugins`
4. Add explicit steering that `core/python/plugins` is kept primarily for tests, compatibility, and some package-local/core features, and that new plugins should not be placed there without explicit user consent.
5. Promote `plugins/docs/` as the current plugin-docs home and reposition `docs/plugins/development.md` as an older/general overview.
6. Update the plugin-development summary so it includes `ApplicationPlugin` and does not overstate older assumptions about required hooks or the default destination for new plugin work.
7. Correct misleading setup/workflow guidance where the root file currently implies broader editable-install coverage than it actually provides.
8. Add a short auxiliary-directories section for less central areas such as `evaluations/`, `tasks/`, `test_dir/`, and generated working directories.
9. If implementation reveals broader consistency fallout in other repo docs, create `051+` follow-up subtasks instead of silently broadening `050`.
10. Validate the updated root `AGENTS.md` against current repo layout, `BUILTIN_PLUGINS` runtime behavior, and active desktop/shared-package surfaces.

## Completion Notes

Added during task completion.

- Updated the root `AGENTS.md` to reflect the current repo structure, including:
  - built-in plugin projects under repo-root `plugins/`
  - `core/python/plugins` renamed to `core-packaged plugins`
  - active desktop and shared-package surfaces in the main project map
  - a separate auxiliary-directories section for less central areas
- Reworked the plugin sections so they now:
  - promote `plugins/docs/` as the current plugin-docs home
  - keep `docs/plugins/development.md` as an older/general overview
  - include `ApplicationPlugin` as a first-class plugin type
  - steer new first-party plugin work toward repo-root `plugins/`
  - explicitly warn against adding new plugins under `core/python/plugins` without user consent
- Corrected the root setup guidance so it no longer implies that `core/python[dev]` installs repo-root plugin packages.
- The investigation surfaced broader consistency fallout outside the root file, so two follow-up subtasks were created instead of broadening `050`:
  - `tasks/20260524-test-and-agents-cleanup/051-plugin-terminology-and-docs-entrypoint-alignment.md`
  - `tasks/20260524-test-and-agents-cleanup/052-setup-and-install-guidance-alignment.md`
- Validation performed:
  - reread the updated root `AGENTS.md`
  - checked the new terminology against `BUILTIN_PLUGINS` runtime behavior
  - confirmed no whitespace or patch formatting issues with `git diff --check`
