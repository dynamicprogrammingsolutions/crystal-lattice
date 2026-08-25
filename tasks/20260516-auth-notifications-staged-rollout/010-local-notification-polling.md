# Stage 1: Local Notification Polling

Add a notification record model and a polling endpoint on the laptop/server so the mobile app can fetch notification-only data directly or through the bridge before remote push is introduced.

SUPERSEDED BY:
`tasks/20260824-os-level-notification-delivery/010-local-network-os-notifications.md`

## Requirements checklist

- [ ] Define a notification record schema that can survive later push and login work.
- [ ] Add a dedicated notification polling endpoint on the FastAPI server, modeled after `/events`.
- [ ] Support direct-IP mobile polling, bridged mobile polling, and periodic background refresh polling.
- [ ] Decide how notification state is stored, filtered, acknowledged, expired, and deduplicated.
- [ ] Document platform limits for 5-minute periodic wake-ups versus 5-15 second active polling.
- [ ] Keep the design compatible with later bridge-side push-token persistence and authentik-based auth.
- [ ] Preserve a minimal-infrastructure path that does not require any push provider or auth service.

Parent Task: `tasks/20260516-auth-notifications-staged-rollout/000-main.md`

## Why this stage comes first

This stage creates the product-level notification model before APNs/FCM or authentik are added. That reduces coupling, gives direct-IP users a useful first implementation, and preserves an easy self-hosted deployment path with no extra external services.

## Current code references

- Existing polling endpoint shape:
  - `application/python/agent_terminal_app/server.py:2951-3032`
- Bridge client is already allowed to call the local FastAPI server over HTTP:
  - `application/python/agent_terminal_app/bridge_client.py:618-656`
- Bridge client already runs inside the same FastAPI process lifecycle:
  - `application/python/agent_terminal_app/server.py:473-482`
- Mobile app already performs foreground polling of event-like data:
  - `mobile/crystal-lattice-control-rn/App.tsx:91-130`

## Decisions captured from research

- The local polling endpoint should be notification-specific rather than overloading `/events`.
- Active polling can be fast:
  - foreground app: about 5-15 seconds
  - bridge-client local polling: about 5-15 seconds
- Periodic wake-up polling can be slow:
  - background scheduler: about 5 minutes is acceptable for the first version
- The endpoint should be compatible with later long-poll or NDJSON evolution.
- This stage should work without any outside push service and without user login.
- Pairing remains a valid authorization model for access in bridge mode.

## Recommended endpoint shape

Suggested initial route:

- `GET /notifications`

Suggested query parameters:

- `since_id`
- `session_id` or other recipient scope if needed
- `limit`
- `include_acknowledged=false`

Suggested response shape:

```json
{
  "notifications": [
    {
      "id": "notif_123",
      "created_at": "2026-05-16T12:34:56Z",
      "kind": "task_completed",
      "title": "Task completed",
      "body": "The agent finished the request.",
      "server_id": "server-123",
      "session_id": "session-456",
      "deep_link": "clc://server/server-123/session/session-456",
      "delivery_hints": {
        "foreground_poll": true,
        "background_poll": true,
        "push_candidate": true
      }
    }
  ],
  "latest_notification_id": "notif_123",
  "cursor_expired": false
}
```

Suggested companion actions:

- `POST /notifications/{notification_id}/ack`
- optional `POST /notifications/{notification_id}/dismiss`

## Storage and model work

Notification record fields to decide now:

- `id`
- `created_at`
- `kind`
- `title`
- `body`
- `server_id`
- `session_id`
- `deep_link`
- `recipient_scope`
- `delivery_hints`
- `expires_at`
- `acked_at`
- `push_sent_at`
- `source_request_id` or similar dedupe hook

Recipient-scope options to keep open for later:

- pair-based scope:
  - `server_id + paired_client_id`
- login-based scope:
  - `user_sub + device_id`
- hybrid scope:
  - store both if present

## Implementation outline

1. Add notification data structures and persistence on the Python server side.
2. Add a `GET /notifications` endpoint modeled after `/events`.
3. Add app-side polling support in the React Native client.
4. Add background polling hooks where platform schedulers allow it.
5. Add notification acknowledgement handling.
6. Add tests for polling, cursoring, dedupe, and expiration.

## Manual vs CLI / agent steps

### Infrastructure

- [Agent/CLI] No external cloud infrastructure is required for this stage.
- [Agent/CLI] Repo code changes, tests, and local dev setup can be done entirely in the workspace.
- [Manual] Background scheduler behavior must be validated on real iOS/Android devices, not just simulators.

### iOS local notification / background prerequisites

- [Manual] Enable the iOS capabilities needed for local notifications and, if used, Background Tasks / Background Fetch in Xcode.
- [Agent/CLI] The code and plist/entitlement file edits can be prepared by an agent once the team chooses the exact library approach.
- [Manual] Real-device verification is required because scheduler wake-up timing is OS-controlled.

### Android local notification / background prerequisites

- [Manual] Confirm Android notification permission behavior on Android 13+ devices.
- [Agent/CLI] Add libraries, manifest entries, notification channels, and WorkManager wiring.
- [Manual] Validate behavior on at least one physical Android device under normal battery restrictions.

## Risks and constraints

- iOS background refresh is not guaranteed and should not be treated as instant delivery.
- Android periodic work timing is intentionally inexact.
- Notification content should stay small and non-sensitive even in Stage 1 because the same records may later become push payload inputs.
- Avoid designing the endpoint around a single device; multiple recipient records may be needed later.
- This stage should not introduce any mandatory external dependency for bridge-only or direct-IP deployments.

## Recommended human docs for this stage

- `tasks/20260516-auth-notifications-staged-rollout/docs/local-notifications-background-refresh.md`
