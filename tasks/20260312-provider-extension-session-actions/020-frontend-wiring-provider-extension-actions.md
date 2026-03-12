# Frontend Wiring For Provider-Extension Actions

Short description: Surface provider-extension-owned `session_action` and `message_action` UI elements in the frontend action menus, and ensure those actions execute through the existing action flow with `action_owner` and session-scoped parameters preserved.

Parent Task: `tasks/20260312-provider-extension-session-actions/000-main.md`

Depends On:
- `tasks/20260312-provider-extension-session-actions/010-core-capability-and-contract.md`
- `tasks/20260310-openai-responses-provider/095-native-compaction-provider-extension.md`

## Origin of this subtask

This subtask folds in and supersedes the narrower draft task:

1. `tasks/20260310-openai-responses-provider/110-wire-provider-extension-session-actions-into-frontend.md`

Use this file as the active follow-up planning document going forward.

## Problem statement

The backend supports provider-extension session actions, but the frontend does not currently show them in the visible action menus.

Backend side is already working:

1. `/sessions/{id}/ui-schema` contains extension-owned `session_action` / `message_action` elements
2. `POST /actions` can execute them through `action_owner: "provider_extension"`

Frontend side is the missing piece:

1. the chat screen still builds visible action menus from application-plugin action sources
2. per-session UI schema is loaded, but not used as the source of visible session/message action buttons

## Current observed frontend gap

Inspected code:

1. `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx:260`
- `pluginSessionActions` and `pluginMessageActions` come from `useApplicationPlugins()`

2. `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx:440`
- per-session UI schema is loaded through `useSessionUiSchemaController(...)`

3. `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx:453`
- session UI schema is available as `uiSchemaElements`

4. `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx:642`
- visible session action definitions are built from `pluginSessionActions`

5. `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx:1478`
- session action dispatch only looks up actions from `pluginSessionActions`

This means provider-extension actions can exist in session UI schema and still never appear in the UI.

## Goal

Make provider-extension session/message actions usable from the frontend without creating a separate interaction model.

Desired behavior:

1. frontend discovers action-shaped elements from session UI schema
2. those actions appear alongside the existing application-plugin actions where appropriate
3. existing dialog/action execution helpers continue to be used
4. backend routing uses the existing `action_owner` mechanism to pick the right execution path

## Implementation intent

1. Merge session UI schema actions into the visible action lists.
- include `ui_type == "session_action"` and `ui_type == "message_action"` elements from session UI schema in the action menus shown in the chat screen
- do this additively so existing application-plugin actions continue to appear

2. Preserve opaque routing metadata.
- ensure `action_owner` survives from session UI schema element -> frontend action element -> action runner -> backend request
- ensure provider-extension session actions still carry `session_id` and dialog-mapped parameters correctly

3. Keep action sources conceptually separate even if the UI merges them.
- application-plugin actions may still come from `useApplicationPlugins()`
- provider-extension session/message actions should come from session UI schema
- if merging requires de-duplication, it should be deterministic and documented

4. Validate the `openai_responses` native compaction action as the concrete example.
- after wiring, it should become visible and executable from the frontend

## Questions to resolve during implementation

1. Should session UI schema actions appear only in the session chat screen, or anywhere the frontend currently shows plugin actions?
2. If an application action and a session UI schema action share the same `id`, what is the merge/de-duplication policy?
3. Does the frontend SDK already preserve opaque fields like `action_owner`, or does the SDK/action runner need a targeted update?
4. Is the scope mobile-only, or should any shared frontend SDK/react package changes also cover desktop consumers?

## Suggested execution plan

1. Inspect the frontend SDK/react helpers used by the mobile app.
- verify how `useApplicationPlugins()`, `useSessionUiSchemaController(...)`, and `runApplicationAction(...)` model and forward action elements

2. Wire session UI schema actions into the visible action sources.
- session actions: merge session UI schema `session_action` elements with existing `pluginSessionActions`
- message actions: merge session UI schema `message_action` elements with existing `pluginMessageActions`

3. Add tests at the highest practical layer.
- frontend/unit/integration coverage showing that session UI schema actions become visible/selectable
- action-runner coverage showing `action_owner: "provider_extension"` is forwarded to backend execution

4. Validate end-to-end with native compaction.
- ensure the action is visible for an `openai_responses` session
- ensure triggering it causes the expected backend action execution and session reload/update

## Acceptance criteria

1. Provider-extension `session_action` UI elements from session UI schema are visible in the frontend session action list.
2. Provider-extension `message_action` UI elements from session UI schema are visible where message actions are shown.
3. Executing one of those actions preserves `action_owner` and reaches the backend provider-extension session-action path.
4. Existing application-plugin actions continue to work.
5. The `openai_responses` native compaction action is usable from the frontend, not only from backend tests.

## References

1. Superseded draft task:
- `tasks/20260310-openai-responses-provider/110-wire-provider-extension-session-actions-into-frontend.md`

2. Frontend code paths:
- `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx:260`
- `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx:440`
- `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx:642`
- `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx:1478`

3. Backend routing already in place:
- `application/python/agent_terminal_app/server.py:2678`
- `core/python/agent_app/application_future.py:1048`

4. Existing backend tests:
- `application/python/tests/test_provider_extension_session_actions_endpoints.py`

5. Concrete example action to validate:
- `plugins/openai_responses/src/openai_responses_plugins/openai_responses_native_compaction_extension.py`