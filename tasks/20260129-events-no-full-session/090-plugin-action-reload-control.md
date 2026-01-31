# Plugins: allow actions to avoid triggering a session reload

Parent Task: `tasks/20260129-events-no-full-session/000-main.md`

Depends On:

- `tasks/20260129-events-no-full-session/070-mobile-remove-reloads.md`

## Goal

Allow application plugins (invoked via `POST /actions`) to signal whether a session reload should happen.

Primary motivating case: `session_actions_app` delete-message actions currently cause mobile to reload even though events are sufficient.

## Status

- [ ] Not started

## What’s happening today (root cause)

### Symptom

- Using the delete action provided by the application plugin triggers an immediate `loadMessages()` in mobile.

### Why it happens

- The mobile app runs actions with `reloadSessionOnUpdated: true`:
  - `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx:392`.

- The frontend SDK converts a plugin response containing `updated_session_ids` into a `reloadSession` effect:
  - `packages/frontend-sdk/src/plugins/actionRunner.ts:137` checks `updated_session_ids.includes(currentSessionId)` and pushes a `reloadSession` effect.

- The session-actions plugin returns `updated_session_ids: [session_id]` for message deletions:
  - `plugins/session-actions-app/src/session_actions_app/__init__.py:459` returns `updated_session_ids` containing the session id.

## Requirements

- Some actions should keep the current default (reload on updated).
- Some actions (notably delete/modify messages) should be able to avoid reload, relying on events instead.
- Solution should generalize beyond one specific plugin.

## Proposed solution options (decision needed)

### Option A (recommended): UI-schema hint on ActionUiElement

Add a convention on `ActionUiElement` (UI schema element) allowing an action to specify effect preferences.

- Example UI element payload:

  ```json
  {
    "ui_type": "message_action",
    "id": "delete_single_message",
    "action_id": "delete_messages",
    "effects": { "reload_session_on_updated": false }
  }
  ```

- Mobile uses that hint when calling `runApplicationAction`:
  - `reloadSessionOnUpdated = element.effects?.reload_session_on_updated ?? true`

- Update `session_actions_app` UI elements (delete) to set that flag.

Pros:
- Per-action granularity.
- Doesn’t require changing the generic `/actions` response schema.

Cons:
- Only works for clients that respect the hint.

### Option B: response-level hint from executeAction

Add a convention in `ExecuteActionResponseOk.result`, e.g.:

- `result.effects = { reload_session: false }`

Then modify `packages/frontend-sdk/src/plugins/actionRunner.ts` so `deriveActionEffectsFromResult()` honors the server’s response and suppresses emitting a `reloadSession` effect.

Pros:
- Centralized behavior: all clients using the SDK runner benefit.

Cons:
- Requires updating plugin code to emit the new field.
- Potentially harder to version / coordinate.

### Option C: mobile-only allowlist/denylist

Hardcode conditions in mobile, e.g. “don’t reload for plugin X + action Y”.

Pros:
- Quick.

Cons:
- Brittle, not extensible.

## Suggested acceptance tests

- Trigger delete via `session_actions_app` message action.
  - Expect: no `loadMessages()` call, messages update via `messages_deleted` events.
- Trigger actions that create sessions (copy/fork).
  - Expect: still navigate/reload as before.
