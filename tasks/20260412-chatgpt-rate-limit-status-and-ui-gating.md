# ChatGPT Rate-Limit Status And UI Gating

Refine the ChatGPT auth proof of concept so ChatGPT login/session actions only appear for relevant OpenAI Responses sessions, and add a new session-scoped account status action whose primary value is Codex-style usage limit visibility (5-hour, weekly, monthly, credits) rather than generic session details.

## Requirements checklist

- [ ] Show ChatGPT login/session actions only for sessions that use the `openai_responses` provider.
- [ ] Further restrict those ChatGPT login/session actions to sessions whose effective `auth_mode` is `auto` or `chatgpt`.
- [ ] Hide those ChatGPT login/session actions for `auth_mode: "api"` and for non-`openai_responses` sessions.
- [ ] Add a new session-scoped application action in the ChatGPT auth app plugin for account status.
- [ ] Keep the new status action focused on account/auth and usage limits, not generic session information.
- [ ] Prioritize Codex-style usage limit details in the new status action:
  - [ ] 5-hour remaining percentage and reset time when available
  - [ ] weekly remaining percentage and reset time when available
  - [ ] monthly remaining percentage and reset time when available
  - [ ] credits balance / unlimited status when available
- [ ] Include account/auth details in the new status action when available:
  - [ ] requested auth mode
  - [ ] effective auth mode
  - [ ] login state
  - [ ] account email
  - [ ] account id
  - [ ] plan type
  - [ ] effective ChatGPT/Codex endpoint when useful
- [ ] Exclude generic session details from the new status action:
  - [ ] model
  - [ ] working directory
  - [ ] session id
  - [ ] agent id
  - [ ] sandbox / approval / other unrelated runtime state
- [ ] Do not use "last assistant message usage" as the primary status source for this action.
- [ ] Investigate whether the ChatGPT Codex endpoint used by `openai_responses` exposes Codex-style rate-limit metadata that can be captured in this repo.
- [ ] If rate-limit metadata is available, capture and persist a latest snapshot suitable for the new status action.
- [ ] If rate-limit metadata is not directly available in the current SDK path, document and implement the smallest viable lower-level or alternate fetch path needed to obtain it.
- [ ] Add tests for:
  - [ ] UI gating by provider + auth mode
  - [ ] account status action payloads
  - [ ] rate-limit snapshot parsing/capture, if implemented
  - [ ] session-scoped endpoint behavior

## Background

The current `chatgpt_auth` application plugin exposes ChatGPT login-related `session_action` UI elements unconditionally from:

- `plugins/chatgpt-auth-app/src/chatgpt_auth_app/__init__.py`

That is broader than desired. The repo already supports session-scoped application UI queries that pass the session's effective config, provider tags, and models into application plugins via:

- `application/python/agent_terminal_app/server.py`
- `application/python/agent_terminal_app/terminal_app.py`
- `packages/frontend-sdk/src/backend/restBackend.ts`

This means UI gating should likely be implemented in the application plugin itself using:

- effective session config
- provider tags such as `provider:openai_responses`
- effective/requested `auth_mode`

## Desired UX

For sessions that are not relevant to ChatGPT-backed OpenAI Responses:

- no ChatGPT login/session actions should be shown

For sessions using `openai_responses` with `auth_mode: "auto"` or `"chatgpt"`:

- existing ChatGPT login actions remain visible
- a new account status action is visible

The new status action should be much closer to "account / limits status" than a full Codex `/status` clone.

It should emphasize:

- whether ChatGPT auth is active
- which account/plan is active
- what current usage limits remain

It should not emphasize:

- model/runtime/session mechanics unrelated to account state

## Codex reference

Codex `/status` includes dedicated rate-limit and credits information, not merely per-request token usage. Relevant references:

- `../codex/codex-rs/tui/src/status/card.rs`
- `../codex/codex-rs/tui/src/status/rate_limits.rs`
- `../codex/codex-rs/tui/src/status/snapshots/codex_tui__status__tests__status_snapshot_includes_credits_and_limits.snap`

Codex gets this information from dedicated rate-limit metadata:

- HTTP headers parsed in `../codex/codex-rs/codex-api/src/rate_limits.rs`
- `codex.rate_limits` events parsed in `../codex/codex-rs/codex-api/src/rate_limits.rs`

Representative fields include:

- `x-codex-primary-used-percent`
- `x-codex-primary-window-minutes`
- `x-codex-primary-reset-at`
- `x-codex-secondary-used-percent`
- `x-codex-secondary-window-minutes`
- `x-codex-secondary-reset-at`
- `x-codex-credits-has-credits`
- `x-codex-credits-unlimited`
- `x-codex-credits-balance`

Codex `/status` then renders rows such as:

- `5h limit`
- `Weekly limit`
- `Monthly limit`
- `Credits`

## Current repo gap

The current OpenAI Responses stack in this repo already handles:

- ChatGPT device login
- saved ChatGPT credentials
- ChatGPT auth refresh and `401` recovery

But it does not currently maintain a Codex-style rate-limit snapshot.

Relevant files:

- `plugins/chatgpt-auth-app/src/chatgpt_auth_app/__init__.py`
- `plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py`
- `plugins/openai_responses/src/openai_responses_plugins/openai_responses_chatgpt_auth_feature.py`
- `plugins/openai_responses/src/openai_responses_plugins/openai_responses_runtime.py`

The current provider extracts response-body data and usage metadata, but not Codex-style rate-limit snapshots.

## Technical investigation target

Determine whether the ChatGPT endpoint currently used by this repo:

- `https://chatgpt.com/backend-api/codex`

returns any of the following during real OpenAI Responses requests:

1. Codex-style `x-codex-*` rate-limit headers on HTTP responses
2. a response-body payload that contains equivalent rate-limit snapshot data
3. SSE / streaming events carrying equivalent `codex.rate_limits` data

If yes, add capture/parsing and make the latest snapshot available to the new account status action.

If no, identify the smallest viable fallback:

1. a lower-level HTTP path that preserves raw headers while keeping current behavior
2. a provider-side sidecar fetch to a dedicated usage/limits endpoint
3. another minimal backend-owned mechanism that can obtain the same data

## Scope guidance

Preferred priority:

1. Correct UI gating
2. New session-scoped account status action
3. Real usage-limit snapshot capture
4. Rendering of credits and limit windows

Avoid broadening scope into:

- a general session status panel
- frontend protocol changes unless strictly necessary
- event-stream UX for live limit refresh in this task

## Suggested output shape for the new status action

The status action should return a normal action `display` payload.

The content should focus on:

- auth state
- account identity
- plan
- usage limits
- credits

If rate-limit data is unavailable, the status action should say so clearly rather than inventing values.

## Test expectations

At minimum, add coverage for:

1. Session-scoped application UI gating
   - `openai_responses` + `auth_mode: auto` -> visible
   - `openai_responses` + `auth_mode: chatgpt` -> visible
   - `openai_responses` + `auth_mode: api` -> hidden
   - non-`openai_responses` provider -> hidden

2. New account status action
   - account/auth fields present when credentials exist
   - limit rows present when a rate-limit snapshot exists
   - clear "not available" messaging when no snapshot exists

3. Rate-limit snapshot capture/parsing
   - parse Codex-style header families if that path is implemented
   - preserve credits / plan information when snapshots are partial, if persistence is implemented

4. Endpoint behavior
   - `/sessions/{id}/application/ui-schema`
   - action execution through `/actions`

## Open design question to settle during implementation

Where should the latest rate-limit snapshot live?

Likely options:

1. application-plugin state only
   - simplest, but process-local and ephemeral
2. credential sidecar file under `CONFIG_DIR`
   - durable and naturally account-scoped
3. session metadata
   - less appropriate because the data is account-scoped, not session-scoped

The most likely fit is a small durable sidecar file under `CONFIG_DIR` so the status action can report the latest known limits even across restarts.