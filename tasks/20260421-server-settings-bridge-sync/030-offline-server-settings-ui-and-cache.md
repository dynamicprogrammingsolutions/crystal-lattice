# Stage 3: Offline Server Settings UI And Cache
Add persisted connection-scoped cache and offline bridge settings UI so cached server settings can be viewed and edited from the connection screen when the server is offline.

## Requirements checklist

- [ ] Persist connection-scoped server settings UI schema and state instead of relying only on in-memory application-plugin caches.
- [ ] Extend the server settings controller to hydrate from persisted cache and then refresh live or bridge state.
- [ ] Add an offline-capable server settings entrypoint to the connection screen for bridge connections with cached state.
- [ ] Show a `Pending sync` warning when bridge `desired_settings` and `last_known_settings` differ.
- [ ] Keep direct/manual/discovery connections live-only with the same Stage 1 behavior when connected.
- [ ] Add tests for cache hydration, connection-screen access, and pending-sync presentation.

Parent Task: `tasks/20260421-server-settings-bridge-sync/000-main.md`
Depends On:
- `tasks/20260421-server-settings-bridge-sync/010-live-server-settings-and-lifecycle.md`
- `tasks/20260421-server-settings-bridge-sync/020-bridge-server-state-and-sync.md`

## Scope

- This stage is about offline bridge UX and persistence.
- The same rendering path should work for:
  - live connected server settings
  - bridge offline cached settings
- Manual/discovery connections should not gain offline desired-state editing.

## Existing Relevant Code

- Application UI schema caching is currently in-memory only:
  - `packages/frontend-sdk/src/plugins/pluginsRegistry.ts:24-161`
- Session settings controller behavior to mirror:
  - cache-first load and refresh semantics in `packages/frontend-sdk/src/sessionSettings/sessionSettingsController.ts:134-380`
- Current live settings modal template:
  - `mobile/crystal-lattice-control-rn/src/components/SessionSettingsModal.tsx:29-220`
- Current sessions screen for live connected settings:
  - `mobile/crystal-lattice-control-rn/src/SessionsScreen.tsx:177-216`
- Current connection screen where the offline gear should land:
  - `mobile/crystal-lattice-control-rn/src/ConnectionScreen.tsx:6-137`

## Implementation Notes

- Persist per-connection server settings data including:
  - filtered server-scoped UI schema
  - bridge `desired_settings`
  - bridge `last_known_settings`
  - timestamps/loading metadata as needed
- Loading behavior should intentionally mimic current session settings UX:
  - show cached values immediately
  - then show `Refreshing settings…` while refetching
- Only bridge connections should expose offline editing from the connection screen.
- Pending-sync UI should be derived from bridge state divergence, not from local optimistic mutation alone.

## Suggested Tests

- frontend SDK tests
  - persisted cache hydration
  - refresh after cached load
  - bridge fallback behavior when server HTTP is unavailable
- mobile/UI tests
  - connection-screen gear visibility when cached server settings exist
  - pending-sync banner/warning rendering
  - offline bridge settings edit persists desired state
- focused integration
  - cache exists
  - server offline
  - user edits desired state from connection screen
  - later reconnect/sync clears pending-sync warning after apply

## Acceptance Notes

- A user should be able to open cached server settings from the connection screen without first reconnecting to the server.
- The latest known values shown offline are allowed to be stale; they should still come from the newest bridge or cached state available.