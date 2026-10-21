# Mobile OAuth Login Flows
Build a mobile-friendly login selection and OAuth handoff flow for Codex first, then reuse the architecture for Claude and align Copilot with the same action/CLI UX where appropriate.

## Task checklist

- [ ] `tasks/20260605-mobile-oauth-login-flows/010-codex-mobile-redirect-poc.md`
  - FIRST SUBTASK: prove whether OpenAI/Codex accepts a mobile redirect URI such as `myapp://...`.
- [ ] `tasks/20260605-mobile-oauth-login-flows/020-auth-ux-and-framework-capability-audit.md`
  - Determines whether the framework already supports the desired chip-style single-confirm selection flow.
- [ ] `tasks/20260605-mobile-oauth-login-flows/030-cli-login-commands-via-plugin-actions.md`
  - PARALLEL WITH `tasks/20260605-mobile-oauth-login-flows/040-frontend-app-link-routing-and-action-resume.md`
  - PARALLEL WITH `tasks/20260605-mobile-oauth-login-flows/050-complete-codex-browser-login-flow.md`
- [ ] `tasks/20260605-mobile-oauth-login-flows/040-frontend-app-link-routing-and-action-resume.md`
  - DEPENDS ON `tasks/20260605-mobile-oauth-login-flows/010-codex-mobile-redirect-poc.md`
- [ ] `tasks/20260605-mobile-oauth-login-flows/050-complete-codex-browser-login-flow.md`
  - DEPENDS ON `tasks/20260605-mobile-oauth-login-flows/010-codex-mobile-redirect-poc.md`
  - DEPENDS ON `tasks/20260605-mobile-oauth-login-flows/020-auth-ux-and-framework-capability-audit.md`
  - DEPENDS ON `tasks/20260605-mobile-oauth-login-flows/040-frontend-app-link-routing-and-action-resume.md`
- [ ] `tasks/20260605-mobile-oauth-login-flows/060-claude-browser-login-adaptation.md`
  - DEPENDS ON `tasks/20260605-mobile-oauth-login-flows/050-complete-codex-browser-login-flow.md`
  - EXTERNAL DEPENDENCY: Claude provider implementation work must exist before this adaptation starts.
- [ ] `tasks/20260605-mobile-oauth-login-flows/070-copilot-shared-ux-and-cli-alignment.md`
  - DEPENDS ON `tasks/20260605-mobile-oauth-login-flows/020-auth-ux-and-framework-capability-audit.md`
  - DEPENDS ON `tasks/20260605-mobile-oauth-login-flows/030-cli-login-commands-via-plugin-actions.md`
  - EXTERNAL DEPENDENCY: Copilot provider implementation work must exist before this alignment starts.
- [ ] `tasks/20260605-mobile-oauth-login-flows/080-polish-tests-and-docs.md`
  - DEPENDS ON `tasks/20260605-mobile-oauth-login-flows/050-complete-codex-browser-login-flow.md`
  - DEPENDS ON `tasks/20260605-mobile-oauth-login-flows/060-claude-browser-login-adaptation.md`
  - DEPENDS ON `tasks/20260605-mobile-oauth-login-flows/070-copilot-shared-ux-and-cli-alignment.md`

## Approved supersession

This Codex-first plan predates delivered generic action deep links, action
dialog selection, current ChatGPT device-code actions, plugin-contributed
top-level commands, and the decision to add a real direct Claude provider.

Its remaining product scope is superseded by:

- `tasks/20260824-plugin-driven-cli-and-interactive-terminal-commands.md`
- `tasks/20260824-direct-claude-provider-and-plugin-login/000-main.md`
- `tasks/20261016-provider-login-experience/000-main.md`
- `tasks/20261016-provider-login-experience/010-codex-browser-login-and-method-selection.md`
- `tasks/20261016-provider-login-experience/020-provider-login-notifications-and-anthropic-adoption.md`
- `tasks/20261016-provider-login-experience/030-provider-auth-global-attention.md`

Provider-specific evidence and useful supporting facts remain historical input.
Copilot work remains deferred until a concrete provider implementation is
planned.

## Reference implementation

Checked-out working reference repo: `../pi`

Treat the `pi` code as the source of truth for provider behavior. Use docs and tests there as supporting material, but trust the implementation first.

Relevant `pi` references already inspected:

- OpenAI Codex auth flow:
  - `../pi/packages/ai/src/utils/oauth/openai-codex.ts`
  - Browser OAuth with PKCE and localhost callback server.
  - Device-code login that eventually exchanges `authorization_code` + `code_verifier` at `/oauth/token`.
- OpenAI Codex request behavior:
  - `../pi/packages/ai/src/providers/openai-codex-responses.ts`
  - Sends bearer token plus `chatgpt-account-id` to `https://chatgpt.com/backend-api/codex/responses`.
- Shared OAuth storage in `pi`:
  - `../pi/packages/coding-agent/src/core/auth-storage.ts`
- `pi` interactive login UX:
  - `../pi/packages/coding-agent/src/modes/interactive/interactive-mode.ts`
  - `../pi/packages/coding-agent/src/modes/interactive/components/login-dialog.ts`
- Claude auth reference:
  - `../pi/packages/ai/src/utils/oauth/anthropic.ts`
  - Browser OAuth with PKCE and callback flow similar to Codex.
- Copilot auth reference:
  - `../pi/packages/ai/src/utils/oauth/github-copilot.ts`
  - Device-code flow only, not a redirect-based mobile callback flow.

## Current repo starting points

Current implementation references already inspected:

- Current ChatGPT/OpenAI auth session actions:
  - `plugins/chatgpt-auth-app/src/chatgpt_auth_app/__init__.py`
- Current OpenAI Responses ChatGPT auth feature:
  - `plugins/openai_responses/src/openai_responses_plugins/openai_responses_chatgpt_auth_feature.py`
- Current saved credential parsing and refresh:
  - `plugins/openai_responses/src/openai_responses_plugins/chatgpt_credentials.py`
- Current runtime behavior for ChatGPT-backed requests:
  - `plugins/openai_responses/src/openai_responses_plugins/openai_responses_runtime.py`
- UI element dialog documentation:
  - `plugins/docs/ui-elements.md`
- Application plugin command hook:
  - `core/python/agent_app/app_plugins.py`

## High-level findings

- Codex and Claude can likely share one redirect-based mobile architecture if their OAuth clients allow a mobile redirect URI.
- Copilot should not be forced into the same redirect callback model; its `pi` implementation is device-code based, but it can still share login selection UX and CLI/action plumbing.
- Our current `chatgpt-auth-app` already contains useful pieces for Codex:
  - device-code start and polling
  - authorization-code exchange
  - credential persistence compatible with `openai_responses`
- The main unknown is redirect acceptance for a mobile app URI such as `myapp://...`; that is why the Codex POC is the first subtask.