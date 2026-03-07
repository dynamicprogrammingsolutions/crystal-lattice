# Native history preservation and single-provider application cores

Short description: Plan and implement a change so normal message operations never silently strip provider-native history, and make the application construct/use cores with exactly one provider when the effective application config already selects one.

## Background

We investigated why deleting messages could remove `metadata.native_messages_integrity` and per-message `metadata.native_indices` even when the session had valid native history.

Key findings:

1. Normal delete flows all route through `AgentCore.slice_session()`.
   - Terminal delete calls `core.slice_session(...)` at `application/python/agent_terminal_app/terminal_app.py:418`.
   - HTTP delete calls `core.slice_session(...)` at `application/python/agent_terminal_app/server.py:1880`.
   - Session-actions app delete calls `core.slice_session(...)` at `plugins/session-actions-app/src/session_actions_app/__init__.py:599`.

2. `slice_session()` currently has many silent fallbacks to `_slice_session_core_only()`, which strips native history.
   - Core-only stripping helper: `core/python/agent_core/core.py:721-773`.
   - Main fallback gate: `core/python/agent_core/core.py:842-847`.
   - Additional fallback branches for invalid/missing native state: `core/python/agent_core/core.py:849-957`.

3. `fork_session()` inherits this behavior because it is a thin wrapper over `slice_session()`.
   - `core/python/agent_core/core.py:988-1009`

4. `modify_message()` also still contains a core-only path that drops native history.
   - Core-only modify helper branch: `core/python/agent_core/core.py:431-476`
   - Public method: `core/python/agent_core/core.py:694-719`

5. `join_sessions()` silently downgrades to core-only when config/native history is incomplete.
   - `core/python/agent_core/core.py:1011-1083`

6. The application currently builds cores with all enabled providers, not necessarily the one selected by the effective request config.
   - `AgentApplication._build_core_with_enabled_ids()` registers all enabled providers at `core/python/agent_app/application_future.py:258-300`.
   - `AgentApplication.load_session()` uses that helper at `core/python/agent_app/application_future.py:924-955`.
   - In the reproduced case, this caused `len(self._providers) != 1` in `slice_session()` and triggered the stripping fallback.

## Desired outcome

Two distinct but related changes are wanted:

1. **Core semantics change:** normal message operations must preserve native history or fail explicitly. Silent stripping should only be possible via an explicit opt-in such as `core_only_operation=True`.
2. **Application/provider selection change:** when the effective application config already selects a provider, application-built cores used for message operations should contain only that provider.

## Suggested work split

Subtasks:

1. `tasks/20260307-native-history-preservation-and-single-provider/010-no-silent-native-history-stripping.md`
2. `tasks/20260307-native-history-preservation-and-single-provider/020-application-single-provider-core-selection.md`

These subtasks are related but can largely be researched/implemented independently. Coordinate the final behavior so they do not fight each other:

- Subtask 010 changes the **core contract** from “preserve when possible, otherwise silently strip” to “preserve or fail unless explicitly forced core-only”.
- Subtask 020 reduces one major source of preservation failures by ensuring application-built cores carry only the provider actually selected by config.

## Notes for the implementing agent

- Update tests as part of the change. Current tests still encode fallback-stripping behavior in some places.
- Be careful to update both core-layer tests and application-layer tests.
- User-facing adapters should translate the new explicit core errors into user-facing errors (`TerminalUserError`, HTTP 400, or application action `ValueError`) rather than leaking internal failures.
