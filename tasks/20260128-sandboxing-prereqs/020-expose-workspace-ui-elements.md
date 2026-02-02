Parent Task: tasks/20260128-sandboxing-prereqs/000-main.md
Depends On: tasks/20260128-sandboxing-prereqs/010-standardize-workspace-path-semantics.md

# Expose Workspace UI Elements (`working_directory`, optional `allowed_paths`)

Make the active workspace visible/editable in UI-driven settings (terminal `/set`, mobile SessionSettingsModal) by ensuring `working_directory` appears in `/sessions/{id}/ui-schema` as a config UI element.

## Current state

- Core aggregates UI elements from provider/feature/tool plugins only:
  - `core/python/agent_core/core.py:1998`

- Codex tools define `working_directory` in config schema but return no UI elements:
  - `plugins/codex-tools/src/codex_tools/shell_tool.py:57`
  - `plugins/codex-tools/src/codex_tools/apply_patch_tool.py:491`

- Mobile settings UI renders config elements from session UI schema:
  - `mobile/crystal-lattice-control-rn/src/components/SessionSettingsModal.tsx:72`

## Goal

Add a UI schema entry such that UIs show something like:

- Label: “Working directory”
- Key: `working_directory`
- Type: `string` (or `text`)

Optionally expose `allowed_paths` (advanced) but it may be preferable to keep it hidden in the first iteration to reduce foot-guns.

## Viable implementation options

1) **Preferred:** add UI elements in the codex-tools plugins.

- Pros: no new plugin required; matches where the config keys are already defined.
- Cons: multiple tools contribute the same key; core de-dupes config UI by key (later wins). Ensure consistent ordering.

2) Add a tiny “workspace config UI” feature plugin that only contributes UI elements.

- Pros: single owner of workspace UI; avoids tool duplication.
- Cons: adds another plugin to deploy/enable.

## Acceptance criteria

- `GET /sessions/{session_id}/ui-schema` includes a config element with `key == "working_directory"`.
- Terminal `/help config` and mobile settings show it (no additional frontend changes if the element is present).

## Tests

- Add a server-level test in `application/python/tests` verifying that `working_directory` appears in session UI schema when codex-tools are enabled.
  - Relevant route: `application/python/agent_terminal_app/server.py:617`
