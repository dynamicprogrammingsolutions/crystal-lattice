# MCP Auth-Required Session Notifications

Publish persistent, actionable session notifications when MCP preparation finds
an authentication-required or failed server, while allowing the request to
continue safely with the remaining tools.

## Requirements checklist

### Functional requirements

- [ ] MCP request preparation publishes a warning notification when a
  configured server requires authentication.
- [ ] An authentication-required notification offers Sign in and MCP status
  actions through the existing MCP application plugin.
- [ ] A failed MCP server notification offers appropriate status and reconnect
  actions.
- [ ] Other MCP servers and ordinary request execution continue when one server
  is unavailable.
- [ ] An unavailable MCP server contributes zero tools rather than hanging or
  aborting the request.
- [ ] Repeated preparation updates the same active server-specific
  notification instead of creating duplicates.
- [ ] Successful login, check, or reconnect resolves or updates the existing
  notification.
- [ ] Notifications rehydrate after reopening the owning session.
- [ ] Real-backend tests cover notification, Sign in, callback, token reuse,
  reconnect, and notification resolution.

### Non-functional requirements

- [ ] Notification publication failure never aborts MCP preparation or the
  model request.
- [ ] OAuth codes, state, tokens, authorization headers, and sensitive server
  errors never enter notification content, events, or logs.
- [ ] Notification behavior is shared by Codex and Claude MCP tool consumers
  without frontend-specific or provider-specific copies.
- [ ] MCP OAuth and status behavior remain owned by `mcp-runtime-app`; the
  notification producer does not duplicate login logic.
- [ ] No MCP-specific notification component or transport is introduced.
- [ ] Existing MCP startup, status, callback, and login behavior remains
  compatible.

Parent Task:
`tasks/20260611-mcp-oauth-action-deeplinks/000-main.md`

Depends On:

- `tasks/20260611-mcp-oauth-action-deeplinks/015-mcp-auth-required-no-hang-and-login-flow.md`
- `tasks/20260619-generic-session-notifications/040-stage-1-dummy-plugin-integration-tests.md`

## Supporting facts

- MCP auth-required detection, active checking, login start/completion, token
  persistence, and generic deep-link routing are implemented.
- Tool contexts already receive a failure-contained session
  `notification_sink`.
- The existing task-015 follow-up describes the intended non-blocking Mode A
  notification behavior but did not implement it.
- Blocking request interactions remain separate future work.

## Execution plan

Status: Draft

Add a provider-neutral notification publication helper at the shared MCP tool
preparation boundary or the narrowest shared consumer boundary that has both
the server status rows and a session-bound notification sink.

Use stable keys such as `mcp:<server-name>:auth_required` and
`mcp:<server-name>:failed`. Build follow-up actions that call the existing MCP
application actions with fixed server identity plus current session/connection
context. Resolve or replace active notifications after a successful status
transition.

Add deterministic Python coverage first, followed by public HTTP/SDK and
React Native real-backend integration. Do not use a live Figma account as the
acceptance path.

### Implementation decisions and open questions

- Decision: initial behavior is non-blocking Mode A.
- Decision: server status is authoritative; notification publication is a
  recoverable presentation side effect.
- Decision: one active notification exists per session, MCP server, and
  condition.
- Open: choose whether failed and auth-required transitions reuse one stable
  server key or separate keys after verifying replacement/resolution UX.

### Documentation

- Update MCP plugin docs with auth-required/failed notification behavior and
  sensitive-data constraints.
- Link notification authoring guidance rather than duplicating lifecycle
  semantics.
- Update task-015 completion/follow-up notes and MCP configuration guidance.

### Task checklist

- [ ] Select the shared MCP notification publication boundary.
- [ ] Define stable keys, safe content, and follow-up mappings.
- [ ] Publish auth-required and failed notifications during preparation.
- [ ] Resolve/update notifications after check, login, and reconnect.
- [ ] Add Python and application integration tests.
- [ ] Add SDK and mobile/desktop real-backend coverage.
- [ ] Complete manual notification → Sign in → reconnect smoke.
- [ ] Update MCP and notification documentation.

### Requirement verification

- A protected MCP server produces one persisted session notification while the
  request continues.
- Sign in executes the existing MCP login action and successful reconnect
  removes or terminally updates the warning.
- Repeated requests do not create duplicate active records.
- A second available MCP server still contributes tools.
- Notification publication failure leaves request preparation successful.

### Additional implementation verification

- Grouped auth exceptions and generic failures produce the correct safe
  notification category.
- Server names and sanitized status text cannot inject secrets or unsupported
  display actions.
- Notification lifecycle remains correct across application reload.