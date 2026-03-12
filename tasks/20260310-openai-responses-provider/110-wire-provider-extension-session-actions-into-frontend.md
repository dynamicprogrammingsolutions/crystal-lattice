# Wire Provider-Extension Session Actions Into Frontend

Short description: Surface provider-extension-owned `session_action` and `message_action` UI elements in the frontend action lists, and make sure those actions execute through the existing action flow with `action_owner` and session-scoped parameters preserved.

Parent Task: `tasks/20260310-openai-responses-provider/000-main.md`

Depends On:
- `tasks/20260310-openai-responses-provider/095-native-compaction-provider-extension.md`

## Why this follow-up exists

Subtask `095` added backend support for provider-extension session actions and verified that:

1. provider extensions can contribute `session_action` UI elements via per-session UI schema
2. `POST /actions` can execute those actions through the new `action_owner: "provider_extension"` routing path
3. `openai_responses` native compaction works end-to-end at the backend and provider level

However, the current mobile/frontend wiring does not actually surface those new actions in the visible action menus. The backend is wired; the frontend action source is not.

## Current observed gap

The mobile chat screen currently gets its visible plugin session/message action lists from `useApplicationPlugins()`, not from the session UI schema.

Relevant code inspected:

1. `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx:260`
- `pluginSessionActions` and `pluginMessageActions` come from `useApplicationPlugins()`

2. `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx:440`
- per-session UI schema is loaded through `useSessionUiSchemaController(...)`

3. `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx:453`
- `uiSchemaElements` is available, but is currently used for attachments/footer/status-bar style rendering rather than the visible action button lists

4. `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx:642`
- visible session action definitions are built from `pluginSessionActions`

5. `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx:1478`
- action dispatch for tapped session actions also only searches `pluginSessionActions`

So even though provider-extension actions show up in `/sessions/{id}/ui-schema`, they do not currently appear in the frontend’s visible action menus.

## Backend status at handoff

The backend wiring added in `095` is in place and was explicitly tested.

Relevant files:

1. `application/python/agent_terminal_app/server.py:2678`
- `/actions` reads `action_owner` and dispatches through `AgentApplication.execute_action(...)`

2. `core/python/agent_app/application_future.py:1048`
- `execute_session_action(...)` loads the session, resolves effective config, calls `core.execute_session_action(...)`, saves the session, and returns standard mutation/reload effects

3. `application/python/tests/test_provider_extension_session_actions_endpoints.py:61`
- verifies provider-extension action appears in session UI schema

4. `application/python/tests/test_provider_extension_session_actions_endpoints.py:76`
- verifies `POST /actions` executes the provider-extension session action successfully

This means the remaining missing piece is primarily frontend discovery/integration rather than backend dispatch.

## Goal

Make provider-extension session/message actions usable from the frontend without inventing a separate interaction model.

The intended UX model remains:

1. frontend gets action-shaped UI elements
2. user taps a visible session or message action
3. existing dialog + action runner machinery executes it
4. backend routes to either application action or provider-extension session action based on `action_owner`

## Implementation intent

1. Merge per-session UI-schema action elements into the frontend-visible action lists.
- include `ui_type == "session_action"` and `ui_type == "message_action"` elements from the session UI schema in the action menus shown in the chat screen
- keep existing application-plugin actions working; this should be an additive merge, not a replacement

2. Preserve backend routing metadata.
- ensure `action_owner` survives from session UI schema element -> frontend action element -> `runApplicationAction(...)` request payload -> backend `/actions`
- ensure provider-extension session actions still carry `session_id` and dialog-mapped parameters correctly

3. Keep action source separation clear.
- application-plugin actions may continue to come from `useApplicationPlugins()`
- session-scoped extension actions should come from the per-session UI schema
- if merging requires de-duplication, do it deterministically and preserve session-specific actions when collisions occur

4. Verify visible integration for the native compaction action.
- `openai_responses_native_compaction` should become visible as a session action in the chat screen when the session’s provider/config enables it
- running it from the frontend should use the same existing action dialog/runner path, not a new bespoke UI path

## Questions to resolve during implementation

1. Should session UI schema actions appear only in the session chat screen, or also anywhere else the app shows plugin actions?
2. If both application actions and session UI schema actions share the same `id`, what should win in the merged frontend list?
3. Does the frontend SDK already preserve opaque fields like `action_owner`, or is a small SDK update needed?
4. Should provider-extension actions also be visible in desktop/terminal UIs, or is this subtask mobile/frontend-only?

## Suggested execution plan

1. Inspect the frontend SDK/react helpers used by the mobile app.
- verify how `useApplicationPlugins()`, `useSessionUiSchemaController(...)`, and `runApplicationAction(...)` model action elements
- confirm whether `action_owner` already flows through unchanged

2. Wire session UI schema actions into the visible chat action lists.
- session actions: merge session UI schema `session_action` elements with existing `pluginSessionActions`
- message actions: merge session UI schema `message_action` elements with existing `pluginMessageActions`

3. Add tests at the highest practical layer.
- frontend/unit/integration coverage showing that session UI schema `session_action` elements become selectable/rendered
- action-runner coverage showing that `action_owner: "provider_extension"` is forwarded to backend execution

4. Validate end-to-end with the native compaction action.
- ensure the action becomes visible for an `openai_responses` session
- ensure triggering it from the frontend reaches the backend action path and causes a session reload/update

## Acceptance criteria

1. Provider-extension `session_action` UI elements from session UI schema are visible in the frontend action list.
2. Provider-extension `message_action` UI elements from session UI schema are visible where message actions are shown.
3. Executing one of those actions preserves `action_owner` and reaches the backend session-action path.
4. Existing application-plugin actions continue to work.
5. The `openai_responses` native compaction action is actually usable from the frontend, not only from backend tests.

## References

1. Session chat frontend action sources and dispatch:
- `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx:260`
- `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx:440`
- `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx:642`
- `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx:1478`

2. Backend action routing added in `095`:
- `application/python/agent_terminal_app/server.py:2678`
- `core/python/agent_app/application_future.py:1048`

3. Existing backend tests proving the path works server-side:
- `application/python/tests/test_provider_extension_session_actions_endpoints.py:61`
- `application/python/tests/test_provider_extension_session_actions_endpoints.py:76`

4. Native compaction action implementation that should become visible once frontend wiring is fixed:
- `plugins/openai_responses/src/openai_responses_plugins/openai_responses_native_compaction_extension.py`

5. Preceding subtask with the backend/provider work and completion notes:
- `tasks/20260310-openai-responses-provider/095-native-compaction-provider-extension.md`