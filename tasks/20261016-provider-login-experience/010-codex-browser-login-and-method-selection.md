# Codex Browser Login And Method Selection

Add a production-ready Codex browser OAuth path alongside the existing
device-code flow, using one complete contributed terminal login operation and
the existing provider action/credential architecture.

## Requirements checklist

- [ ] Existing Codex device-code login remains supported and selectable.
- [ ] Codex browser OAuth performs PKCE authorization, callback validation,
  token exchange, refresh-compatible persistence, and account metadata
  extraction without changing the credential format consumed by OpenAI
  Responses.
- [ ] A top-level contributed command can start one complete Codex login flow,
  present or open the authorization URL, report progress, wait for callback,
  and finish with a terminal result.
- [ ] The interactive terminal can invoke the same complete flow through a
  contributed slash command.
- [ ] When provider policy permits, terminal browser login uses a temporary
  loopback callback server owned by the auth plugin and closes it after
  success, failure, cancellation, or expiry.
- [ ] Mobile and desktop start and complete browser login through plugin
  actions and generic deep-link routing rather than running an OAuth server or
  exchanging tokens in frontend code.
- [ ] Users can select among the supported Codex login methods through
  standard action dialog controls or command arguments.
- [ ] Callback state, PKCE verifier, authorization code, access token, refresh
  token, and account identifiers remain out of ordinary displays and logs.
- [ ] Stale, duplicate, expired, cancelled, and superseded callbacks cannot
  replace current credentials.

Parent Task:
`tasks/20261016-provider-login-experience/000-main.md`

Depends On:

- `tasks/20260824-plugin-driven-cli-and-interactive-terminal-commands.md`

## Open requirement questions

1. Which redirect URIs are accepted by the current Codex OAuth client:
   loopback HTTP, custom app URI, universal link, or only provider-controlled
   redirects?
2. Is a manually pasted redirect/code fallback required in addition to the
   loopback server and app-link paths?
3. Should `crystal-lattice auth login codex` open the browser automatically,
   print the link, or do both?
4. Should `/login codex` block ordinary prompt entry until completion or run
   as a terminal-owned foreground operation with explicit cancellation?

## Supporting details

- `plugins/chatgpt-auth-app` currently implements device-code login, polling,
  status, cancellation, logout, credential persistence, and token exchange.
- `plugins/openai_responses` already consumes and refreshes the saved ChatGPT
  credential contract.
- The local `../pi` Codex implementation uses PKCE, a localhost callback
  server, a manual pasted redirect fallback, and bearer-token plus account-ID
  request headers.
- Current `pi`, OpenCode, and Codex CLI login experiences should be inspected
  before finalizing browser opening, URL presentation, progress output,
  timeout, Ctrl-C, and terminal restoration behavior.
- Generic frontend action deep links and pending callback routing already
  exist; provider redirect acceptance remains to be verified.

## Execution plan

Status: Draft

First verify the supported redirect modes against current provider behavior.
Then extend the ChatGPT auth plugin with browser-login attempt state and one
foreground command-oriented orchestration path. Preserve device-code behavior
and credential compatibility.

The plugin owns the temporary callback server and login lifecycle. The command
adapter starts the bound action, renders safe progress/status updates, waits
for terminal completion, and maps terminal cancellation to the provider-owned
cancel action. Frontends use start/complete actions and generic deep links.

### Implementation decisions and open questions

- Decision: browser and device-code login are methods of one provider auth
  plugin and produce one compatible credential format.
- Decision: users do not need to issue a separate status command to complete a
  normal terminal login.
- Decision: the loopback callback server, when supported, is plugin-owned and
  attempt-scoped.
- Decision: app frontends call actions and never perform the token exchange.
- Open: approve the redirect variants, manual fallback, browser-opening
  policy, and exact terminal command syntax after the provider probe.

### Documentation

- Document supported Codex login methods and redirect limitations.
- Document the complete top-level and slash-command flows.
- Document terminal cancellation, expiry, browser errors, and manual fallback
  if delivered.
- Preserve current credential and refresh documentation.

### Task checklist

- [ ] Inspect and record current `pi`, OpenCode, and Codex foreground login UX.
- [ ] Verify current Codex redirect and callback restrictions.
- [ ] Define browser-login attempt and callback state.
- [ ] Implement browser authorization and token exchange.
- [ ] Implement attempt-scoped loopback callback handling where supported.
- [ ] Bind the complete flow to top-level and slash commands.
- [ ] Add action-dialog method selection for app frontends.
- [ ] Add lifecycle, supersession, cancellation, redaction, and refresh tests.
- [ ] Run approved manual provider verification.
- [ ] Update current documentation and requirement evidence.

### Requirement verification

- Device-code login continues to work unchanged.
- Browser login completes through one command invocation and produces
  credentials used by an OpenAI Responses ChatGPT/Codex request.
- Mobile or desktop can complete the supported browser flow through actions
  and generic callback routing.
- Cancelled, expired, duplicate, and stale callbacks do not modify active
  credentials.

### Additional implementation verification

- The callback listener stops after every terminal outcome and cannot accept a
  later callback for the completed attempt.
- Status output contains no authorization code, token, verifier, or sensitive
  account claim.
- Terminal interruption returns control predictably and leaves a subsequent
  login attempt usable.
