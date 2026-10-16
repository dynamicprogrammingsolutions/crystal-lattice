# Provider Login Notifications And Anthropic Adoption

Adopt the Codex-tested login action and callback UX for Anthropic subscription
OAuth, and provide stable actionable auth notifications in each provider's
owning connection or session without requiring global attention.

## Requirements checklist

- [ ] Missing, expired, revoked, or invalid provider authentication can create
  one stable actionable notification in the owning connection or session.
- [ ] Provider-owned actions exposed from the notification can start or resume
  login, show useful progress, cancel the active attempt, retry where valid,
  and log out.
- [ ] Codex browser/device method selection and Anthropic browser login use the
  same provider-neutral action and display conventions.
- [ ] Anthropic subscription OAuth is available from mobile, desktop,
  top-level CLI, and the interactive terminal without frontend-owned protocol
  logic.
- [ ] Login completion, refresh, cancellation, and logout invalidate or
  refresh affected action/provider state without requiring an unrelated user
  message.
- [ ] Browser callbacks and pending continuation preserve connection and login
  attempt ownership.
- [ ] API-key Anthropic configurations remain usable without OAuth prompts.
- [ ] OpenRouter Claude configurations do not show direct-Anthropic
  authentication requirements.
- [ ] Owning-surface notifications and login correctness work when
  application-global attention is unavailable or disabled.
- [ ] Repeated authentication failures do not create notification spam or
  expose provider credentials and callback secrets.

Parent Task:
`tasks/20261016-provider-login-experience/000-main.md`

Depends On:

- `tasks/20261016-provider-login-experience/010-codex-browser-login-and-method-selection.md`
- `tasks/20260824-direct-claude-provider-and-plugin-login/020-claude-authentication-plugin.md`

## Open requirement questions

1. Should auth-required notifications be application-scoped by credential
   target, session-scoped by failed request, or linked through one shared
   credential occurrence with session projections?
2. Which success transitions should resolve silently versus leave a short
   terminal notification in the owning surface?
3. Which login-method preference, if any, belongs in provider configuration
   rather than being selected for each attempt?

## Supporting details

- The authoritative notification substrate, action displays, dialogs, deep
  links, and disconnected pending callback handling already exist.
- Global attention is a temporary cross-application presentation and is not
  required to persist or act on an owning notification.
- Anthropic OAuth lifecycle and secure credential persistence belong to
  `tasks/20260824-direct-claude-provider-and-plugin-login/020-claude-authentication-plugin.md`.
- Final Anthropic cross-entrypoint verification belongs to
  `tasks/20260824-direct-claude-provider-and-plugin-login/030-claude-client-and-terminal-integration.md`.

## Execution plan

Status: Draft

Define a provider-neutral auth lifecycle/display convention implemented by
the Codex and Anthropic auth plugins. Each credential target owns a stable
notification occurrence whose actions delegate to the plugin's existing
login lifecycle. Notification dismissal does not cancel login or delete
credentials.

Adopt the Codex method-selection and callback conventions in the Anthropic
plugin after its OAuth backend is complete. Keep API-key and OpenRouter
configurations outside direct-provider OAuth prompting.

### Implementation decisions and open questions

- Decision: provider auth plugins remain the executable source of truth.
- Decision: owning notifications are independently useful and do not carry
  global-attention dependencies.
- Decision: callback routing is provider-neutral while state validation and
  token exchange remain plugin-owned.
- Decision: notification arrival never navigates automatically.
- Open: approve notification scope and post-success lifecycle semantics before
  implementation.

### Documentation

- Document provider-neutral auth notification lifecycle and safe content.
- Document Codex method selection and Anthropic browser-login adoption.
- Document API-key, direct OAuth, compatible endpoint, and OpenRouter
  distinctions.
- State explicitly that global attention is optional presentation.

### Task checklist

- [ ] Define stable auth-notification keys, scope, and lifecycle mapping.
- [ ] Add Codex auth-required notification publication and resolution.
- [ ] Adopt the action/dialog/callback conventions in the Anthropic auth
  plugin.
- [ ] Add provider/config-aware visibility for app actions and notifications.
- [ ] Add state refresh/invalidation after auth mutations.
- [ ] Add backend, SDK, mobile, desktop, terminal, and callback tests.
- [ ] Complete approved manual Codex and Anthropic callback verification.
- [ ] Update user/plugin documentation and requirement evidence.

### Requirement verification

- Missing or expired credentials produce one scope-correct actionable
  notification without global attention.
- Successful login resolves or updates the owning notification and enables a
  subsequent provider request without an unrelated message.
- Codex device/browser and Anthropic browser flows use the same generic action
  and display path while preserving provider-specific protocol behavior.
- API-key and OpenRouter configurations remain free of misleading direct
  OAuth prompts.

### Additional implementation verification

- Dismissing the notification does not cancel a login attempt.
- Logout produces a new auth-required occurrence only when authentication is
  required again.
- One connection cannot complete or cancel another connection's login
  attempt.
