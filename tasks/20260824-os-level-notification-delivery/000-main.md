# OS-Level Notification Delivery

Deliver operating-system notifications through independently deployable local
network, community identity, account/device routing, and bridge push stages
without changing authoritative Crystal notification ownership.

## Requirements checklist

### Functional requirements

- [ ] Important authoritative Crystal notification transitions can produce a
  provider-neutral OS-delivery candidate.
- [ ] A mobile device can present OS notifications from a directly reachable
  local-network server without bridge connectivity or account login.
- [ ] Community bridge operators can optionally deploy Authentik and enable
  normalized account and server identity.
- [ ] Authenticated accounts can own servers and register notification devices
  for routed delivery.
- [ ] A community bridge can deliver eligible notifications through APNs/FCM
  to account-owned devices.
- [ ] Opening an OS notification can focus the relevant saved connection and
  session, then hydrate authoritative notification state.
- [ ] Local anonymous, pairing-scoped, and account-routed delivery modes remain
  distinguishable and independently configurable.
- [ ] Each delivery stage remains independently useful and optional.

### Non-functional requirements

- [ ] The authoritative notification owns content, revisions, dismissal,
  resolution, retention, and history; OS delivery owns only targeting,
  attempts, deduplication, and tap routing.
- [ ] No commercial account, entitlement, payment, or private hosted-service
  implementation is required.
- [ ] Public task files, code, configuration, and documentation contain no
  dependency on private repositories.
- [ ] Local and pairing-based operation remains available without Authentik or
  push-provider credentials.
- [ ] Notification and identity secrets are excluded from ordinary logs,
  diagnostics, and OS payloads.
- [ ] Platform scheduling and delivery guarantees are documented honestly and
  verified on real devices.
- [ ] Self-hosters can enable only the infrastructure tiers they want.

## Open requirement questions

1. What content should an OS-delivery candidate carry?
   - Recommendation: stable transition identity, safe generic title/body,
     owning server/session destination, expiry, and category; fetch full
     authoritative content after opening the app.
2. Should pairing-scoped remote push ship alongside account-routed push?
   - Recommendation: keep the contract compatible but make account-routed
     delivery the initial remote implementation unless pairing-only demand
     justifies another privacy/routing policy.
3. Which first provider path should send both platforms?
   - Recommendation: start with FCM HTTP v1 as the bridge sender, with Firebase
     forwarding iOS delivery to APNs, while keeping the delivery interface
     provider-neutral.

## Subtasks

- [ ] `tasks/20260824-os-level-notification-delivery/010-local-network-os-notifications.md`
- [ ] `tasks/20260824-os-level-notification-delivery/020-community-authentik-bridge-identity.md`
- [ ] `tasks/20260824-os-level-notification-delivery/030-account-and-device-notification-routing.md`
- [ ] `tasks/20260824-os-level-notification-delivery/040-bridge-apns-fcm-push-delivery.md`

## Relationship to earlier work

This task supersedes the useful delivery goals in:

`tasks/20260516-auth-notifications-staged-rollout/000-main.md`

Mapping:

- old local notification polling → subtask 010;
- old Authentik integration → subtask 020 plus public modular bridge
  dependencies;
- old bridge push delivery → subtasks 030 and 040.

The old direct Authentik-JWT dependency for downstream services is replaced by
normalized public identity/access grants. Cloud-specific access enforcement is
outside this notification task and remains owned by future cloud work.

## Supporting facts

- Crystal application/session notifications already provide authoritative
  persistence, revisions, lifecycle, events, retention, and follow-up actions.
- The global-attention task will define stable attention transition identity,
  expiry, explicit View destinations, and local acknowledgement.
- Local OS notifications can be posted by the mobile app after a successful
  refresh but cannot guarantee arbitrary background or terminated-app network
  execution.
- APNs/FCM remote delivery can wake or notify a backgrounded/terminated app but
  requires device tokens and an external sender.
- The public modular bridge task tree defines replaceable identity providers,
  OIDC clients, normalized accounts, server ownership, grants, and bridge
  enforcement.

## Execution plan

Status: Draft

Execute the four subtasks as independent capability layers.

Subtask 010 defines the shared OS-delivery candidate and implements direct
local-network refresh plus device-local presentation. It cannot depend on
accounts, bridge connectivity, or push providers.

Subtask 020 supplies an optional community Authentik deployment and a minimal
community identity/account/access-provider implementation against the public
modular bridge contracts. It must remain useful for self-deployed bridges
without commercial services.

Subtask 030 binds account identity, server ownership, device identity, and
rotating provider tokens into provider-neutral notification routes.

Subtask 040 adds the bridge sender and native APNs/FCM integration. It reuses
the delivery candidate and route contracts and keeps provider delivery
separate from authoritative notification lifecycle.

Stop for user review if any stage requires making Authentik, a bridge, or a
push provider mandatory for direct/local Crystal use, or if safe delivery
would require sending model/session content through the bridge/provider by
default.

### Implementation decisions and open questions

- Decision: attention eligibility is the source transition; it is not an OS
  delivery receipt.
- Decision: OS close/tap does not dismiss the authoritative notification.
- Decision: community Authentik is a real public implementation behind
  replaceable contracts.
- Decision: local delivery remains account-free.
- Open: approve candidate payload, pairing-scoped push, and first provider
  recommendations before implementation.

### Documentation

- Add a cross-package OS-delivery specification only when subtask 010 begins
  and the shared candidate/receipt contract is approved.
- Keep mobile background/native guidance with the mobile package.
- Keep community Authentik and bridge push deployment guidance with the public
  owning packages.
- Preserve the old task concept documents as historical research until their
  current replacements are published.

### Task checklist

- [ ] Approve shared delivery-candidate and routing decisions.
- [ ] Execute and verify local-network OS notification subtask 010.
- [ ] Execute and verify community Authentik subtask 020.
- [ ] Execute and verify account/device routing subtask 030.
- [ ] Execute and verify bridge APNs/FCM subtask 040.
- [ ] Complete real-device iOS and Android checkpoints for applicable stages.
- [ ] Verify local, pairing/static, authenticated, and push-disabled
  compatibility.
- [ ] Reconcile old task relations and current documentation.

### Requirement verification

- Local mode produces OS notifications from a directly reachable server with
  no bridge or login.
- Community Authentik supports mobile/terminal login, stable account identity,
  and claimed server ownership using only public components.
- Account/device routing selects only devices belonging to the server owner.
- Bridge push reaches backgrounded and terminated real devices and opens the
  correct connection/session.
- Dismissal and resolution remain authoritative server operations rather than
  OS-delivery side effects.

### Additional implementation verification

- Duplicate polling/events/provider retries do not duplicate OS delivery.
- Account switch, logout, server transfer, token rotation, and revocation
  remove obsolete routes.
- Missing Authentik or push configuration cannot break direct/local or
  pairing/static bridge operation.