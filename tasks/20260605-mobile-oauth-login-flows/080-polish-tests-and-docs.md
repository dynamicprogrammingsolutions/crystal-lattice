# Polish Tests And Docs
Finish the work with tests, docs, and cleanup once the Codex, Claude, and Copilot tasks have landed.

## Requirements checklist

- [ ] Add regression coverage for the selected auth flows and UI/action contracts.
- [ ] Document the final user-facing behavior for mobile, frontend, and CLI login flows.
- [ ] Document provider differences clearly, especially redirect-based versus device-code behavior.
- [ ] Record any residual risks, unsupported cases, or provider restrictions discovered during implementation.

Parent Task: `tasks/20260605-mobile-oauth-login-flows/000-main.md`
Depends On: `tasks/20260605-mobile-oauth-login-flows/050-complete-codex-browser-login-flow.md`, `tasks/20260605-mobile-oauth-login-flows/060-claude-browser-login-adaptation.md`, `tasks/20260605-mobile-oauth-login-flows/070-copilot-shared-ux-and-cli-alignment.md`

## Test and documentation starting points

- `plugins/chatgpt-auth-app/tests`
- `plugins/openai_responses/tests`
- `application/python/tests`
- `plugins/docs/ui-elements.md`
- `plugins/docs/application-plugins.md`
- `plugins/docs/actions.md`
- Any mobile-app documentation or README files that end up owning the deep-link flow

## Important documentation outcomes

- Codex and Claude should be documented as redirect-based browser-login providers if the mobile redirect path is supported.
- Copilot should be documented as a device-code provider even if it shares the same visible auth framework.
- The final docs should point maintainers back to the `pi` code paths used as reference during design, while keeping this repo's implementation as the authority for behavior here.