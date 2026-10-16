# Codex Mobile Redirect POC
Prove whether OpenAI/Codex accepts a mobile redirect URI and whether the app can capture enough information to resume the flow through an action call.

SUPERSEDED BY:
`tasks/20261016-provider-login-experience/010-codex-browser-login-and-method-selection.md`

## Requirements checklist

- [ ] Verify whether the OpenAI/Codex OAuth client accepts a redirect URI such as `myapp://oauth/callback`.
- [ ] Build the smallest viable start-flow proof of concept without committing to the full product UX yet.
- [ ] Record the exact success or failure mode, including any provider-side restrictions on redirect URIs.
- [ ] Capture the minimum redirect payload the frontend would need in order to resume the flow safely.

Parent Task: `tasks/20260605-mobile-oauth-login-flows/000-main.md`
Depends On: None

## Why this is first

If Codex does not accept a mobile redirect URI for the current OAuth client, the rest of the mobile browser-login plan changes immediately. This task is the main feasibility gate.

## Known working reference in `pi`

Use these files as the source of truth for the current working CLI/browser implementation:

- `../pi/packages/ai/src/utils/oauth/openai-codex.ts`
  - Browser OAuth + PKCE setup.
  - Local callback server on `http://localhost:1455/auth/callback`.
  - Manual pasted redirect fallback.
  - Device-code flow that ultimately exchanges `authorization_code` + `code_verifier`.
- `../pi/packages/ai/src/providers/openai-codex-responses.ts`
  - Codex backend URL normalization and request headers.
  - JWT `chatgpt_account_id` extraction from the access token.
- `../pi/packages/coding-agent/src/modes/interactive/interactive-mode.ts`
  - Login dialog orchestration and manual code race with callback server.

Important high-level flow discovered from `pi`:

1. Construct PKCE challenge and `state`.
2. Open `https://auth.openai.com/oauth/authorize`.
3. Receive redirect carrying `code` and `state`.
4. Exchange `code` + `code_verifier` at `https://auth.openai.com/oauth/token`.
5. Persist access token, refresh token, and account metadata.
6. Send bearer token plus `chatgpt-account-id` to the ChatGPT/Codex backend.

## Current repo starting points

- `plugins/chatgpt-auth-app/src/chatgpt_auth_app/__init__.py`
  - Already supports Codex device auth defaults and auth-code exchange in the polled device-code path.
- `plugins/openai_responses/src/openai_responses_plugins/chatgpt_credentials.py`
  - Already knows how to store and refresh the saved ChatGPT credentials.
- `plugins/openai_responses/src/openai_responses_plugins/openai_responses_runtime.py`
  - Already consumes `chatgpt_access_token`, `chatgpt_account_id`, and `chatgpt_base_url`.

## POC scope

Keep this intentionally narrow:

- It is acceptable to add temporary or thin plumbing if it helps answer the redirect-acceptance question.
- It is not necessary to finish the whole frontend UX here.
- The output of this task should be a factual answer and a concrete next-step decision.

## Suggested experiments

- Try constructing a browser-login start action for Codex that uses a test redirect such as `myapp://oauth/callback`.
- If the provider requires an HTTPS redirect, test a universal-link style callback instead.
- Check whether the provider rejects the redirect immediately at authorize time, only at token exchange time, or whether it succeeds.
- If successful, record whether the redirect includes only `code` and `state`, or any provider-specific extras that matter later.

## Success criteria

- There is a written conclusion on whether app-link redirect handling is viable for Codex with the current client.
- The result includes the exact redirect format and the next implementation path.
- If the result is negative, the task records the blocking constraint clearly enough to redirect the project toward device-code or backend-owned redirect alternatives.