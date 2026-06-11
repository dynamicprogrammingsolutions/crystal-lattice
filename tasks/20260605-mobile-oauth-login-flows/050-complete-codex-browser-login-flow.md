# Complete Codex Browser Login Flow
Turn the Codex proof of concept into a production-ready browser-login path that works end to end with login-type selection, redirect completion, and existing credential persistence.

## Requirements checklist

- [ ] Add the full Codex browser-login action flow, including start and completion steps.
- [ ] Reuse existing saved-credential and refresh behavior where possible.
- [ ] Integrate login-type selection from settings and from action-time selection when no preference is set.
- [ ] Keep device-code login supported as an alternative path.
- [ ] Ensure the resulting saved credentials work with `openai_responses` without requiring a separate credential format.

Parent Task: `tasks/20260605-mobile-oauth-login-flows/000-main.md`
Depends On: `tasks/20260605-mobile-oauth-login-flows/010-codex-mobile-redirect-poc.md`, `tasks/20260605-mobile-oauth-login-flows/020-auth-ux-and-framework-capability-audit.md`, `tasks/20260605-mobile-oauth-login-flows/040-frontend-app-link-routing-and-action-resume.md`

## Known starting points in this repo

- `plugins/chatgpt-auth-app/src/chatgpt_auth_app/__init__.py`
  - Existing device-code flow.
  - Existing auth-code exchange helper.
  - Existing status, cancel, logout actions.
- `plugins/openai_responses/src/openai_responses_plugins/chatgpt_credentials.py`
  - Existing token parsing and refresh behavior.
- `plugins/openai_responses/src/openai_responses_plugins/openai_responses_chatgpt_auth_feature.py`
  - Existing `auth_mode: api | chatgpt | auto` handling.
- `plugins/openai_responses/src/openai_responses_plugins/openai_responses_runtime.py`
  - Existing base URL and header behavior for ChatGPT-backed requests.

## Working-reference flow in `pi`

Source of truth for the target reference:

- `../pi/packages/ai/src/utils/oauth/openai-codex.ts`
- `../pi/packages/ai/src/providers/openai-codex-responses.ts`
- `../pi/packages/coding-agent/src/core/auth-storage.ts`

Important behavior to preserve conceptually:

- PKCE browser login yields access token, refresh token, and account id.
- Provider request path can derive or use `chatgpt_account_id`.
- Refresh path continues through `https://auth.openai.com/oauth/token`.

## Expected output

- Full Codex browser-login feature wired into our app/plugin architecture.
- Coexistence of browser-login and device-code flows under one clean user-facing selection model.
- Clear documentation of any remaining provider-specific limitations.