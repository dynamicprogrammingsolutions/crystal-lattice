# Stage 2: Bridge Server State And Sync
Extend the bridge and Python bridge client so bridge connections can store desired server settings while the server is offline, and so the server can later reconcile those settings and publish the last known applied state.

## Requirements checklist

- [ ] Add a generic per-server state document to the bridge, keyed by `server_id`.
- [ ] Store both `desired_settings` and `last_known_settings` in the bridge document.
- [ ] Allow bridge app clients to read and update the per-server state document using `pairing_token` + `server_id`, even when no live server session exists.
- [ ] Allow the Python bridge client to fetch bridge state, reconcile `desired_settings` into local server settings, and push `last_known_settings` back after apply.
- [ ] Keep reconciliation and polling in the server/transport layer, not inside the sleep-prevention plugin.
- [ ] Add the macOS scheduled wake + poll hook for bridge sync entrypoints.
- [ ] Add tests for bridge state storage, authorization, and Python-side reconciliation.
- [ ] Preserve the current bridge HTTP tunnel behavior for normal paired live requests.

Parent Task: `tasks/20260421-server-settings-bridge-sync/000-main.md`
Depends On: `tasks/20260421-server-settings-bridge-sync/010-live-server-settings-and-lifecycle.md`

## Scope

- This stage is about transport/state sync, not offline UI polish.
- The bridge must remain generic; it should not know what individual settings keys mean.
- Manual/discovery connections remain live-only and are unaffected here.

## Existing Relevant Code

- Bridge app-side channel currently supports:
  - server listing
  - pairing
  - resume
  - HTTP requests
  - see `bridge-elixir/lib/bridge/app_channel.ex:57-260`
- Bridge server-side channel currently supports:
  - registration
  - proxied HTTP responses
  - server push events for pairing and HTTP requests
  - see `bridge-elixir/lib/bridge/server_channel.ex:5-175`
- Frontend bridge transport currently assumes a live paired session for normal requests:
  - `packages/frontend-sdk/src/transport/bridgeTransport.ts:93-260`
- The bridge already has `pairing_token` and `server_id` concepts available during `pair_submit` and `resume_session`:
  - `bridge-elixir/lib/bridge/app_channel.ex:95-216`

## Implementation Notes

- The bridge state document should be opaque from the bridge's perspective. Suggested shape:
  - `desired_settings`
  - `last_known_settings`
  - optionally timestamps, if helpful for freshness/debugging
- App-side bridge state operations should work without requiring a live `session_id`.
- The Python bridge client should reconcile using Stage 1 `AgentApplication` server settings helpers so that:
  - lifecycle triggers still run
  - plugins remain unaware of bridge internals
- Reconciliation source should be explicit in lifecycle context, for example `source: "bridge_sync"`.
- The macOS scheduled wake helper should call into a bridge-sync entrypoint; it should not manipulate sleep-prevention state directly.

## Suggested Tests

- `bridge-elixir/test`
  - per-server state CRUD
  - pairing-token-based authorization
  - offline app access without live server session
- `application/python/tests`
  - bridge client reconciliation of `desired_settings`
  - bridge client publication of `last_known_settings`
- `packages/frontend-sdk/src/transport`
  - bridge-native state read/write behavior separate from tunneled HTTP
- integration
  - offline desired-state update on bridge
  - later server wake/reconnect
  - desired state applied locally
  - last known state updated on bridge

## Acceptance Notes

- At the end of this stage, pending sync should be representable as:
  - `desired_settings != last_known_settings`
- UI work can remain minimal as long as the transport/data path is testable.