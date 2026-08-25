# Claude Client And Terminal Integration

Expose the direct Claude provider and authentication actions consistently in
mobile, desktop, top-level CLI, and the interactive terminal, then verify the
complete saved-login request flow.

## Requirements checklist

### Functional requirements

- [ ] Mobile and desktop show appropriate Claude login, status, cancel, and
  logout actions for direct-Claude configurations.
- [ ] The Claude auth plugin contributes top-level and interactive terminal
  command bindings.
- [ ] Generic `/action` can invoke the same Claude actions.
- [ ] Login completion invalidates or refreshes affected provider/action state
  without requiring an unrelated user message.
- [ ] A saved login can be used for an ordinary and tool-enabled request from
  each supported application entrypoint.
- [ ] OpenRouter Claude configurations do not show misleading direct-Claude
  authentication requirements.

### Non-functional requirements

- [ ] Frontends contain no Claude protocol or token-exchange implementation.
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
Claude auth plugin. Route every frontend through existing action runners and
generic deep-link handling. Use real backend component/integration harnesses to
prove that saved credentials become visible to the direct provider after
login, refresh, and reconnect.

Keep visual work limited to standard action/dialog/notification components. Any
need for Claude-specific frontend state or components is a scope boundary and
requires user review.

### Implementation decisions and open questions

- Decision: direct-Claude configuration controls action visibility.
- Decision: command names are plugin-owned bindings under the generic command
  contract.
- Open: exact user-facing naming depends on whether one or multiple credential
  modes ship.

### Documentation

- Update mobile, desktop, terminal, and provider quickstarts with one shared
  login/status/logout workflow.
- Document OpenRouter versus direct-Claude selection clearly.

### Task checklist

- [ ] Add configuration-aware UI/action declarations.
- [ ] Add top-level and slash command descriptors.
- [ ] Add refresh/invalidation behavior after auth mutations.
- [ ] Add backend and SDK integration tests.
- [ ] Add mobile and desktop component/native tests.
- [ ] Run terminal and real-provider smoke tests.
- [ ] Complete manual mobile/desktop login and request checkpoints.
- [ ] Update user documentation.

### Requirement verification

- Each frontend can start login, observe status, cancel, and logout.
- Top-level command, slash command, and `/action` invoke the same action.
- Saved credentials support a subsequent real direct-provider request.
- OpenRouter configurations remain free of direct-auth prompts.

### Additional implementation verification

- Reopening or reconnecting a frontend preserves accurate auth status.
- One connection cannot execute a callback against another connection.
- Account/credential details remain absent from generic connection records.