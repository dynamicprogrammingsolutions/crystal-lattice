# Plugin-Driven CLI And Interactive Terminal Commands

Expose application-plugin actions consistently through top-level CLI commands,
plugin-contributed interactive slash commands, and a generic `/action`
fallback without introducing a second execution API.

## Requirements checklist

### Functional requirements

- [ ] Application plugins can bind existing application actions to top-level
  CLI commands and interactive terminal slash commands.
- [ ] The interactive terminal discovers plugin-contributed commands after
  application configuration and plugin loading.
- [ ] Dynamic terminal help and completion include contributed command names,
  descriptions, and supported arguments.
- [ ] A generic `/action` command can list and execute available application
  and current-session actions.
- [ ] Command arguments and prompted values are validated through the bound
  action definition.
- [ ] Session-scoped commands receive the current session and effective
  application context when required.
- [ ] Terminal rendering preserves useful action displays, errors, and
  follow-up information.
- [ ] Authentication plugins can contribute login, status, cancellation, and
  logout commands without provider-specific terminal code.

### Non-functional requirements

- [ ] Plugin actions remain the single executable source of truth for
  top-level commands, slash commands, and `/action`.
- [ ] Command-name and alias collisions are detected and reported
  deterministically.
- [ ] Invalid, unavailable, or ambiguous commands fail before mutating session,
  credential, or plugin state.
- [ ] Sensitive values are excluded from help, completion, logs, and ordinary
  diagnostics.
- [ ] Existing static terminal commands and top-level contributed commands
  remain compatible during migration.
- [ ] Automated tests prove that each supported command entrypoint invokes the
  same plugin action and validation contract.

## Scope

This task owns the generic application/terminal command contribution surface
and the generic `/action` fallback. Provider-specific command definitions
remain in their owning plugins.

This task supersedes:

- `tasks/20260605-mobile-oauth-login-flows/030-cli-login-commands-via-plugin-actions.md`
- `tasks/20260315-terminal-action-command.md`

## Open requirement questions

1. Should one command descriptor name both the top-level command and slash
   command, or may plugins provide distinct aliases for each frontend?
   - Recommendation: use one action binding with explicit optional frontend
     names so both entrypoints share arguments while allowing idiomatic names.
2. Should `/action` expose every action or only actions represented by current
   UI elements?
   - Recommendation: expose application actions and current-session actions
     that are valid in the active context; do not expose hidden lifecycle-only
     actions by default.

## Supporting facts

- `ApplicationPlugin.get_commands()` and
  `AgentApplication.get_application_commands()` already exist.
- The top-level `crystal-lattice` parser already executes contributed commands
  through `execute_application_action(...)`.
- The interactive terminal still uses a static decorator registry and does
  not consume application-plugin command descriptors.
- No generic `/action` command is currently registered.
- ChatGPT and MCP authentication plugins expose actions but do not currently
  contribute terminal commands.

## Execution plan

Status: Draft

Normalize the existing command descriptor around one plugin/action binding and
optional top-level/slash presentation metadata. Preserve current top-level
command behavior while adding dynamic interactive registration after the
terminal application has loaded its configuration.

Add a generic terminal command adapter that:

1. resolves the contributed command and bound action;
2. parses inline arguments or prompts for missing supported inputs;
3. supplies current-session context when the action requires it;
4. executes through the existing application action path;
5. renders the standard action result without provider-specific logic.

Implement `/action` on the same adapter. Its list/completion behavior should
derive from current application and session action definitions rather than
maintaining a separate catalog.

Use a dummy application plugin as the generic contract consumer, then adopt
the command surface in the existing ChatGPT auth plugin. Claude command
adoption remains in the direct-Claude task so this task does not depend on a
provider that does not yet exist.

### Implementation decisions and open questions

- Decision: command descriptors are frontend bindings, not executable plugin
  hooks.
- Decision: static built-in slash commands and dynamic plugin commands share
  one collision policy and help output.
- Decision: `/action` is a generic fallback and does not replace convenient
  plugin-contributed command names.
- Open: approve the recommended descriptor shape before implementation changes
  public plugin documentation.

### Documentation

- Update application-plugin authoring documentation with top-level and
  interactive command bindings.
- Update terminal user and development documentation for dynamic commands,
  `/action`, prompting, completion, and collision behavior.
- Document that command implementations must remain thin bindings to actions.

### Task checklist

- [ ] Approve the command descriptor and collision policy.
- [ ] Normalize command discovery and validation in the application layer.
- [ ] Preserve and test existing top-level contributed commands.
- [ ] Add interactive plugin command registration, help, and completion.
- [ ] Add generic `/action` listing, prompting, and execution.
- [ ] Add standard terminal action-result rendering.
- [ ] Add dummy-plugin and ChatGPT-auth command adoption.
- [ ] Add unit, application, terminal, and CLI integration tests.
- [ ] Update user and plugin-authoring documentation.

### Requirement verification

- A dummy plugin action produces equivalent results through a top-level
  command, a contributed slash command, and `/action`.
- Invalid and missing arguments produce the same validation outcome through
  each entrypoint.
- Current-session actions receive the expected session context.
- Collision, unknown-action, disabled-action, and secret-redaction tests pass.
- Existing built-in slash commands and `validate-cloud` behavior remain
  functional.

### Additional implementation verification

- Dynamic command reload behavior is explicit when `AgentApplication` is
  reconstructed.
- Command completion does not execute plugin actions or expose sensitive
  defaults.
- A plugin unload or configuration change cannot leave a stale executable
  command binding.