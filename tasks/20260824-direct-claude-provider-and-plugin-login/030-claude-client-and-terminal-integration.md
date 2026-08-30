# Anthropic Client And Terminal Integration

Expose the direct Anthropic provider and OAuth actions consistently in mobile,
desktop, top-level CLI, and the interactive terminal, then verify the complete
saved-login request flow.

## Requirements checklist

### Functional requirements

- [ ] Mobile and desktop show appropriate Anthropic OAuth login, status,
  cancel, and logout actions for direct `anthropic` configurations.
- [ ] The Anthropic auth plugin contributes top-level and interactive terminal
  command bindings.
- [ ] Generic `/action` can invoke the same Anthropic actions.
- [ ] Login completion invalidates or refreshes affected provider/action state
  without requiring an unrelated user message.
- [ ] A saved OAuth login can be used for an ordinary and tool-enabled request
  from each supported application entrypoint.
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
- `tasks/20260824-direct-claude-provider-and-plugin-login/020-claude-authentication-plugin.md`
- `tasks/20260824-plugin-driven-cli-and-interactive-terminal-commands.md`

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

### Implementation decisions and open questions

- Decision: direct `anthropic` configuration and effective auth mode control
  action visibility.
- Decision: command names are plugin-owned bindings under the generic command
  contract.
- Decision: API-key configurations do not require or advertise OAuth login.
- Open: finalize user-facing command names with the OAuth plugin plan.

### Documentation

- Update mobile, desktop, terminal, and provider quickstarts with one shared
  OAuth login/status/logout workflow.
- Document API-key, OAuth, Anthropic-compatible, and OpenRouter selection
  clearly.

### Task checklist

- [ ] Add configuration-aware UI/action declarations.
- [ ] Add top-level and slash command descriptors.
- [ ] Add refresh/invalidation behavior after auth mutations.
- [ ] Add backend and SDK integration tests.
- [ ] Add mobile and desktop component/native tests.
- [ ] Run terminal and real-provider smoke tests.
- [ ] Complete manual mobile/desktop OAuth and request checkpoints.
- [ ] Update user documentation.

### Requirement verification

- Each frontend can start OAuth login, observe status, cancel, and logout.
- Top-level command, slash command, and `/action` invoke the same action.
- Saved credentials support a subsequent real direct-provider request.
- API-key and OpenRouter configurations remain free of misleading OAuth
  prompts.

### Additional implementation verification

- Reopening or reconnecting a frontend preserves accurate auth status.
- One connection cannot execute a callback against another connection.
- Account/credential details remain absent from generic connection records.