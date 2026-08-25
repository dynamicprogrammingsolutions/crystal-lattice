# Claude Authentication Plugin

Implement plugin-owned Claude credential acquisition, persistence, status,
refresh, cancellation, and logout for the credential modes approved by the
parent task.

## Requirements checklist

### Functional requirements

- [ ] The plugin exposes login, status, cancel, refresh where applicable, and
  logout application actions.
- [ ] The supported login flow stores credentials in the provider-consumable
  contract defined by subtask 010.
- [ ] Login attempts have explicit identity, progress, completion, failure,
  expiry, cancellation, and supersession behavior.
- [ ] Browser callbacks use generic action-deep-link routing when required.
- [ ] Device-code, API-key, or browser-login selection is represented through
  standard action inputs/displays when multiple modes are supported.
- [ ] Logout and revocation remove or invalidate saved provider credentials.

### Non-functional requirements

- [ ] Credentials use configurable secure persistence and atomic replacement.
- [ ] OAuth state, PKCE verifier, refresh token, authorization code, and access
  token values never enter ordinary displays, notifications, or logs.
- [ ] A stale callback or polling result cannot overwrite a newer login
  attempt.
- [ ] Provider-specific protocol behavior remains inside the plugin.
- [ ] Deterministic fixtures cover every lifecycle before manual/provider
  validation.

Parent Task:
`tasks/20260824-direct-claude-provider-and-plugin-login/000-main.md`

Depends On:

- `tasks/20260824-direct-claude-provider-and-plugin-login/010-direct-claude-provider-runtime.md`

## Supporting facts

- Generic application actions, action displays, dialog inputs, open/copy
  follow-ups, and action deep links already exist.
- Managed background processes are available when polling or long-running
  login work is required.
- The ChatGPT auth plugin demonstrates a useful lifecycle pattern but is not a
  protocol authority for Claude.

## Execution plan

Status: Draft

Implement a first-party application plugin whose stored output is the direct
provider credential contract rather than a frontend-specific session. Reuse
generic action/deep-link/display infrastructure and managed background process
support only where the selected protocol needs them.

Use deterministic issuer/token fixtures for lifecycle and security coverage.
Add hosted/manual validation only after callback URIs, client identity, scopes,
and refresh semantics are confirmed from authoritative provider behavior.

### Implementation decisions and open questions

- Decision: one active login attempt per credential target; a newer attempt
  supersedes the older one.
- Decision: credential persistence is independent from application session
  history.
- Open: exact login modes, callback forms, and storage integration follow the
  parent credential decision.

### Documentation

- Document login modes, actions, storage path/provider, status, refresh,
  logout, callback URIs, and troubleshooting.
- Document sensitive fields that must never be surfaced or logged.

### Task checklist

- [ ] Confirm selected authentication protocols and client configuration.
- [ ] Define credential and login-attempt storage.
- [ ] Implement login/status/cancel/refresh/logout actions.
- [ ] Implement deep-link callback or device-code polling as required.
- [ ] Add deterministic lifecycle, security, and supersession tests.
- [ ] Add provider-consumption integration tests.
- [ ] Run approved manual/hosted login verification.
- [ ] Document behavior and limitations.

### Requirement verification

- A completed login writes credentials consumed by the direct provider.
- Cancelled, expired, failed, and superseded attempts do not write active
  credentials.
- Logout makes a subsequent direct request report authentication required.
- Callback state and refresh-token tests reject tampering and stale attempts.

### Additional implementation verification

- Credential writes survive process interruption without partial JSON/state.
- Concurrent status checks cannot extend or resurrect an expired attempt.
- Provider errors are redacted before entering action displays.