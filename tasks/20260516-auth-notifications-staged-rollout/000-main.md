# Auth And Notifications Staged Rollout

Create a staged implementation plan for local polling notifications, remote push notifications, and later authentik-based login without losing the current pairing-based bridge flow.

## Task checklist

- [ ] `tasks/20260516-auth-notifications-staged-rollout/010-local-notification-polling.md`
- [ ] `tasks/20260516-auth-notifications-staged-rollout/020-bridge-push-delivery.md`
- [ ] `tasks/20260516-auth-notifications-staged-rollout/030-authentik-auth-integration.md`

## Purpose

This task directory captures the current product and architecture decisions made during research:

- Easy self-hosting remains a first-class requirement.
  - Users must still be able to deploy and use the bridge with no authentication service and no push-notification service.
  - The default or minimal deployment path should continue to work much like today.
- Stage 1 should add notification records plus a polling endpoint on the laptop/server, similar to `/events`, so the mobile app can fetch notifications over direct IP or over the bridge.
- Stage 1 supports two polling cadences:
  - foreground app polling or bridge-client polling at roughly 5-15 seconds
  - periodic background wake-up polling at roughly 5 minutes, where platform schedulers allow it
- Stage 2 should add remote push delivery through the bridge while keeping notification production on the laptop/server.
- Push-token persistence should live in the bridge so refreshed tokens are not lost when the desktop app is offline.
- Pairing remains a valid authorization model for notifications even before user-login auth exists.
- Stage 3 should add authentik-based login as an additional, stronger verification and authorization layer without forcing notification delivery to be redesigned.

## Current architecture notes

- The Python bridge client is started as a background task from the FastAPI app, not as a completely separate daemon:
  - `application/python/agent_terminal_app/server.py:473-482`
- The bridge client maintains the WebSocket connection to the bridge and already proxies local HTTP requests via `httpx`:
  - `application/python/agent_terminal_app/bridge_client.py:146-214`
  - `application/python/agent_terminal_app/bridge_client.py:618-656`
- The bridge client currently consumes bridge-originated messages and does not yet send notification-specific events:
  - `application/python/agent_terminal_app/bridge_client.py:292-319`
- The server already exposes an `/events` polling endpoint that can serve as the design template for a notification endpoint:
  - `application/python/agent_terminal_app/server.py:2951-3032`
- The mobile app already has foreground event polling and bridge transport timeout rules, but no push-notification SDKs:
  - `mobile/crystal-lattice-control-rn/App.tsx:91-130`
  - `mobile/crystal-lattice-control-rn/package.json:16-40`
- The bridge currently uses pairing/session mechanics and unauthenticated server registration:
  - `bridge-elixir/lib/bridge/app_channel.ex:64-180`
  - `bridge-elixir/lib/bridge/server_channel.ex:11-42`
- The cloud orchestrator currently uses a control token and scoped bearer-token checks, not a user identity layer:
  - `cloud-orchestrator/lib/cloud_orchestrator/router.ex:18-209`

## Deliverables in this task directory

- Stage task files for the three rollout phases.
- Human-targeted concept docs under `tasks/20260516-auth-notifications-staged-rollout/docs/`:
  - `push-notifications-fcm-apns.md`
  - `local-notifications-background-refresh.md`
  - `authentik-auth-concepts.md`

## Suggested reading order

1. `tasks/20260516-auth-notifications-staged-rollout/docs/local-notifications-background-refresh.md`
2. `tasks/20260516-auth-notifications-staged-rollout/010-local-notification-polling.md`
3. `tasks/20260516-auth-notifications-staged-rollout/docs/push-notifications-fcm-apns.md`
4. `tasks/20260516-auth-notifications-staged-rollout/020-bridge-push-delivery.md`
5. `tasks/20260516-auth-notifications-staged-rollout/docs/authentik-auth-concepts.md`
6. `tasks/20260516-auth-notifications-staged-rollout/030-authentik-auth-integration.md`

## High-level rollout summary

1. Build a local notification model first.
   - Introduce a notification record schema and a server endpoint dedicated to polling notifications.
   - Use it for direct-IP mode, bridge mode, and background scheduler wake-ups.
   - This stage is the minimum-infrastructure enhancement path and should work without push services or an auth service.
2. Add bridge-mediated remote push delivery second.
   - Keep notification creation on the laptop/server.
   - Persist push tokens in the bridge.
   - Let the bridge client poll locally and forward push-send requests to the bridge.
   - Push support must be optional and disabled by default when provider credentials are absent.
3. Add authentik-based login third.
   - Preserve the notification model and delivery pipeline.
   - Introduce identity-aware verification, device binding, and future sharing/organization features.
   - Auth support must be optional and should not block pairing-only or local-only deployments.

## Compatibility requirement

All new features in this rollout should be designed as optional capabilities:

- no-auth deployments remain supported
- no-push deployments remain supported
- direct-IP mode remains supported
- self-hosters can adopt only the infrastructure pieces they want
- missing provider credentials or auth configuration should degrade behavior gracefully rather than breaking startup
