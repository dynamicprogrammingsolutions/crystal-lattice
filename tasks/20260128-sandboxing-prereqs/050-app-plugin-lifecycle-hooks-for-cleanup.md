Parent Task: tasks/20260128-sandboxing-prereqs/000-main.md

# Application Plugin Lifecycle Hooks (Sandbox Cleanup)

Support safe cleanup of sandbox temp directories created by the sandbox application plugin.

## Current state

- Application plugins are instantiated once per `AgentApplication` instance.
  - Wrapper: `core/python/agent_app/app_plugins.py:101`

- There are no lifecycle callbacks beyond `init()`.
  - Protocol: `core/python/agent_app/app_plugins.py:22`

For sandboxing, we want the plugin to be able to:

- Cleanup temp clones on app shutdown.
- Optionally, reconcile stale sandboxes on startup (e.g., after crash).

## Goal

Add optional lifecycle hooks to the application plugin protocol and wrapper, for example:

- `shutdown(state) -> None`
- (optional) `on_session_deleted(session_id, state) -> None`

And wire these into application lifecycle:

- `AgentApplication.close()` (new) or into the HTTP/terminal app shutdown events.

## Design considerations

- Hooks must be best-effort and must not crash the application during shutdown.
- Cleanup must respect policy/allowlists (don’t delete arbitrary paths).
- If sandbox directories are referenced in `session.metadata`, cleanup should avoid deleting directories still referenced by other sessions.

## Acceptance criteria

- There is a documented, supported place for a sandbox plugin to delete its temp directories.
- The lifecycle is exercised in at least one test or integration path.
