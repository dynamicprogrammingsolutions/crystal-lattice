# Setup And Install Guidance Alignment

Align setup, editable-install, and contributor workflow guidance outside the root `AGENTS.md` so developers are not misled about what gets installed from `core/python`, `application/python`, and repo-root plugin packages.

## Requirements checklist

- [x] Audit setup/install guidance in the main repo docs for misleading editable-install wording.
- [x] Clarify where local source installs require installing `core/python` before `application/python`.
- [x] Clarify that repo-root plugin packages are installed separately when actively changing them.
- [x] Update only the docs that are directly inconsistent with the setup guidance corrected in task `050`.
- [x] Record any remaining package-specific install oddities that should be handled in a later package-local pass.

Parent Task: `tasks/20260524-test-and-agents-cleanup/000-main.md`

Depends On: `tasks/20260524-test-and-agents-cleanup/050-root-agents-fact-audit-and-structure-refresh.md`

## Why this exists

Task `050` corrects the root `AGENTS.md`, but broader setup/install wording is still inconsistent elsewhere:

- `application/python/README.md:75-88`
  - source-install guidance installs local `core/python` before `application/python`
- `core/python/README.md`
  - documents `core/python` installation from within that package
- `plugins/AGENTS.md:22-33`
  - documents plugin-package installation as a separate step
- repo-level docs can still imply that `core/python[dev]` covers more of the repo than it actually does

This follow-up should align those repo docs after the root guidance is settled.

## Likely files to inspect

- `README.md`
- `application/python/README.md`
- `core/python/README.md`
- `plugins/AGENTS.md`

## Notes

- Keep this task focused on contributor setup/install guidance.
- Do not expand it into broader package README cleanup unless the inconsistency is directly tied to editable-install workflow.

## Execution plan

Added during task completion.

1. Update the root contributor setup wording in `README.md` so it clearly separates local `core/python`, `application/python`, and repo-root plugin editable installs.
2. Tighten `application/python/README.md` source-install guidance so it explicitly states that local app development installs `core/python` first and still does not install repo-root plugin packages.
3. Clarify in `core/python/README.md` that its source and development install commands cover only the core SDK package, not the terminal app or repo-root plugin packages.
4. Refine `plugins/AGENTS.md` setup guidance so it reinforces that plugin packages are installed separately, with local `core/python` as the prerequisite and `application/python` added only when app-level integration is needed.
5. Keep the pass limited to docs directly inconsistent with task `050`, and record any remaining package-local install oddities for later follow-up rather than broadening scope here.
6. Validate the updated wording for consistency across the touched files, then update task status and completion notes.

## Completion Notes

Added during task completion.

- Updated the contributor setup/install wording in:
  - `README.md`
  - `application/python/README.md`
  - `core/python/README.md`
  - `plugins/AGENTS.md`
- The updated wording now consistently states:
  - local source work on `application/python` installs `core/python` first
  - `core/python` install commands only cover the core SDK package
  - repo-root plugin packages are installed separately when actively changing them
  - `application/python` is only an extra editable install when plugin work needs app-level integration
- Remaining package-local install oddities noted for later follow-up rather than changed here:
  - `plugins/template-python-provider/README.md`
  - `plugins/template-python-tools/README.md`
  - `plugins/template-bash-tool/README.md`
  - `plugins/openai_responses/README.md`
  - `plugins/reference-openai-compatible-provider/README.md`
  - `plugins/gemini-compaction-app/README.md`
  - `plugins/web-fetch-shared/README.md`
- Validation performed:
  - reread the edited sections for wording consistency with task `050`
  - confirmed the pass stayed limited to the directly inconsistent docs named by this task