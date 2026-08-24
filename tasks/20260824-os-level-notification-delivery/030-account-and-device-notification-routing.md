# Account And Device Notification Routing

Bind mobile notification devices to community accounts and route eligible
notification transitions from account-owned Crystal servers without requiring
a commercial control plane.

## Requirements checklist

### Functional requirements

- [ ] A mobile installation has a stable notification-device identity distinct
  from rotating APNs/FCM provider tokens.
- [ ] A community account can register, update, disable, and revoke multiple
  notification devices.
- [ ] A claimed Crystal server resolves to its owning community account.
- [ ] An OS-delivery candidate can resolve from server identity to the
  account's eligible active devices.
- [ ] Account switch, logout, account deletion, server unclaim/transfer, token
  rotation, and device revocation update routes explicitly.
- [ ] Multiple devices per account and multiple servers per account are
  supported.
- [ ] Pairing-scoped remote routing remains representable as a separate
  optional mode.
- [ ] Local-network delivery remains connection-scoped and does not require
  account routing.
- [ ] Users can control device-level and category-level remote delivery
  eligibility.

### Non-functional requirements

- [ ] Routing consumes public community account and server-ownership contracts.
- [ ] Email is never a routing or ownership key.
- [ ] Account credentials and refresh tokens are not copied into device route
  records.
- [ ] Raw provider tokens are protected at rest and excluded from logs and
  diagnostics.
- [ ] Registration, token rotation, candidate routing, and revocation are
  idempotent.
- [ ] Route removal and account/server revocation converge within a documented
  bound.
- [ ] The routing model remains provider-neutral across APNs, FCM, and future
  delivery providers.
- [ ] Cross-account routing is prevented by data constraints and integration
  tests.

Parent Task:
`tasks/20260824-os-level-notification-delivery/000-main.md`

Depends On:

- `tasks/20260824-os-level-notification-delivery/010-local-network-os-notifications.md`
- `tasks/20260824-os-level-notification-delivery/020-community-authentik-bridge-identity.md`

## Open requirement questions

1. Should a notification device belong to one active account at a time?
   - Recommendation: yes for initial delivery; account switch explicitly
     rebinds or registers a separate account-scoped route.
2. Where should provider tokens be stored?
   - Recommendation: in a bridge-adjacent durable notification route service,
     not on every Crystal server and not solely in mobile local storage.

## Execution plan

Status: Draft

Define provider-neutral notification-device and delivery-route records keyed by
stable device identity, account identity, server ownership, platform/provider,
and rotating provider token. Add authenticated registration and revocation
operations using the community account access contract.

Map each incoming delivery candidate to its owning server/account and selected
eligible devices. Keep local connection delivery outside this route service.
Add idempotency keys and terminal route outcomes needed by the bridge sender,
but do not implement APNs/FCM calls in this subtask.

### Implementation decisions and open questions

- Decision: stable device identity and rotating provider token are separate.
- Decision: routing records never contain user auth refresh tokens.
- Decision: server ownership is checked at candidate-routing time.
- Open: approve single-active-account device binding and service placement.

### Documentation

- Document device registration, token rotation, account/server association,
  preferences, revocation, retention, and privacy.
- Document pairing-scoped compatibility separately from account routing.

### Task checklist

- [ ] Approve route model, account binding, and storage boundary.
- [ ] Define device, token, route, preference, and delivery-attempt contracts.
- [ ] Add authenticated device registration/update/revoke operations.
- [ ] Integrate server ownership and account route resolution.
- [ ] Add account/device/category preference handling.
- [ ] Add idempotency, rotation, revocation, and retention.
- [ ] Add service, API, mobile integration, and cross-account tests.
- [ ] Complete account-switch/device-revocation manual checkpoint.
- [ ] Update public documentation.

### Requirement verification

- One account registers multiple devices and routes a candidate from its
  claimed server to those eligible devices.
- Another account cannot register or receive for that server.
- Token rotation updates the route without duplicating the device.
- Logout, account deletion, server transfer, and revocation stop subsequent
  routing within the documented bound.

### Additional implementation verification

- Duplicate registrations and delivery candidates are idempotent.
- Provider-token storage and diagnostics pass secret scanning/redaction tests.
- Route retention does not leave indefinitely active orphaned devices.