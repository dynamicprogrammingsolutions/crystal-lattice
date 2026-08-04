# Stage 1 Notification Design

Design the non-blocking generic session notification model. This stage supports useful, persistent, actionable notifications without pausing a running request.

## Requirements checklist

- [x] Define the notification data model stored in `Session.metadata`.
- [x] Define notification lifecycle events.
- [x] Define de-duplication and update semantics.
- [x] Define how `ActionDisplayPayload` is reused for notification rendering and actions.
- [x] Define model-visibility rules so notifications are hidden from provider/model history by default.
- [x] Document failure behavior: notification emission must not fail the user request.

Parent Task: `tasks/20260619-generic-session-notifications/000-main.md`

Completed Via:
`tasks/20260729-staged-application-config-and-full-reload.md`

## Data Model

Notifications are stored under `Session.metadata["notifications"]["items"]` as a list. Each notification is a plain dict:

```json
{
  "id": "notif_<uuid>",
  "key": "stable-dedupe-key",
  "kind": "notification",
  "status": "pending",
  "severity": "info",
  "title": "Figma MCP needs sign-in",
  "body": "This request is continuing without Figma tools.",
  "created_at": "2026-06-19T12:00:00Z",
  "updated_at": "2026-06-19T12:00:00Z",
  "request_id": "req_...",
  "source": {
    "plugin": "mcp_runtime_app",
    "subsystem": "mcp",
    "server_name": "figma"
  },
  "display": {
    "format": "markdown",
    "body": "This request is continuing without Figma tools.",
    "title": "Figma MCP needs sign-in",
    "variant": "warning",
    "presentation": "inline",
    "dismissible": true,
    "actions": [
      {
        "kind": "run_action",
        "id": "start-login",
        "label": "Sign in",
        "plugin": "mcp_runtime_app",
        "action_id": "mcp_start_login",
        "fixed_params": { "server_name": "figma" }
      }
    ]
  },
  "resolution": null,
  "model_visibility": "hidden"
}
```

### Field semantics

| Field | Type | Description |
|-------|------|-------------|
| `id` | string (uuid) | Assigned by the backend. Used for updates/resolution. |
| `key` | string | Plugin-provided stable dedupe key. If a pending notification with the same key exists, `create` updates it in place instead of appending. |
| `kind` | `"notification"` | Stage 1 only supports `notification`. Stage 2 adds `interaction`. |
| `status` | `"pending"` \| `"resolved"` | Stage 1 only. Stage 2 adds `pending_response`, `responded`, `cancelled`, `expired`. |
| `severity` | `"info"` \| `"success"` \| `"warning"` \| `"error"` | Machine-readable level for SDK filtering/sorting. Defaults to `info`. |
| `title`, `body` | string | Plain-text summary. Rich rendering lives in `display`. |
| `created_at`, `updated_at` | ISO 8601 string | Set by the backend. |
| `request_id` | string \| null | The request that emitted the notification, if applicable. |
| `source` | dict | Plugin-provided provenance. Free-form beyond `plugin` (required). |
| `display` | `ActionDisplayPayload` | Existing type from `packages/frontend-sdk/src/types/plugins.ts`. Renders via `ActionDisplayCard` / `ActionResultInlineCard`. |
| `resolution` | null \| dict | Set when the notification is resolved. Shape: `{ "action_id": "...", "values": {...}, "resolved_at": "ISO8601" }`. |
| `model_visibility` | `"hidden"` | Stage 1 only supports `hidden`. Reserved for future `summary` / `message`. |

### Severity vs. display.variant

`severity` is the stable machine-readable field used by SDK selectors and future filtering. `display.variant` is the presentation hint. When `display.variant` is omitted, the RN host defaults it to match `severity`. Plugins may override `display.variant` for a softer/stronger presentation without changing `severity`.

## Standard display presentations

Stage 1 shares `ActionDisplayPayload.presentation` with owner-memory
application notifications and direct action responses:

- `banner` — connection-aware top banner rail; on desktop every producer uses
  the same rail.
- `inline` — session notification region for the owning session.
- `modal` — mobile modal or desktop React window.

Explicit presentation wins. A session notification without presentation
defaults to `inline`. Presentation changes placement only; persistence,
lifecycle, model visibility, and follow-up action behavior remain unchanged.

This standardization is implemented through the active overlap recorded in
`tasks/20260729-staged-application-config-and-full-reload.md`.

## Lifecycle Events

SDK event types (added to `packages/frontend-sdk/src/types/events.ts`):

- `session_notification_created`
- `session_notification_updated`
- `session_notification_resolved`

Each event payload:

```json
{
  "type": "session_notification_created",
  "session_id": "...",
  "request_id": "..." | null,
  "notification": { "...": "..." }
}
```

Clients update UI from events immediately and reload persisted notifications from session metadata on reconnect. These events pass through the existing `compact_events` pass unchanged (only `partial`/`tool_partial`/`final`/`tool_results` are compacted).

## De-Duplication

Notifications support a stable `key`. Creating a notification with an existing pending `key` updates the existing item in place (merging `display`, `severity`, `body`, `updated_at`) rather than appending a duplicate. The returned `id` is the existing notification's `id`.

Suggested MCP keys (MCP follow-up, not Stage 1 tests):

```text
mcp:<server-name>:auth_required
mcp:<server-name>:failed
```

Stage 1 tests use generic keys such as `dummy:tool:warning`.

## Display Reuse

The `display` field is an existing `ActionDisplayPayload`. Buttons and follow-up actions use existing action display shapes:

- `run_action` — execute an application action (e.g., start login, resolve notification)
- `open_url` — open an external URL
- `copy_text` — copy text to clipboard
- `download_attachment_asset` — download a session asset
- `dismiss` — frontend-only hide (no backend roundtrip)

No new prompt/button schema is invented for Stage 1.

## Visibility

Notifications are not model-visible by default. `model_visibility: "hidden"` means the notification never enters `Session.messages` or native provider history. Reserved future values: `summary` (a summary message is appended), `message` (the full notification body is appended). Stage 1 implements `hidden` only.

## Failure Behavior

Notification emission must not fail the user request. Two layers:

1. **`notification_sink` (tool context)**: wraps `AgentApplication` methods in `try/except`, logs failures via `agent_core.utils.get_logger`. Tools call `context["notification_sink"].create({...})` and never see exceptions.
2. **`AgentApplication.create_session_notification(...)`**: raises on programmer errors (invalid notification dict, missing session). Application plugins call this directly and are responsible for their own error handling.

## CL-150 Notes

The CL-150 branch includes prompt lifecycle ideas, but its implementation is tightly coupled to tool-call interception and assistant message metadata. For Stage 1, reuse only the concepts of pending/resolved lifecycle and frontend selectors, not the implementation shape.

## Completion Notes

- Completed via
  `tasks/20260729-staged-application-config-and-full-reload.md`.
- The final design includes success severity and producer-independent banner,
  inline, and modal presentations.
- Stage 2 interaction design remains untouched.