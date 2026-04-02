# Sandboxing Prerequisites (Git-local clone workflow)

Design and implement the architectural prerequisites to support a “sandbox workspace” feature as an **application plugin**, starting with **Option 2 (local clone to temp dir)**, while keeping **Option 1 (`git worktree`)** and **Option 3 (`git archive`/patch-only)** as future alternatives.

The intended UX is:

- User triggers an application action like “Enter sandbox”.
- The server creates a temp directory, clones the current local repo into it, and switches the agent’s effective workspace to that directory.
- The agent works in the sandbox (including branch creation/commits inside the sandbox clone).
- User later triggers “Export/transfer changes” (mechanism TBD in a later task).

This task covers **core/app/plugin capabilities** needed so the sandbox feature can be implemented cleanly as a plugin, without scattering ad-hoc logic across frontends.

## What’s Known (Repo Investigation)

### Current capabilities (already present)

- Per-session config overrides exist: stored in `session.metadata["overrides"]` and merged into request config.
  - Terminal: `application/python/agent_terminal_app/terminal_app.py:619`
  - HTTP server: `_run_send_request_background` merges stored + request overrides: `application/python/agent_terminal_app/server.py:506`
  - Endpoints: `GET/PATCH/DELETE /sessions/{id}/overrides...`: `application/python/agent_terminal_app/server.py:768`

- Tools already accept `working_directory` in config, but do not expose UI elements for it.
  - `plugins/codex-tools/src/codex_tools/shell_tool.py:36`
  - `plugins/codex-tools/src/codex_tools/apply_patch_tool.py:478`

- Core UI schema aggregation exists for provider/feature/tool plugins:
  - `AgentCore.get_ui_schema`: `core/python/agent_core/core.py:1998`

- Application plugins already support user-initiated actions and app-level UI schema.
  - Protocol: `core/python/agent_app/app_plugins.py:22`
  - Action/UI export: `core/python/agent_app/application_future.py:700`
  - HTTP action endpoint: `application/python/agent_terminal_app/server.py:1971`

### Gaps / sharp edges

- **No UI schema element exists for `working_directory`** today, so UIs cannot display or edit it.
- `allowed_paths` resolution is inconsistent between plugins:
  - Codex tools resolve `allowed_paths` via `os.path.abspath(p)` relative to process CWD, not `working_directory`:
    - `plugins/codex-tools/src/codex_tools/shell_tool.py:156`
    - `plugins/codex-tools/src/codex_tools/apply_patch_tool.py:636`
  - `feature-file-context` resolves `allowed_paths` relative to `working_directory`:
    - `plugins/feature-file-context/src/feature_file_context/file_context_feature.py:125`

- Application plugins can mutate sessions by load/save, but there is no small, standard helper API for updating overrides.
- Application plugin UI elements are not session-aware (`get_ui_elements(state)` has no session argument), which makes clean “Enter/Exit sandbox” conditional UI hard without frontend conventions.
- Application plugins have no lifecycle hooks for cleanup (important for temp directories).

## Goal

Add minimal core/app/plugin capabilities so a sandbox application plugin can:

- Set and display the agent workspace (`working_directory`) per session.
- Keep filesystem tools working safely by correctly scoping `allowed_paths`.
- Offer robust app actions with predictable visibility and cleanup.

## Subtasks

- [ ] `tasks/20260128-sandboxing-prereqs/010-standardize-workspace-path-semantics.md`
- [ ] `tasks/20260128-sandboxing-prereqs/020-expose-workspace-ui-elements.md`
- [ ] `tasks/20260128-sandboxing-prereqs/030-add-session-override-helper-apis.md`
- [ ] `tasks/20260128-sandboxing-prereqs/040-session-aware-app-plugin-ui-and-conditions.md`
- [ ] `tasks/20260128-sandboxing-prereqs/050-app-plugin-lifecycle-hooks-for-cleanup.md`

## Future Alternatives (not implemented in this task)

- Option 1: `git worktree` sandbox.
  - Pros: fast, low disk.
  - Cons: shared `.git` metadata/refs means weaker isolation.

- Option 3: `git archive` / patch-only sandbox.
  - Pros: simplest/most restrictive (no git operations in sandbox).
  - Cons: no in-sandbox branching/commits.
