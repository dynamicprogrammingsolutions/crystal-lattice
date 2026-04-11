# ChatGPT Token Refresh And 401 Recovery

Add the next auth-hardening step after the ChatGPT device-login proof of concept: use the saved `refresh_token` to renew ChatGPT credentials, persist rotated tokens, and recover cleanly from ChatGPT endpoint `401` responses during OpenAI Responses requests.

## Requirements checklist

- [ ] Add managed ChatGPT token refresh using the saved `refresh_token`.
- [ ] Persist refreshed credentials atomically to the same credential file used by the login plugin and provider auth feature.
- [ ] Add provider-side `401` recovery for ChatGPT-backed OpenAI Responses requests:
  - one guarded refresh attempt
  - one retry after successful refresh
  - clear permanent failure messaging when refresh cannot recover
- [ ] Keep `api`, `chatgpt`, and `auto` mode semantics intact.
- [ ] Avoid regressing the existing device-code login flow, saved-login integration test, and API-key mode.
- [ ] Add focused unit and mocked integration tests for refresh success, refresh failure, and `401` retry behavior.

## Background

The current POC successfully:

- logs in via ChatGPT device code
- saves `access_token`, `refresh_token`, `id_token`, account metadata, and expiry
- uses the saved `access_token` for ChatGPT-backed OpenAI Responses requests

But the current runtime path does **not** use the saved `refresh_token`.

Current limitation in this repo:

- `plugins/chatgpt-auth-app/src/chatgpt_auth_app/__init__.py`
  - saves `refresh_token`
- `plugins/openai_responses/src/openai_responses_plugins/openai_responses_chatgpt_auth_feature.py`
  - only loads saved credentials and checks local validity from `access_token` + optional `expires_at`
- `plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py`
  - only sends the current access token
  - does not refresh on `401`

Observed failure mode:

```text
RuntimeError: OpenAI Responses stream failed: Error code: 401 - {'detail': 'Could not parse your authentication token. Please try signing in again.'}
```

That is most likely caused by an expired or revoked ChatGPT `access_token` that still exists on disk, with no refresh-and-retry path yet.

## Relevant current files

- `plugins/chatgpt-auth-app/src/chatgpt_auth_app/__init__.py`
- `plugins/openai_responses/src/openai_responses_plugins/openai_responses_chatgpt_auth_feature.py`
- `plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py`
- `plugins/openai_responses/tests/test_openai_responses_chatgpt_auth_feature_unit.py`
- `plugins/openai_responses/tests/test_openai_responses_provider_unit.py`
- `plugins/openai_responses/tests/test_openai_responses_chatgpt_auth_manual_integration.py`
- `plugins/chatgpt-auth-app/tests/test_chatgpt_auth_app_plugin_unit.py`

## Codex reference behavior

Codex already solves this class of problem in its managed ChatGPT auth stack.

Useful references:

- `../codex/codex-rs/core/src/auth.rs`
- `../codex/codex-rs/backend-client/src/client.rs`

Key behaviors to mirror conceptually:

1. Managed refresh-token exchange:
   - `POST https://auth.openai.com/oauth/token`
   - JSON body includes:
     - `client_id = app_EMoamEEZ73f0CkXaXp7hrann`
     - `grant_type = refresh_token`
     - `refresh_token = ...`

2. Persist rotated tokens:
   - Codex persists refreshed tokens and reloads auth state after refresh.

3. `401` recovery state machine:
   - on unauthorized:
     - reload auth from storage if safe
     - refresh from authority
     - retry once
   - if refresh still fails, bubble a clear auth error

4. Distinguish permanent refresh failure from transient failure:
   - revoked / expired / reused refresh tokens are treated as “sign in again”

Important references:

- refresh request logic: `../codex/codex-rs/core/src/auth.rs`
- unauthorized recovery state machine: `../codex/codex-rs/core/src/auth.rs`

## Desired behavior in this repo

### Managed refresh flow

When ChatGPT credentials are stored locally and include a `refresh_token`:

- runtime can refresh them against `https://auth.openai.com/oauth/token`
- refreshed credentials are written back atomically
- subsequent requests use the new access token

### `401` recovery flow

For ChatGPT-backed OpenAI Responses requests:

1. Send request with saved access token.
2. If the ChatGPT endpoint returns `401`:
   - reload credentials from disk
   - if credentials changed, retry once with reloaded token
   - otherwise attempt refresh using `refresh_token`
   - persist refreshed credentials
   - retry once
3. If recovery fails:
   - for permanent refresh failure, raise a clear “Please sign in again” style error
   - for transient refresh failure, raise an explicit refresh failure error

### Mode semantics

- `auth_mode = "api"`:
  - unchanged
- `auth_mode = "chatgpt"`:
  - use ChatGPT token refresh / retry behavior
  - if no valid refresh path exists, fail clearly
- `auth_mode = "auto"`:
  - continue preferring ChatGPT when saved credentials exist
  - if ChatGPT auth becomes unrecoverable, decide whether to:
    - fail clearly, or
    - fall back to API only when an API key is actually configured

This fallback decision should be treated carefully because silent fallback may hide that the user is no longer actually using ChatGPT auth.

## Implementation notes

### 1. Shared credential helper

Consider extracting or reusing small helpers so the login plugin and provider-side refresh path agree on:

- credential file location
- atomic write behavior
- token normalization
- expiry parsing
- account metadata extraction from refreshed tokens

### 2. Refresh request shape

Expected refresh request should likely match Codex:

```json
{
  "client_id": "app_EMoamEEZ73f0CkXaXp7hrann",
  "grant_type": "refresh_token",
  "refresh_token": "..."
}
```

Target endpoint:

- `https://auth.openai.com/oauth/token`

The response may rotate:

- `access_token`
- `refresh_token`
- possibly `id_token`

The refreshed credential file should preserve useful metadata fields such as:

- `account_id`
- `account_email`
- `plan_type`
- `obtained_at`
- `expires_at`

### 3. Provider-side placement

The most natural implementation seam is probably:

- keep file-writing ownership in a helper associated with ChatGPT auth credentials
- trigger refresh from the OpenAI Responses provider when a ChatGPT-backed request fails with `401`

This likely belongs in:

- `plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py`

The feature plugin can stay focused on:

- selecting auth mode
- loading current credential state
- injecting base URL / token / account id into runtime config

### 4. Error messaging

Good error outcomes:

- refresh token revoked/expired:
  - “Saved ChatGPT login expired or was revoked. Please sign in again.”
- no refresh token present:
  - “Saved ChatGPT login cannot be refreshed. Please sign in again.”
- refresh endpoint/network failure:
  - “Failed to refresh ChatGPT credentials: ...”

### 5. Streaming path matters most

The most important path is:

- `stream_api(...)`

Because ChatGPT mode is intentionally streaming-only in the current POC.

Non-streaming ChatGPT mode should remain explicitly unsupported.

## Proposed implementation plan

1. Add a credential-refresh helper that:
   - loads current credentials
   - calls the ChatGPT refresh endpoint
   - normalizes and atomically persists refreshed credentials

2. Add guarded credential reload + refresh helpers in the OpenAI Responses provider.
   - reload from disk before refreshing so another process/test run can win the race safely
   - only refresh when still in ChatGPT-backed mode

3. Add `401` recovery to the streaming ChatGPT request path.
   - detect unauthorized response
   - retry once after reload/refresh

4. Optionally add the same guarded recovery to ChatGPT model discovery if useful.
   - lower priority than request streaming

5. Improve user-facing errors for unrecoverable auth failures.

6. Add tests.

## Test plan

### Unit tests

- refresh helper returns normalized credential payload on success
- refresh helper writes rotated access and refresh tokens atomically
- refresh helper preserves/updates account metadata
- revoked/expired refresh token maps to a clear permanent error
- missing refresh token maps to a clear sign-in-again error

### Provider tests

- streaming ChatGPT request retries once after `401` and succeeds with refreshed token
- streaming ChatGPT request reloads changed credentials from disk before attempting authority refresh
- streaming ChatGPT request surfaces clear error when refresh fails permanently
- `api` mode is unchanged
- non-streaming ChatGPT mode still raises the explicit unsupported error

### Manual integration

Optional follow-up manual test:

1. log in via device code
2. force token refresh path, either by:
   - using an older/invalid saved access token while keeping a valid refresh token, or
   - waiting for real expiry if practical
3. verify the next real ChatGPT-backed Responses request refreshes successfully and updates the credential file

## Risks / decisions

- We need to confirm the exact refresh response shape returned by the real `auth.openai.com/oauth/token` refresh flow in this environment.
- `auto` mode fallback behavior after unrecoverable ChatGPT refresh failure should be chosen deliberately.
- Concurrent refresh attempts from multiple processes may need a simple file-locking or guarded-reload strategy if collisions become common.

## Completion notes placeholder

Add implementation outcomes, tests run, and any discovered refresh-endpoint quirks here when this task is executed.