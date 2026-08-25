# Local-Network OS Notifications

Let mobile devices discover important Crystal notification transitions over a
direct local-network connection and present device-local OS notifications
without bridge connectivity or account login.

## Requirements checklist

### Functional requirements

- [ ] Mobile can request OS notification permission and expose its current
  permission/configuration state.
- [ ] Saved direct/manual and local-discovery connections can participate in
  notification refresh without a bridge.
- [ ] The server exposes or derives provider-neutral OS-delivery candidates
  from eligible attention transitions.
- [ ] A newly observed eligible candidate can create a device-local OS
  notification.
- [ ] A local delivery ledger prevents duplicate presentation of the same
  connection and attention transition.
- [ ] Tapping the OS notification opens or focuses the relevant saved
  connection/session when locally available.
- [ ] Foreground local delivery coordinates with in-app global attention.
- [ ] Users can enable or disable local OS delivery globally and per
  connection.

### Non-functional requirements

- [ ] No Authentik, account service, bridge, APNs, FCM, or external
  infrastructure is required.
- [ ] Foreground delivery may be prompt, while background scheduling is
  explicitly best effort and terminated-app delivery is not guaranteed.
- [ ] Background work respects iOS and Android battery, network, and scheduler
  restrictions.
- [ ] Connection credentials and sensitive notification content are excluded
  from scheduler metadata and OS payloads by default.
- [ ] Failure to refresh one connection does not suppress another connection.
- [ ] Real-device iOS and Android verification supplements deterministic
  candidate, ledger, and routing tests.

Parent Task:
`tasks/20260824-os-level-notification-delivery/000-main.md`

Depends On:

- `tasks/20260824-operational-notifications-and-global-attention/020-global-attention-contract-and-delivery.md`

## Open requirement questions

1. Should background refresh poll every saved direct connection or only
   connections explicitly opted in?
   - Recommendation: explicit per-connection opt-in, with a global master
     switch.
2. Should foreground delivery post an OS notification while the app is active?
   - Recommendation: prefer in-app attention while active and reserve OS
     presentation for background/inactive state, subject to user preference.

## Execution plan

Status: Draft

Define a versioned OS-delivery candidate projected from authoritative attention
records. Include only safe presentation text, category, source connection
identity, optional session destination, transition token, occurrence/expiry,
and a stable candidate identity.

Add mobile background refresh ownership outside individual screens. It loads
opted-in saved direct connections, performs bounded candidate refresh, compares
against a durable local delivery ledger, and schedules local notifications for
new eligible candidates.

Route notification taps through the connection lifecycle controller so stale
background work cannot focus or mutate the wrong connection. Add platform
adapters and deterministic tests before real-device scheduler verification.

### Implementation decisions and open questions

- Decision: the local ledger records delivery/acknowledgement, not
  authoritative notification dismissal.
- Decision: candidate identity includes connection plus attention transition.
- Decision: full notification state is fetched after open.
- Open: approve opt-in and foreground presentation recommendations.

### Documentation

- Document permissions, per-connection settings, expected foreground,
  background, and terminated-app behavior.
- Document iOS BGTask/background refresh and Android scheduler limitations
  without promising exact cadence.
- Document privacy and payload boundaries.

### Task checklist

- [ ] Approve candidate payload and local-delivery preferences.
- [ ] Add server/SDK candidate query and types.
- [ ] Add durable local delivery ledger.
- [ ] Add mobile permission and settings model.
- [ ] Add bounded direct-connection background refresh.
- [ ] Add iOS and Android local notification adapters.
- [ ] Add tap routing through connection lifecycle.
- [ ] Add backend, SDK, component, and deterministic native tests.
- [ ] Complete physical-device background/manual verification.
- [ ] Update documentation and requirement evidence.

### Requirement verification

- An opted-in direct connection produces one local OS notification for one
  eligible transition.
- Repeated refresh does not duplicate it.
- Tap opens the owning connection/session only when authority is current.
- No login, bridge, or provider credential is present.
- Background scheduling behavior is recorded honestly on both platforms.

### Additional implementation verification

- Expired candidates are not newly presented after delayed refresh.
- Connection deletion/repair removes or remaps ledger and tap destinations
  safely.
- Offline refresh failure cannot mark a candidate delivered.