# Direct Claude Provider And Plugin-Driven Login

Deliver a direct Claude provider path and plugin-owned authentication lifecycle
that work consistently from mobile, desktop, top-level CLI, and the interactive
terminal while preserving the existing OpenRouter Claude option.

## Requirements checklist

### Functional requirements

- [ ] A direct Claude provider can execute ordinary and tool-enabled requests
  without routing through OpenRouter.
- [ ] The provider consumes the approved supported Claude credential modes.
- [ ] A Claude authentication application plugin exposes login, status,
  cancellation, refresh where applicable, and logout actions.
- [ ] Saved Claude credentials are directly usable by the provider through one
  documented credential contract.
- [ ] Mobile and desktop expose the Claude authentication actions through the
  standard application/session action UI.
- [ ] Claude authentication works through plugin-contributed top-level and
  interactive terminal commands.
- [ ] Missing, expired, revoked, cancelled, and invalid authentication states
  produce actionable plugin-owned results.
- [ ] Existing `claude-tools` work with the direct provider.
- [ ] Existing OpenRouter-based Claude agents remain available and are not
  silently replaced.

### Non-functional requirements

- [ ] Credentials use configurable secure persistence and are excluded from
  ordinary logs, notifications, session records, and diagnostics.
- [ ] Direct-provider selection and fallback behavior are explicit and do not
  silently route a failed request through another paid provider.
- [ ] OAuth state, PKCE, refresh, supersession, and cancellation are safe when
  subscription OAuth is supported.
- [ ] Claude-specific behavior remains in provider/auth plugins rather than
  generic application, terminal, or frontend code.
- [ ] Deterministic provider/auth tests and selective hosted verification cover
  the supported credential modes and tool loop.
- [ ] Public documentation distinguishes direct Claude access from
  OpenRouter-hosted Claude access.

## Open requirement questions

1. Which credential modes are required for the first complete release?
   - Options: Anthropic API key, Claude subscription OAuth compatible with the
     inspected `pi` flow, or both.
   - Recommendation: support API-key mode as the deterministic direct-provider
     baseline and subscription OAuth when provider behavior can be verified
     without weakening credential or account safety.
2. Should direct Claude become a new default agent or remain an explicitly
   selected configuration?
   - Recommendation: keep the existing OpenRouter Claude default until direct
     provider/auth hosted verification is complete.

## Subtasks

- [ ] `tasks/20260824-direct-claude-provider-and-plugin-login/010-direct-claude-provider-runtime.md`
- [ ] `tasks/20260824-direct-claude-provider-and-plugin-login/020-claude-authentication-plugin.md`
- [ ] `tasks/20260824-direct-claude-provider-and-plugin-login/030-claude-client-and-terminal-integration.md`

## Supporting facts

- The current default `claude` agent uses the OpenRouter provider with an
  Anthropic model slug.
- `plugins/claude-tools` provides Claude-compatible tools and compaction but
  does not implement a direct Anthropic provider or Claude login.
- The existing ChatGPT auth application plugin demonstrates background login,
  saved credentials, status, cancellation, logout, and provider consumption.
- Generic action deep links and action-dialog selection already exist.
- Plugin-driven terminal commands are tracked separately so the provider task
  does not add another command framework.

## Execution plan

Status: Draft

Implement the work in three independently reviewable stages. First establish
the direct provider and credential-consumption boundary. Next implement the
plugin-owned authentication lifecycle. Finally expose and verify the shared
actions across terminal and React Native frontends.

Do not change the default Claude agent until the direct provider, credential
refresh, tool behavior, and hosted smoke evidence are complete. Stop for user
review if provider subscription authentication requires undocumented
credential extraction, imitation of private clients, or materially different
security boundaries from the approved credential mode.

### Implementation decisions and open questions

- Decision: provider transport and authentication UI are separate plugins
  joined by a documented credential contract.
- Decision: `claude-tools` remains provider-independent where its current
  interop contract permits.
- Decision: OpenRouter remains a supported explicit alternative.
- Open: resolve the initial credential-mode requirement before approving
  subtask 010/020 implementation plans.

### Documentation

- Add provider installation, configuration, credential, model, tool, and
  troubleshooting documentation in the owning provider package.
- Add Claude login, status, logout, storage, and callback documentation in the
  auth plugin.
- Update default-agent and terminal/mobile guidance only when behavior is
  delivered.

### Task checklist

- [ ] Resolve the supported credential modes and default-agent decision.
- [ ] Execute and verify direct provider runtime subtask 010.
- [ ] Execute and verify authentication plugin subtask 020.
- [ ] Execute and verify frontend/terminal integration subtask 030.
- [ ] Run selective real-provider and saved-login smoke tests.
- [ ] Reconcile documentation and requirement evidence.
- [ ] Record whether and when the default Claude agent should change.

### Requirement verification

- A direct Claude request and a tool-enabled request complete using the
  supported credential mode.
- Login/status/logout and credential refresh behave consistently across
  application actions and terminal bindings.
- Mobile and desktop can complete the supported login flow and use the saved
  credential on a subsequent provider request.
- OpenRouter Claude behavior remains available and unchanged unless explicitly
  selected otherwise.

### Additional implementation verification

- Revoked or expired credentials cannot fall through to an unintended
  provider.
- Concurrent login attempts and provider requests have deterministic
  supersession behavior.
- Credential files and diagnostics contain no unnecessary provider response or
  account data.