# Stage 1 Notification Design

Design the non-blocking generic session notification model. This stage should support useful, persistent, actionable notifications without pausing a running request.

## Requirements checklist

- [ ] Define the notification data model stored in `Session.metadata`.
- [ ] Define notification lifecycle events.
- [ ] Define de-duplication and update semantics.
- [ ] Define how `ActionDisplayPayload` is reused for notification rendering and actions.
- [ ] Define model-visibility rules so notifications are hidden from provider/model history by default.
- [ ] Document failure behavior: notification emission must not fail the user request.

Parent Task: `tasks/20260619-generic-session-notifications/000-main.md`

## Proposed Data Model

Store notifications under session metadata:

```json
{
  "notifications": {
    "items": [
      {
        "id": "notif_...",
        "key": "stable-dedupe-key",
        "kind": "notification",
        "status": "pending",
        "severity": "warning",
        "title": "Figma MCP needs sign-in",
        "body": "This request is continuing without Figma tools.",
        "created_at": "2026-06-19T...",
        "updated_at": "2026-06-19T...",
        "request_id": "req_...",
        "source": {
          "plugin": "mcp_runtime_app",
          "subsystem": "mcp",
          "server_name": "figma"
        },
        "display": {
          "format": "markdown",
          "title": "Figma MCP needs sign-in",
          "body": "This request is continuing without Figma tools.",
          "variant": "warning",
          "presentation": "inline",
          "actions": []
        },
        "resolution": null,
        "model_visibility": "hidden"
      }
    ]
  }
}
```

## Lifecycle Events

Add SDK event types for:

- `session_notification_created`
- `session_notification_updated`
- `session_notification_resolved`

Each event should include:

- `session_id`
- optional `request_id`
- `notification`

Clients should be able to update UI from events immediately, and reload persisted notifications from session metadata later.

## De-Duplication

Notifications should support a stable `key`. Creating a notification with an existing pending key should update the existing item rather than append a duplicate.

For MCP auth this can be:

```text
mcp:<server-name>:auth_required
```

## Display Reuse

The `display` field should be an existing `ActionDisplayPayload`. Buttons and follow-up actions should use existing action display shapes:

- `run_action`
- `open_url`
- `copy_text`
- `download_attachment_asset` when relevant

Do not invent a separate prompt/button schema for Stage 1.

## Visibility

Notifications should not become model-visible messages by default. If future features need model-visible notifications, add an explicit `model_visibility` option such as:

- `hidden`
- `summary`
- `message`

Stage 1 should implement `hidden` only unless a strong local reason appears.

## CL-150 Notes

The CL-150 branch includes prompt lifecycle ideas, but its implementation is tightly coupled to tool-call interception and assistant message metadata. For Stage 1, reuse only the concepts of pending/resolved lifecycle and frontend selectors, not the implementation shape.