Parent Task: tasks/20260128-sandboxing-prereqs/000-main.md

# Add Session Override Helper APIs (Application Layer)

Reduce duplication and make sandbox plugins safer by adding small, standard helper methods on `AgentApplication` for manipulating per-session overrides.

## Current state

- Overrides live at `session.metadata["overrides"]`.
- Several codepaths implement the same pattern:
  - acquire lock → load session → update metadata → save session → publish event → record checkpoint.
  - Terminal command implementation: `application/python/agent_terminal_app/terminal_app.py:982`
  - HTTP implementation: `application/python/agent_terminal_app/server.py:797`
  - Application plugins do their own lock/load/save/event patterns (e.g. title plugin): `plugins/session-title-app/src/session_title_app/__init__.py:176`

## Goal

Add methods to `core/python/agent_app/application_future.py`:

- `patch_session_overrides(session_id: str, updates: Dict[str, Any]) -> Session`
- `delete_session_override(session_id: str, key: str) -> Session`
- (optional) `get_session_overrides(session_id: str) -> Dict[str, Any]`

These helpers should:

- Acquire `AgentApplication.acquire_session_lock(session_id)`.
- Load session (404/KeyError semantics are handled by caller).
- Update `metadata["overrides"]` immutably.
- Save the updated session.
- Publish a standard event (proposal):
  - `type: "session_overrides_updated"`
  - `session_id`
  - `keys`: list of updated/removed keys

## Why this is a prerequisite for sandboxing

A sandbox plugin needs to atomically update at least:

- `working_directory`
- `allowed_paths`

…and it should do so with consistent locking/eventing semantics shared with terminal and HTTP flows.

## Follow-up refactors (optional)

- Update terminal `/set` and server override endpoints to call these helpers.

## Tests

- Add unit tests in `core/python/tests` for the new helper(s).
- Optionally update `application/python/tests/test_agent_terminal_app_server.py` to ensure server endpoints still work if refactored.
