# Provider Login Notifications And Deep-Link UX

Provide a provider-neutral, persistent, actionable login experience for
Codex/ChatGPT and Claude using existing notifications, action displays, global
attention, and generic action deep links.

SPLIT INTO:

- `tasks/20261016-provider-login-experience/000-main.md`
- `tasks/20261016-provider-login-experience/010-codex-browser-login-and-method-selection.md`
- `tasks/20261016-provider-login-experience/020-provider-login-notifications-and-anthropic-adoption.md`
- `tasks/20261016-provider-login-experience/030-provider-auth-global-attention.md`

This draft is retained as historical input and must not be executed as one
combined task. The split removes global attention from the critical path for
functional Codex and Anthropic login.

## Requirements checklist

### Functional requirements

- [ ] Missing, expired, or revoked provider authentication can create an
  actionable notification in the correct session or connection scope.
- [ ] Provider-owned notification actions can start login, show status, cancel
  an attempt, and log out.
- [ ] Users can select among supported login methods through standard action
  dialog controls.
- [ ] Existing device-code login remains supported.
- [ ] Browser-capable flows use generic action deep links to target the correct
  connection, session, plugin, action, and login attempt.
- [ ] A callback received while its target connection is unavailable remains
  pending and can resume when that connection becomes available.
- [ ] Important authentication transitions can request configurable global
  attention.
- [ ] View and Sign in are explicit user actions; notification arrival never
  navigates automatically.
- [ ] Existing Codex credential persistence remains compatible.

### Non-functional requirements

- [ ] Shared frontend routing contains no provider-specific OAuth logic.
- [ ] OAuth state, PKCE, credential, token, and callback secrets remain owned
  by the backend/plugin and are excluded from notification content.
- [ ] Stale callbacks and superseded attempts cannot mutate current
  credentials.
- [ ] Provider redirect restrictions are verified rather than assumed.
- [ ] Failure of enhanced notification/deep-link UX does not remove the basic
  provider login path.
- [ ] Mobile, desktop, and terminal use the same plugin action contracts.

Depends On:

- `tasks/20260824-direct-claude-provider-and-plugin-login/000-main.md`
- `tasks/20260824-operational-notifications-and-global-attention/020-global-attention-contract-and-delivery.md`
- `tasks/20260824-operational-notifications-and-global-attention/040-global-attention-frontend-integration.md`

## Supporting facts

- ChatGPT device-code login already works through application actions and
  action displays.
- Generic action deep links and disconnected pending callback handling already
  exist.
- Current provider login actions are discoverable through menus but do not use
  persistent auth-required notifications.
- The global-attention task owns cross-session/connection temporary banners;
  this task only marks provider transitions eligible.

## Execution plan

Status: Draft

Define a small provider-auth notification convention on top of the existing
notification and attention contracts. Authentication plugins create/update one
stable notification per credential target and lifecycle occurrence, while
their existing actions remain the executable behavior.

Generalize login-method selection and callback continuation through current
action dialog and deep-link runners. Implement Codex first as an existing
consumer, then adopt the same contract in the direct-Claude auth plugin.

### Implementation decisions and open questions

- Decision: authentication notifications are ordinary authoritative
  notifications, not a new auth-state store.
- Decision: notification dismissal does not cancel login or delete
  credentials.
- Decision: callbacks execute only after explicit target resolution and state
  validation.
- Open: provider-specific redirect availability may limit which browser flows
  are offered.

### Documentation

- Update notification/plugin guidance with authentication-required examples
  and sensitive-data rules.
- Document generic deep-link callback ownership and pending behavior.
- Update provider auth docs with delivered login-method and attention options.

### Task checklist

- [ ] Define provider-auth notification keys and lifecycle mapping.
- [ ] Add Codex auth-required notification publication and resolution.
- [ ] Add login-method selection through standard dialogs.
- [ ] Add/verify browser callback continuation where supported.
- [ ] Adopt the contract in the Claude auth plugin.
- [ ] Add backend, SDK, mobile, desktop, and deep-link integration tests.
- [ ] Add global-attention preference tests.
- [ ] Complete provider/manual callback verification.
- [ ] Update documentation and requirement evidence.

### Requirement verification

- Missing/expired credentials produce one scope-correct actionable
  notification.
- Login success resolves or updates the notification without exposing
  credentials.
- Device-code and approved browser flows complete through the same plugin
  actions.
- A callback targets only its named connection/session/login attempt.
- Global attention can be acknowledged without dismissing the auth
  notification.

### Additional implementation verification

- Repeated failed requests do not create notification spam.
- Logout creates a new lifecycle occurrence only when authentication is again
  required.
- An unavailable target connection does not cause callback execution against
  the currently focused connection.