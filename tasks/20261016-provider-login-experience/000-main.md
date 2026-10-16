# Provider Login Experience

Deliver provider-owned login methods consistently across command-line,
interactive-terminal, mobile, and desktop entrypoints while keeping
application-global attention as an optional follow-up rather than a login
prerequisite.

## Requirements checklist

- [ ] Codex supports browser login alongside the existing device-code flow
  without changing the saved credential format consumed by OpenAI Responses.
- [ ] Anthropic subscription OAuth adopts the same provider-neutral action,
  callback, and owning-surface notification UX after its authentication plugin
  is implemented.
- [ ] A contributed terminal login command drives one complete interactive
  login flow, reports progress, and remains active until success, failure,
  cancellation, or expiry.
- [ ] Mobile and desktop invoke provider-owned actions and contain no OAuth
  token exchange, PKCE, or credential persistence logic.
- [ ] Authentication-required conditions can create stable, actionable
  notifications in their owning connection or session without depending on
  application-global attention.
- [ ] Browser callbacks target only their named connection and login attempt;
  unavailable targets can retain a pending callback for later continuation.
- [ ] Device-code login, API-key authentication, and OpenRouter-hosted Claude
  remain independently usable where applicable.
- [ ] A later global-attention integration can surface selected provider-auth
  transitions across open connections without changing login correctness or
  owning-notification lifecycle.
- [ ] Credentials, authorization codes, refresh tokens, PKCE verifiers, and
  callback secrets remain backend/plugin-owned and absent from ordinary
  displays, notifications, command completion, logs, and diagnostics.

## Open requirement questions

1. What exact top-level and interactive command grammar should be the public
   contract?
   - Current direction: one complete flow such as
     `crystal-lattice auth login codex` or `/login anthropic`, rather than
     requiring users to coordinate separate start/status/cancel commands.
2. Which provider flows may bind a loopback callback server, and which require
   a custom app link, universal link, device-code flow, or manual pasted
   redirect fallback?
3. Should terminal login open the system browser automatically, print a link,
   or do both by default?
4. How should an interactive slash-command login temporarily coexist with
   normal terminal input while it waits for the callback?

## Subtasks

- [ ] `tasks/20261016-provider-login-experience/010-codex-browser-login-and-method-selection.md`
- [ ] `tasks/20261016-provider-login-experience/020-provider-login-notifications-and-anthropic-adoption.md`
- [ ] `tasks/20261016-provider-login-experience/030-provider-auth-global-attention.md`

## Supporting details

- Current ChatGPT/Codex authentication is device-code based and already stores
  credentials consumed by the OpenAI Responses provider.
- Generic action dialogs, action displays, action deep links, and disconnected
  pending-callback handling already exist.
- The direct Anthropic provider runtime is complete for API-key requests;
  subscription OAuth is owned by
  `tasks/20260824-direct-claude-provider-and-plugin-login/020-claude-authentication-plugin.md`.
- Generic contributed command discovery and execution are owned by
  `tasks/20260824-plugin-driven-cli-and-interactive-terminal-commands.md`.
- The former combined task
  `tasks/20260824-provider-login-notifications-and-deep-link-ux.md` mixed core
  login behavior with optional global-attention presentation and is split into
  this task group.
- The local `../pi` implementation remains a behavioral reference for Codex
  and Anthropic browser OAuth, loopback callbacks, manual fallback, refresh,
  and credential consumption.

## Execution plan

Status: Draft

Implement the generic terminal command capability first, then complete the
Codex browser/device login experience as the first provider consumer.
Implement Anthropic subscription OAuth and adopt the same action, callback,
and owning-notification conventions. Complete native Anthropic server web
search before the final Anthropic cross-entrypoint acceptance task.

Treat global attention as a separate final subtask. Core login, callback,
credential, command, and owning-notification requirements must be independently
complete before attention work begins.

### Implementation decisions and open questions

- Decision: a login command represents one complete interactive operation,
  not a required sequence of user-issued start/status/cancel commands.
- Decision: provider auth plugins own protocol behavior, loopback servers,
  callbacks, state, PKCE, refresh, persistence, and cancellation.
- Decision: command and frontend adapters execute the same plugin actions.
- Decision: owning-surface auth notifications do not depend on global
  attention.
- Decision: global attention never navigates automatically and is not required
  for callback completion.
- Open: approve the exact command grammar, browser-opening policy, callback
  modes, and interactive-terminal waiting behavior before implementation.

### Documentation

- Document one complete login flow for top-level CLI, interactive terminal,
  mobile, and desktop.
- Distinguish provider protocol behavior from command/action presentation.
- Document loopback, app-link, device-code, and manual callback variants only
  after provider verification.
- Document owning notifications separately from optional global attention.

### Task checklist

- [ ] Approve the generic contributed-command contract and one-flow login UX.
- [ ] Complete Codex browser login and method selection.
- [ ] Complete Anthropic subscription OAuth.
- [ ] Adopt the shared login and owning-notification UX for Anthropic.
- [ ] Complete native Anthropic server web search.
- [ ] Complete Anthropic mobile/desktop/terminal convergence and combined
  OAuth-plus-search acceptance.
- [ ] Complete provider-auth global attention as a non-blocking enhancement.
- [ ] Reconcile superseded OAuth task references and documentation.

### Requirement verification

- Codex device-code and browser login both produce credentials usable by the
  existing OpenAI Responses path.
- One top-level command and one contributed slash command each complete login
  without requiring a separate status command.
- Anthropic browser OAuth produces credentials used by a subsequent direct
  provider request.
- Owning-surface auth notifications remain actionable without the global
  attention frontend.
- Global attention can be disabled or unavailable without breaking login,
  callback completion, credential refresh, or logout.

### Additional implementation verification

- Ctrl-C or equivalent terminal cancellation cannot leave a newer login
  attempt vulnerable to an older callback.
- Loopback callback servers bind only for the active attempt, validate state,
  return a bounded browser response, and shut down after terminal completion.
- Reconnection cannot execute a pending callback against the currently focused
  but incorrect connection.
