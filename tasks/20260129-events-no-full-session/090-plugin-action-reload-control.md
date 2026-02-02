# Plugins: action results distinguish mutations vs UI effects

Parent Task: `tasks/20260129-events-no-full-session/000-main.md`

Depends On:

- `tasks/20260129-events-no-full-session/070-mobile-remove-reloads.md`

## Goal

Make the `/actions` contract semantically correct by separating:

- **What changed** (session mutations)
- **What the UI should do** (explicit UI effects like navigation or reload)

Primary motivating case: message-delete actions update session history via events and should not force a full session reload.

## Status

- [x] Complete

## What was happening (root cause)

### Symptom

- Using the delete action provided by the application plugin triggers an immediate `loadMessages()` in mobile.

### Why it happens

- Mobile requested reload-on-update for all actions.
- The SDK treated `updated_session_ids` as “reload this session”.
- Plugins correctly reported “session updated” even when events were sufficient, which unintentionally triggered reloads.

## Requirements

- Reporting `updated_session_ids` must remain **semantically correct** (it means “state changed”, not “reload now”).
- Reload must be **explicit**, used only when events are insufficient.
- Navigation must be **explicit**, and clients can also choose their own policy (e.g. “navigate on created session”).

## Implemented solution (breaking change)

Action results now use:

```json
{
  "mutations": {
    "created_session_ids": ["..."],
    "updated_session_ids": ["..."],
    "deleted_session_ids": ["..."]
  },
  "ui_effects": {
    "navigate_to_session_id": "..." | null,
    "reload_session_ids": ["..."],
    "reload_sessions_list": true
  }
}
```

Semantics:

- `mutations.*` is the truth: what sessions were created/updated/deleted.
- `ui_effects.*` is explicit UI guidance:
  - Reload happens only when `reload_session_ids` includes the current session.
  - Navigation happens only when `navigate_to_session_id` is a non-empty string.
  - `navigate_to_session_id: null` explicitly suppresses auto-navigation policies.

SDK policy knobs:

- `reloadSessionsListOnMutations` still exists as a client policy for snapshot-based session lists.
- `navigateOnCreatedSession` still exists as a client policy, but is suppressed when the plugin explicitly provides `navigate_to_session_id: null`.

## Acceptance tests

- Trigger delete via `session_actions_app` message action.
  - Expect: no `loadMessages()` call, messages update via `messages_deleted` events.
- Trigger actions that create sessions (copy/fork).
  - Expect: still navigate/reload as before.

## Implementation notes

- SDK updates:
  - `packages/frontend-sdk/src/types/plugins.ts`
  - `packages/frontend-sdk/src/plugins/actionRunner.ts`
  - `packages/frontend-sdk/src/plugins/__tests__/actionRunner.test.ts`

- Mobile update:
  - `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx`

- Plugin updates (both in-tree copies):
  - `plugins/session-actions-app/src/session_actions_app/__init__.py`
  - `plugins/rebuild-native-app/src/rebuild_native_app/__init__.py`
  - `plugins/session-title-app/src/session_title_app/__init__.py`
  - `plugins/generate-title-app/src/generate_title_app/__init__.py`
  - `plugins/summarize-range-app/src/summarize_range_app/__init__.py`
  - `plugins/session-pinned-app/src/session_pinned_app/__init__.py`
  - `core/python/plugins/session_actions_app.py`
  - `core/python/plugins/rebuild_native_app.py`
  - `core/python/plugins/session_title_app.py`
  - `core/python/plugins/generate_title_app.py`
  - `core/python/plugins/summarize_range_app.py`
  - `core/python/plugins/session_pinned_app.py`

- Python tests updated to assert `mutations.*` / `ui_effects.*`:
  - `core/python/tests/test_*_app_plugin_unit.py`
  - `core/python/tests/test_rebuild_native_app.py`
  - `application/python/tests/test_server_actions_*.py`
