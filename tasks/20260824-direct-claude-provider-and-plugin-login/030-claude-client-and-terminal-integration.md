# Anthropic Client And Terminal Integration

Expose the direct Anthropic provider and OAuth actions consistently in mobile,
desktop, top-level CLI, and the interactive terminal, then verify the complete
saved-login request flow.

## Requirements checklist

### Functional requirements

- [ ] Mobile and desktop show appropriate Anthropic OAuth login, status,
  cancel, and logout actions for direct `anthropic` configurations.
- [ ] The Anthropic auth plugin contributes top-level and interactive terminal
  bindings for one complete login flow that reports progress and remains
  active until success, failure, cancellation, or expiry.
- [ ] Generic `/action` can invoke the same Anthropic actions.
- [ ] Login completion invalidates or refreshes affected provider/action state
  without requiring an unrelated user message.
- [ ] A saved OAuth login can be used for an ordinary and tool-enabled request
  from each supported application entrypoint.
- [ ] A saved OAuth login can execute an Anthropic-native server web-search
  request, render its source citations, survive persistence/reload, and
  support a provider-native follow-up request.
- [ ] API-key configurations remain usable without OAuth actions.
- [ ] OpenRouter Claude configurations do not show misleading direct-Anthropic
  authentication requirements.

### Non-functional requirements

- [ ] Frontends contain no Anthropic protocol or token-exchange
  implementation.
- [ ] All entrypoints execute the same plugin actions and render the standard
  action-display contract.
- [ ] Deep-link and command routing preserve connection/session ownership.
- [ ] Native/manual checkpoints supplement rather than replace automated
  backend, SDK, component, and integration coverage.
- [ ] Accessibility labels and terminal completion are stable for supported
  actions.

Parent Task:
`tasks/20260824-direct-claude-provider-and-plugin-login/000-main.md`

Depends On:

- `tasks/20260824-direct-claude-provider-and-plugin-login/010-direct-claude-provider-runtime.md`
- `tasks/20260824-direct-claude-provider-and-plugin-login/011-anthropic-server-web-tools.md`
- `tasks/20260824-direct-claude-provider-and-plugin-login/020-claude-authentication-plugin.md`
- `tasks/20260824-plugin-driven-cli-and-interactive-terminal-commands.md`
- `tasks/20261016-provider-login-experience/020-provider-login-notifications-and-anthropic-adoption.md`

## Execution plan

Status: Draft

Add provider/config-aware UI declarations and plugin command descriptors to the
Anthropic auth plugin. Route every frontend through existing action runners
and generic deep-link handling. Use real backend component/integration
harnesses to prove that saved credentials become visible to the provider after
login, refresh, and reconnect.

Keep visual work limited to standard action/dialog/notification components.
Any need for Anthropic-specific frontend protocol state or components is a
scope boundary and requires user review.

Use this task as the convergence gate for OAuth and native server web search.
The decisive hosted path starts without saved Anthropic credentials, completes
browser OAuth, runs native server search with the saved credential, renders
citations, reloads or reconnects, and completes a follow-up request with
provider-native history.

### Implementation decisions and open questions

- Decision: direct `anthropic` configuration and effective auth mode control
  action visibility.
- Decision: command descriptors are plugin-owned bindings under the generic
  command contract, but normal login is one foreground operation rather than a
  user-coordinated sequence of start and status commands.
- Decision: API-key configurations do not require or advertise OAuth login.
- Decision: provider-auth global attention is not a dependency of this task;
  owning notifications and explicit action results are sufficient for login
  acceptance.
- Open: finalize user-facing command names, aliases, provider inference,
  browser-opening policy, and foreground interruption behavior with the OAuth
  and generic-command plans before implementation.

### Documentation

- Update mobile, desktop, terminal, and provider quickstarts with one complete
  OAuth login flow plus separately meaningful management actions such as
  logout.
- Document API-key, OAuth, Anthropic-compatible, and OpenRouter selection
  clearly.
- Distinguish Anthropic-native server search from the existing
  Gemini/Tavily-backed client search.

### Task checklist

- [ ] Add configuration-aware UI/action declarations.
- [ ] Add top-level and slash command descriptors.
- [ ] Add refresh/invalidation behavior after auth mutations.
- [ ] Add the combined saved-OAuth, native-server-search, citation, reload, and
  follow-up acceptance path.
- [ ] Add backend and SDK integration tests.
- [ ] Add mobile and desktop component/native tests.
- [ ] Run terminal and real-provider smoke tests.
- [ ] Complete manual mobile/desktop OAuth and request checkpoints.
- [ ] Update user documentation.

### Requirement verification

- Each frontend can start OAuth login, observe progress, cancel, and logout.
- A top-level command and slash command each complete login through one
  invocation; `/action` can invoke the same underlying actions.
- Saved credentials support a subsequent real direct-provider request.
- Saved credentials support a real Anthropic-native server web search whose
  citations remain visible after normal response processing, followed by a
  successful post-reload request.
- API-key and OpenRouter configurations remain free of misleading OAuth
  prompts.

### Additional implementation verification

- Reopening or reconnecting a frontend preserves accurate auth status.
- One connection cannot execute a callback against another connection.
- Account/credential details remain absent from generic connection records.