# Persistent Request And Action Errors

Persist selected terminal server-side request and action failures through the
existing notification model while keeping validation, connection, and
frontend-local failures ephemeral.

## Requirements checklist

- [ ] A terminal model request, provider, or tool-loop infrastructure failure
  is persisted as a notification in the owning session.
- [ ] An operational session-action failure is persisted in the owning
  session, and an operational application-action failure is persisted for the
  owning connection/application.
- [ ] Validation, action-resolution, connection-lifecycle, and frontend-local
  failures remain ephemeral.
- [ ] Persistent failures expose safe user-facing information and remain
  available through normal notification lifecycle and history behavior.
- [ ] Existing immediate request and action error responses remain available
  so persistence does not delay current feedback.

Parent Task: `tasks/20260824-operational-notifications-and-global-attention/000-main.md`

Depends On:

- the completed Stage A–D notification substrate in
  `tasks/20260619-generic-session-notifications/045-stage-1-authoritative-dismissal-retention-history-and-interaction-readiness.md`.

## Supporting details

- `AgentApplication.send_request(...)` already owns `request_error` lifecycle
  dispatch and observes terminal tool-loop error events.
- The shared request coordinator now owns request startup and event
  publication outside FastAPI.
- FastAPI currently maps action exceptions into error envelopes after calling
  `AgentApplication.execute_action_with_metadata(...)`.
- The application layer can determine the resolved action owner and session
  context and is therefore the correct persistence boundary.
- A transport failure before the server receives an action cannot be
  authoritatively persisted by that server and remains frontend connection
  state.
- Notification bodies and source metadata must not contain credentials,
  authorization headers, provider payloads, stack traces, sensitive local
  paths, or model-visible content.

## Execution plan

Status: Draft

Define an application-layer operational error classification with explicit
persistent and ephemeral categories. Keep HTTP status/envelope mapping in the
adapter, but move enough action outcome/error normalization into
`AgentApplication` that terminal failures can be persisted consistently for
HTTP, terminal, plugins, and future application entrypoints.

For requests, create a session error notification only for terminal execution
failures after request admission. Do not persist malformed input, missing
sessions, readonly views, duplicate admission, or connection transport
failure. Preserve the current error and completion events.

For actions, distinguish:

- validation/resolution/not-found/readonly errors that never entered
  operational plugin work;
- operational exceptions or explicit structured operational failures after
  action execution began.

Persist per-occurrence failures with request/action identity and safe
classification. A plugin may return structured safe details or retry actions,
but arbitrary exception text is sanitized before notification creation.
Notification persistence failure remains failure-contained and never replaces
the original action/request result.

Add Retry/View follow-ups only when a normal existing action or request path
can execute them safely. A later successful retry resolves an earlier error
only when an explicit correlation identifies that condition; success does not
silently resolve unrelated historical failures.

### Implementation decisions and open questions

- **Decided:** Request failures and session-action failures use session
  notifications; application-action operational failures use application
  notifications.
- **Decided:** Connection open/reconnect/pairing/repair errors remain under
  the connection lifecycle and are not duplicated as notifications.
- **Decided:** Validation, unknown/ambiguous action, malformed input,
  not-found, readonly, duplicate-admission, and frontend-local failures remain
  ephemeral.
- **Recommendation:** Use one lifecycle occurrence per terminal request or
  action execution. Reserve stable-key in-place updates for a continuing
  condition explicitly identified by the producer.
- **Recommendation:** Introduce a typed safe error descriptor rather than
  deriving persistence or severity from exception message text.

### Documentation

- Update notification specifications with the persistent-versus-ephemeral
  error boundary and scope mapping.
- Update application development documentation for action/request error
  classification, sanitization, and failure containment.
- Update plugin action documentation with the structured operational failure
  shape and safe retry guidance.
- Update frontend documentation only for delivered persistent error behavior;
  connection-error documentation remains under the connection lifecycle.

### Task checklist

- [ ] Define typed operational error categories and sanitization.
- [ ] Move action failure classification to the application execution
  boundary while preserving HTTP envelopes.
- [ ] Persist terminal request failures as session notifications.
- [ ] Persist operational session/application action failures in their owning
  scope.
- [ ] Add safe retry/view follow-ups where applicable.
- [ ] Add request, action, API, store, and failure-containment tests.
- [ ] Add SDK/mobile/desktop integration coverage for rehydrated errors.
- [ ] Update specifications, plugin/application docs, and requirement
  evidence.
- [ ] Complete manual owning-session/connection visibility smoke tests.

### Requirement verification

- Request persistence: a controlled provider/tool-loop failure produces both
  the immediate error event and a rehydratable session error notification.
- Action persistence: public session/application action calls prove
  operational failures persist in the correct scope and preserve direct error
  responses.
- Ephemeral boundary: validation, resolution, readonly, connection, and local
  frontend failures produce no server notification.
- Safety: tests prove redaction and that notification-store failure cannot
  replace or abort the original request/action failure path.
- Recovery: retry/view actions use existing public paths and do not mutate
  unrelated terminal records.

### Additional implementation verification

- Repeated failures do not overwrite an earlier terminal occurrence.
- Concurrent failures in different sessions retain independent identity.
- Malformed plugin error details are ignored or sanitized without failing the
  error path.
