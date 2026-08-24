# Bridge APNs/FCM Push Delivery

Let a community self-deployed bridge deliver eligible Crystal notification
transitions through APNs/FCM to account-owned mobile devices.

## Requirements checklist

### Functional requirements

- [ ] Mobile obtains, registers, and refreshes APNs/FCM-compatible provider
  tokens under its stable notification-device identity.
- [ ] The community bridge or its adjacent notification service stores and
  resolves account-scoped device destinations.
- [ ] A connected account-owned Crystal server can submit eligible
  OS-delivery candidates without sending raw account credentials.
- [ ] The sender routes candidates only to devices belonging to the owning
  account and allowed by user preferences.
- [ ] Provider delivery supports bounded retry, invalid-token handling, and
  delivery deduplication.
- [ ] Push taps open the relevant saved connection/session and hydrate
  authoritative notification state.
- [ ] Operators and users can configure which attention categories are
  remotely push-worthy.
- [ ] A bridge can disable push while retaining ordinary authenticated,
  pairing, or static-token operation.
- [ ] Multiple devices receive account-scoped delivery according to explicit
  policy.

### Non-functional requirements

- [ ] No private hosted account, notification, or push service is required.
- [ ] Bridge operators supply and secure their own APNs/FCM credentials.
- [ ] Push payloads default to generic non-sensitive content and opaque routing
  identifiers; full content is fetched after app open.
- [ ] Provider failure never changes authoritative notification lifecycle.
- [ ] Cross-account delivery is prohibited and integration-tested.
- [ ] Bridge clustering, restart, retry, and token refresh do not duplicate
  pushes.
- [ ] Push-disabled deployments start and proxy normally without provider
  credentials.
- [ ] Real-device iOS and Android tests cover background/terminated delivery,
  tap routing, token rotation, and revocation.

Parent Task:
`tasks/20260824-os-level-notification-delivery/000-main.md`

Depends On:

- `tasks/20260824-os-level-notification-delivery/030-account-and-device-notification-routing.md`
- `tasks/20260821-modular-bridge-access-platform/170-mixed-transport-access-e2ee-and-metering-alignment.md`

## Open requirement questions

1. Should the first sender use FCM HTTP v1 for both Android and iOS?
   - Recommendation: yes, with Firebase configured to forward iOS to APNs;
     retain a provider-neutral sender interface for future direct APNs.
2. Should push delivery include notification title/body or only a generic
   notice?
   - Recommendation: generic safe title/body by default, with stricter
     operator/user opt-in before richer content is considered.

## Execution plan

Status: Draft

Add native mobile permission/token adapters and authenticated registration
through subtask 030. Implement a provider-neutral bridge sender interface with
an FCM HTTP v1 implementation, bounded retries, invalid-token classification,
idempotency, and delivery-attempt recording.

Submit delivery candidates from the connected server/bridge control path using
stable candidate identity and server ownership rather than raw notification
stores or credentials. Keep payload content minimal. On tap, use opaque
destination metadata to open the saved connection and fetch current
authoritative notification state.

Add deterministic provider fixtures and local bridge integration before
operator-supplied Firebase/APNs real-device validation.

### Implementation decisions and open questions

- Decision: provider send outcome does not mutate notification lifecycle.
- Decision: push sender credentials remain bridge-side.
- Decision: tap always rehydrates current server state.
- Open: approve FCM-first and generic-payload recommendations.

### Documentation

- Document Firebase/APNs operator setup, mobile app registration, credentials,
  permissions, payload privacy, retries, invalid tokens, and troubleshooting.
- Document push-disabled and local-only alternatives.
- Keep provider secrets out of examples and generated diagnostics.

### Task checklist

- [ ] Approve first sender and payload policy.
- [ ] Add mobile permission and provider-token adapters.
- [ ] Add authenticated token registration/rotation.
- [ ] Add provider-neutral sender and FCM implementation.
- [ ] Add candidate submission, route lookup, attempts, retry, and invalidation.
- [ ] Add tap routing and authoritative refresh.
- [ ] Add unit, bridge, SDK, mobile, cluster, and failure tests.
- [ ] Complete real-device background/terminated delivery on iOS and Android.
- [ ] Verify push-disabled community deployment.
- [ ] Publish operator and user documentation.

### Requirement verification

- A candidate from an account-owned server reaches only the account's eligible
  registered devices.
- Backgrounded and terminated real devices receive and open the notification.
- Duplicate candidate submission/provider retry produces at most one intended
  user-visible delivery per device.
- Invalid/revoked tokens stop future sends.
- Missing provider configuration leaves bridge connectivity functional.

### Additional implementation verification

- Cluster node changes do not duplicate attempts.
- Provider rate limiting/backoff cannot block bridge proxy traffic.
- Logs, metrics, and traces contain no provider credentials or sensitive
  notification body.