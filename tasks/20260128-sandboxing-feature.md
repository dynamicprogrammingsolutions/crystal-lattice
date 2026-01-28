# Sandboxing Feature (Local Git Clone Workspace)

Implement a “sandbox workspace” feature for the AI agent application, starting with **Option 2 (local clone into a temporary directory)**, as an **application plugin**. The plugin should allow a user to move a session into a sandboxed working directory (a local clone of the current Git repo), let the agent work there (including creating branches/commits in the sandbox clone), and later exit/export work back to the original repository.

This task is intended to be resumed in a fresh conversation after prerequisites are completed.

## Related prerequisite tasks (must be completed first)

These are tracked in:

- `tasks/20260128-sandboxing-prereqs/000-main.md`

Key prerequisite subtasks (all paths are required dependencies for a clean implementation):

- `tasks/20260128-sandboxing-prereqs/010-standardize-workspace-path-semantics.md`
- `tasks/20260128-sandboxing-prereqs/020-expose-workspace-ui-elements.md`
- `tasks/20260128-sandboxing-prereqs/030-add-session-override-helper-apis.md`
- `tasks/20260128-sandboxing-prereqs/040-session-aware-app-plugin-ui-and-conditions.md`
- `tasks/20260128-sandboxing-prereqs/050-app-plugin-lifecycle-hooks-for-cleanup.md`

## Context (what exists today)

### Application plugins and actions

- The application layer supports **application plugins** with:
  - action definitions (`get_actions`) and execution (`execute_action`)
  - plugin-contributed application UI schema (`get_ui_elements`)
  - wiring into the HTTP server via `POST /actions`.

Relevant code:

- Application plugin protocol: `core/python/agent_app/app_plugins.py:22`
- App plugin wrapper: `core/python/agent_app/app_plugins.py:101`
- App plugin actions + UI schema aggregation: `core/python/agent_app/application_future.py:700`
- HTTP endpoint for actions: `application/python/agent_terminal_app/server.py:1971`

### Per-session overrides

- Sessions can store per-session configuration overrides under `session.metadata["overrides"]`.
- Both terminal and HTTP flows merge overrides into the effective request config.

Relevant code:

- Terminal request applies overrides: `application/python/agent_terminal_app/terminal_app.py:619`
- Server send-request worker merges stored overrides + HTTP overrides: `application/python/agent_terminal_app/server.py:506`
- Overrides endpoints exist:
  - `GET /sessions/{session_id}/overrides`: `application/python/agent_terminal_app/server.py:768`
  - `PATCH /sessions/{session_id}/overrides`: `application/python/agent_terminal_app/server.py:797`
  - `DELETE /sessions/{session_id}/overrides/{key}`: `application/python/agent_terminal_app/server.py:922`

### Workspace-related config keys already used by tools/features

- Codex tools are configurable with `working_directory` and `allowed_paths`.
  - `shell`: `plugins/codex-tools/src/codex_tools/shell_tool.py:36`
  - `apply_patch`: `plugins/codex-tools/src/codex_tools/apply_patch_tool.py:478`

- `feature-file-context` also uses `working_directory`/`allowed_paths` and already resolves allowlists relative to `working_directory`.
  - `plugins/feature-file-context/src/feature_file_context/file_context_feature.py:125`

### Current sharp edges (why prerequisites exist)

- Codex tools currently resolve `allowed_paths` relative to process CWD (not `working_directory`), which makes switching workspaces brittle:
  - `plugins/codex-tools/src/codex_tools/shell_tool.py:156`
  - `plugins/codex-tools/src/codex_tools/apply_patch_tool.py:636`

- Codex tools currently do **not** expose UI elements for `working_directory` (so UIs can’t show/edit it without extra work):
  - `plugins/codex-tools/src/codex_tools/shell_tool.py:57`

## Feature goal

Provide a plugin-driven workflow:

1) **Enter sandbox**
   - Create a temp directory.
   - Create a local clone of the *current local repository* into that directory.
   - Switch this session’s effective workspace to that clone by updating per-session overrides.

2) **Work in sandbox**
   - The agent uses file/shell tools against the sandbox working directory.
   - The agent may create branches/commits inside the sandbox clone.

3) **Exit sandbox / export results** (mechanism TBD; tracked as follow-up)
   - User may choose to:
     - keep commits and bring them back (e.g. `format-patch`, `bundle`, `fetch`), or
     - transfer working-tree changes back (e.g. `git diff --binary` + `git apply --3way`).

## Security model (assumptions)

- This feature is primarily an **organizational sandbox** (separate clone directory + tool allowlist), not a hardened OS sandbox.
- The agent should only be granted filesystem access within the sandbox directory via `allowed_paths`.

If a stronger adversarial model is desired later, it will require OS/container-level isolation (out of scope here).

## Option 2 (initial implementation): local clone workflow

### High-level approach

- Implement a new **application plugin** (new plugin package under `plugins/`), e.g. `plugins/sandboxing-app`.
- Store sandbox state in `session.metadata` (not in global process state), so it survives restarts and is inspectable by frontends.

Suggested metadata shape (finalize during implementation):

- `session.metadata["sandbox"] = {
    "active": true,
    "original_repo": "/abs/path/to/original",
    "sandbox_dir": "/abs/path/to/temp/clone",
    "created_at": "...",
    "mode": "clone",
    "notes": "...",
  }`

Suggested overrides set while active:

- `session.metadata["overrides"]["working_directory"] = sandbox_dir`
- `session.metadata["overrides"]["allowed_paths"] = [sandbox_dir]` (absolute)

### Required application actions

Implement these actions on the application plugin:

- `enter_sandbox`
  - params: `{ "session_id": string, "branch": optional string, "source": optional string }`
  - creates the clone and updates session overrides + metadata

- `exit_sandbox`
  - params: `{ "session_id": string, "cleanup": boolean }`
  - clears overrides and marks sandbox inactive; cleanup behavior depends on lifecycle hooks

- `sandbox_status` (optional)
  - returns whether active and key paths

Do **not** implement transfer/export in this task; only set the stage and ensure the agent can operate in the sandbox directory safely.

### Git operations for clone (local-only)

Preferred for safety/isolation:

- `git clone --no-hardlinks <original_repo> <sandbox_dir>`

Avoid `--shared` / alternates; avoid hardlinks.

After clone:

- Optionally checkout a new branch: `git -C <sandbox_dir> checkout -b agent/sandbox-<id>`

### Policy/guardrails

- Only allow sandbox dirs under a configured base directory (e.g. `~/.crystal/sandboxes` or a config setting).
- Always store absolute paths.
- Never delete directories outside the sandbox base.
- If `session.metadata["sandbox"]` is active but the directory is missing, surface a clear status/error and offer to “reset”.

## Future alternatives to keep in mind (not implemented now)

### Option 1: `git worktree`

- Pros: fast, low disk.
- Cons: shares `.git` metadata/refs; weaker isolation; still workable as a future mode.

### Option 3: `git archive` / patch-only

- Pros: minimal footprint; simplest to restrict (no git operations in sandbox).
- Cons: no branching/committing within sandbox.

The plugin design should keep a `sandbox.mode` field (e.g., `clone`, `worktree`, `archive`) to support these later.

## UI expectations

- User triggers actions via frontends:
  - Terminal can call `POST /actions`.
  - Mobile already supports listing/executing application actions:
    - `mobile/crystal-lattice-control-rn/src/api.ts:361`

Prerequisite tasks should enable:

- `working_directory` appearing in session UI schema and thus visible in:
  - terminal `/set` help output
  - mobile session settings modal.

## Acceptance criteria (after prerequisites)

- A user can call `enter_sandbox` and the session’s effective workspace changes.
- Tools operate within the sandbox directory (read/write/patch/shell) and are blocked from escaping by `allowed_paths`.
- A user can call `exit_sandbox` and return the session’s workspace to the original repo.
- Metadata + events make state changes observable to clients.

## Follow-up task (explicitly out of scope here)

Implement “transfer changes back” workflows (patch export/apply, `format-patch`/`am`, or `bundle`/`fetch`). This should be tracked separately once the workspace switching and safety model are in place.
