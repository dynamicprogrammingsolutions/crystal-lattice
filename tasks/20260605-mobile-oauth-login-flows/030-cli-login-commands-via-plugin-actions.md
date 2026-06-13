# CLI Login Commands Via Plugin Actions
Add CLI and slash-command entry points that call plugin actions instead of duplicating provider-specific login logic.

## Requirements checklist

- [ ] Confirm the current application-plugin command hook and how terminal frontends consume it.
- [ ] Design CLI commands for login flows so they bind to existing actions rather than introducing a separate execution path.
- [ ] Add or plan commands for Codex first, with a shape reusable for Claude and Copilot later.
- [ ] Keep this work compatible with the login-type selection UX from the framework audit.

Parent Task: `tasks/20260605-mobile-oauth-login-flows/000-main.md`
Depends On: `tasks/20260605-mobile-oauth-login-flows/020-auth-ux-and-framework-capability-audit.md`

## Parallelization note

This task is intentionally parallel to the mobile app-link work. The CLI surface should call the same application actions, even if the underlying provider capabilities differ.

## Current repo references

- `core/python/agent_app/app_plugins.py`
  - `get_commands(...)` exists specifically for CLI/slash command bindings to existing actions.
- `core/python/agent_app/application_future.py`
  - Application layer command/action collection and dispatch.
- `application/python/agent_terminal_app`
  - Terminal frontend and slash-command surface.
- `plugins/cloud-agent-app/src/cloud_agent_app/cloud_agent_app_plugin.py`
  - Example plugin that already contributes commands in addition to actions.

## Design intent

- The plugin remains the source of truth for login operations.
- CLI commands should be thin wrappers over action execution.
- The command surface should not fork behavior away from the mobile/frontend action-driven path.

## Candidate command shapes

- A generic auth command that starts login for a chosen provider.
- Provider-specific convenience commands if the frontend needs them.
- Optional flags or interactive selection for login type, depending on the outcome of the UX audit.

## Expected output

- Concrete command definitions or a detailed implementation-ready plan.
- Clear mapping from each CLI command to an existing action id and parameter set.
- Notes on how terminal UX should handle browser-login, device-code, and status-check flows.