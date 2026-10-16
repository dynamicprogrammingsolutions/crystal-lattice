# Anthropic OAuth Authentication Plugin

Implement plugin-owned Anthropic OAuth credential acquisition, persistence,
status, refresh, cancellation, and logout using the provider contract defined
by subtask 010.

## Requirements checklist

### Functional requirements

- [ ] The plugin exposes OAuth login, status, cancel, refresh, and logout
  application actions.
- [ ] A completed login stores credentials in the provider-consumable contract
  defined by subtask 010.
- [ ] The provider can select `oauth` and `auto` authentication modes without
  changing the API-key configuration contract.
- [ ] Login attempts have explicit identity, progress, completion, failure,
  expiry, cancellation, and supersession behavior.
- [ ] Browser callbacks support the verified provider-compatible variants:
  generic action-deep-link routing for app frontends and an attempt-scoped
  plugin-owned loopback callback server for terminal flows when permitted.
- [ ] The action lifecycle can drive one complete foreground terminal login
  operation: start authorization, expose safe instructions/progress, wait for
  callback, handle interruption, and return a terminal result.
- [ ] Logout and revocation remove or invalidate saved OAuth credentials.

### Non-functional requirements

- [ ] Credentials use configurable secure persistence and atomic replacement.
- [ ] OAuth state, PKCE verifier, refresh token, authorization code, and access
  token values never enter ordinary displays, notifications, or logs.
- [ ] A stale callback or polling result cannot overwrite a newer login
  attempt.
- [ ] OAuth protocol behavior remains inside the auth plugin and narrow
  provider credential/transport hooks.
- [ ] Deterministic fixtures cover every lifecycle before manual/provider
  validation.
- [ ] The local `../pi` implementation is used as a protocol and behavior
  reference, with deviations documented and tested.

## Open requirement questions

1. Which callback URI variants, client identity, scopes, and provider headers
   are accepted for Anthropic subscription OAuth?
2. Does the terminal flow require a manual pasted redirect fallback in
   addition to an attempt-scoped loopback listener?
3. What progress/result contract should the login action expose so a command
   can remain active without repeatedly issuing user-visible status commands?
4. Should the plugin request that the terminal open the browser
   automatically, or provide both an open action and a copyable URL?

Parent Task:
`tasks/20260824-direct-claude-provider-and-plugin-login/000-main.md`

Depends On:

- `tasks/20260824-direct-claude-provider-and-plugin-login/010-direct-claude-provider-runtime.md`

## Supporting facts

- API-key authentication is delivered by subtask 010 and does not require an
  interactive login action.
- Generic application actions, action displays, dialog inputs, open/copy
  follow-ups, and action deep links already exist.
- Managed background processes are available when polling or long-running
  login work is required.
- The ChatGPT auth plugin demonstrates a useful lifecycle pattern but is not a
  protocol authority for Anthropic.
- The local `../pi` repository contains Anthropic PKCE login, callback,
  exchange, refresh, token-expiry, and provider-consumption behavior.

## Execution plan

Status: Draft

Implement a first-party application plugin whose stored output is the
`anthropic` provider credential contract rather than a frontend-specific
session. Reuse generic action/deep-link/display infrastructure and managed
background process support where the selected OAuth flow needs them.

Translate the `../pi` OAuth behavior into this repository's plugin,
persistence, cancellation, redaction, and action contracts. Use deterministic
issuer/token fixtures for lifecycle and security coverage. Add hosted/manual
validation only after callback URIs, client identity, scopes, provider headers,
and refresh semantics have been verified.

For terminal use, expose one provider-owned login workflow that can create and
close an attempt-scoped loopback callback listener, publish bounded progress,
and complete or cancel while the contributed command remains in the
foreground. For mobile and desktop, expose start/complete actions and use
generic deep-link routing. Both entrypoint shapes operate on the same attempt
and credential contracts.

### Implementation decisions and open questions

- Decision: API-key setup remains configuration-only; this task implements
  OAuth rather than an API-key entry form.
- Decision: one active login attempt per credential target; a newer attempt
  supersedes the older one.
- Decision: credential persistence is independent from application session
  history.
- Decision: `auth_mode` uses `api`, `oauth`, and `auto`.
- Decision: the auth plugin owns login and refresh; the provider owns only
  credential consumption and request transport.
- Decision: users do not need to issue a separate status command to complete a
  normal terminal login; status remains an action/lifecycle capability for
  rendering, reconnection, and app frontends.
- Decision: any loopback callback server is auth-plugin-owned, bound to one
  attempt, and stopped after every terminal outcome.
- Open: finalize callback variants, client configuration, browser-opening
  policy, manual fallback, and the action progress contract after a focused
  comparison of `../pi` and current provider behavior.

### Documentation

- Document OAuth login, status, storage path/provider, refresh, logout,
  callback URIs, troubleshooting, and the distinction from API-key config.
- Document the one-command terminal flow separately from app action/deep-link
  completion.
- Document sensitive fields that must never be surfaced or logged.
- Update the Anthropic package specification before implementing any OAuth
  behavior that changes the provider credential or transport contract.

### Task checklist

- [ ] Inspect and record the selected `../pi` OAuth protocol behavior.
- [ ] Define the provider-consumable OAuth credential and login-attempt
  storage.
- [ ] Implement login/status/cancel/refresh/logout actions.
- [ ] Implement browser callback variants, attempt-scoped loopback handling,
  foreground progress, interruption, and supersession.
- [ ] Implement provider `oauth` and `auto` consumption hooks.
- [ ] Add deterministic lifecycle, security, refresh, and supersession tests.
- [ ] Add provider-consumption integration tests.
- [ ] Run approved manual/hosted OAuth verification.
- [ ] Document behavior and limitations.

### Requirement verification

- A completed OAuth login writes credentials consumed by the direct provider.
- One terminal login invocation can remain active through authorization and
  callback completion without requiring a separate user-issued status command.
- Cancelled, expired, failed, and superseded attempts do not write active
  credentials.
- Logout makes a subsequent OAuth-only direct request report authentication
  required.
- Callback state and refresh-token tests reject tampering and stale attempts.
- API-key mode remains independent from OAuth credential state.

### Additional implementation verification

- Credential writes survive process interruption without partial JSON/state.
- Concurrent status checks cannot extend or resurrect an expired attempt.
- Provider errors are redacted before entering action displays.
- Refresh and provider requests cannot race into an older credential replacing
  a newer credential.
- Callback listeners close after success, failure, cancellation, expiry, and
  terminal interruption.