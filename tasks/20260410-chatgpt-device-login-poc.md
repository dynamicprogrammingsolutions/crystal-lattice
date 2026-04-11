# ChatGPT Device Login POC Via Plugins

Create a minimum proof-of-concept ChatGPT login flow for cross-device use, using application plugins for login management, generic action endpoints for control, and a provider-side plugin hook so OpenAI Responses can use saved ChatGPT credentials instead of only API keys.

## Requirements checklist

- [x] Implement an extremely minimal cross-device login UX based on device-code style auth:
  - implemented via `chatgpt_auth` application plugin with backend-side polling and manual status/cancel actions
  - `login_start` returns a verification URL, user code, and login id.
  - backend/plugin starts background polling immediately after `login_start`.
  - user can manually run `check_status`.
  - user can manually run `cancel_login`.
- [x] Implement the login control flow as plugins, using application plugin actions and UI schema elements discoverable by existing frontend action plumbing.
- [x] Support use from the existing frontend with only minimal URL/code display and manual `Check status` / `Cancel` actions; no event-driven UX is required for the proof of concept.
- [x] Persist credentials under a path rooted in `CONFIG_DIR`, not a hardcoded path.
- [x] Expose config-resolution environment variables such as `CONFIG_DIR` to plugin code in a first-class way, so plugins can compute paths from the same resolved environment used by config placeholder resolution.
- [x] Make the saved credentials accessible to runtime provider logic via a feature or extension plugin.
- [x] Add an OpenAI Responses auth integration that can switch between `api`, `chatgpt`, and `auto` modes, including endpoint/base-url selection and UI/config-driven switching.
- [x] Add a UI action that shows the current logged-in status in a user-visible way.
- [x] Cover the proof of concept with focused tests across config/env plumbing, application actions, persistence, cancellation, and provider-side credential usage.
- [x] Document the proof-of-concept plugin authoring approach under the canonical docs in `plugins/docs`.

## Goal and non-goal

### Goal

Provide the smallest working login system for the current architecture:

- mobile frontend may be connected over direct HTTP or the Elixir bridge
- frontend only needs to display a URL/code and expose `Check status` / `Cancel`
- backend plugin owns long-running polling and credential persistence
- provider-side runtime can consume saved auth and use ChatGPT-hosted access for OpenAI Responses

### Non-goal

This proof of concept is not trying to ship the final auth UX. It intentionally avoids:

- frontend-mediated OAuth callback handling
- automatic event-driven status UX
- full account/rate-limit protocol parity with Codex
- multi-account / workspace selection UX
- generalized auth support across every provider

## Why device-code first

The backend is often not on the same device where the browser opens. A localhost callback flow like Codex's managed browser login is not a reliable minimum in this architecture when the phone opens the browser and the backend is a laptop/server behind bridge/direct routing.

For this repo's first working version, device-code style login is the correct minimum because:

- the frontend only needs to show a URL/code
- the backend can poll in the background and save credentials when authorization completes
- persistence does not depend on the frontend staying open or polling at the right moment
- cancellation is straightforward: stop the background poller and mark the attempt canceled

Codex uses a similar headless/device-code fallback for non-local browser situations:

- `codex-rs/tui/src/onboarding/auth/headless_chatgpt_login.rs`

Relevant Codex references:

- `codex-rs/app-server/README.md:1032-1115`
- `codex-rs/app-server/src/codex_message_processor.rs:955-1077`
- `codex-rs/tui/src/onboarding/auth/headless_chatgpt_login.rs:1-244`

## Existing architecture relevant to this task

### Application plugin actions already fit auth-control flows

Application plugins are the right layer for this work because they are app-global, can write files, can publish events, and are not tied to a single session.

Key references:

- Protocol and capabilities:
  - `core/python/agent_app/app_plugins.py`
  - `plugins/docs/application-plugins.md`
- Generic action execution:
  - `core/python/agent_app/application_future.py:1547-1690`
- HTTP exposure of actions and UI schema:
  - `application/python/agent_terminal_app/server.py:2799-2915`
- Existing application-plugin example:
  - `plugins/session-actions-app/src/session_actions_app/__init__.py:76-170`

This gives us a ready path for:

- `login_start`
- `check_status`
- `cancel_login`
- `logout`
- a visible status action

### Session actions are session-scoped today

The user asked for application plugins and "session actions" even though auth is not session-scoped. Current runtime semantics matter here:

- application plugin actions are not session-bound
- core/provider-extension/feature actions executed through `execute_session_action(...)` require `session_id`

Reference:

- `core/python/agent_app/application_future.py:1581-1667`

Because of that, the proof of concept should treat auth-control actions as application plugin actions first. If we want them to also show up in session-scoped UI surfaces, that should be done by returning `ui_type: "session_action"` or similar from the application plugin UI schema, not by forcing the auth logic into core session-action execution.

Docs for current action and UI model:

- `plugins/docs/actions.md`
- `plugins/docs/ui-elements.md:477-556`

### Config placeholder resolution already computes `CONFIG_DIR`, but plugins do not get a dedicated resolved-env contract

Config resolution already derives and uses:

- `CONFIG_DIR`
- `WORKING_DIR`
- `BUILTIN_PLUGINS`

References:

- `core/python/agent_app/config.py:25-51`
- `core/python/agent_app/application_future.py:125-133`

Current issue:

- placeholders can use `${env:CONFIG_DIR}`
- plugin code does not currently receive a first-class "resolved env" mapping from the application
- many plugins therefore fall back to hardcoded paths or direct `os.environ`

For this auth POC, a first-class plugin-visible resolved env contract is needed so credential paths can be derived from the same `CONFIG_DIR` anchor used by config resolution.

### OpenAI Responses currently assumes API-key style auth

The OpenAI Responses provider currently resolves:

- `api_key` from config or `OPENAI_API_KEY`
- `base_url` from config or `https://api.openai.com/v1`

References:

- `plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py:126-145`
- `plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py:243-267`

There is already real test coverage for switching between OpenAI and OpenRouter providers at the application level:

- `plugins/openai_responses/tests/test_agent_application_openai_responses_provider_switch.py`

This is a strong base for adding:

- auth mode switching
- base-url / endpoint switching
- provider-side credential injection

## Proof-of-concept functional requirements

### 1. Application plugin: ChatGPT auth app

Add a new application plugin, tentatively:

- `plugins/chatgpt-auth-app`

Responsibilities:

- start a device-code login attempt
- keep track of pending attempt state in process memory
- poll the auth provider in the background
- save credentials atomically when login completes
- expose manual actions for `check_status`, `cancel_login`, `logout`
- contribute minimal UI elements so the frontend can surface these actions

Suggested config shape:

```json
{
  "application": {
    "chatgpt_auth": {
      "credentials_path": "${env:CONFIG_DIR}/auth/chatgpt-auth.json",
      "attempts_path": "${env:CONFIG_DIR}/auth/chatgpt-auth-attempts.json",
      "device_code_poll_interval_seconds": 5,
      "login_timeout_seconds": 900
    }
  }
}
```

Notes:

- `credentials_path` must remain configurable
- plugin should create parent directories as needed
- atomic write is required for credentials
- pending-attempt persistence can be in-memory for the first POC; if a process restart occurs, the attempt may be lost

### 2. Minimal action contract

Suggested action ids:

- `login_start`
- `check_status`
- `cancel_login`
- `logout`

Suggested `login_start` result:

```json
{
  "status": "ok",
  "auth_status": {
    "state": "pending",
    "login_id": "uuid",
    "verification_url": "https://…",
    "user_code": "ABCD-EFGH"
  }
}
```

Suggested `check_status` result:

```json
{
  "status": "ok",
  "auth_status": {
    "state": "pending" | "authenticated" | "canceled" | "failed" | "logged_out",
    "login_id": "uuid-or-null",
    "account_email": "optional",
    "plan_type": "optional",
    "error": "optional"
  }
}
```

Suggested `cancel_login` result:

```json
{
  "status": "ok",
  "auth_status": {
    "state": "canceled",
    "login_id": "uuid"
  }
}
```

Suggested `logout` result:

```json
{
  "status": "ok",
  "auth_status": {
    "state": "logged_out"
  }
}
```

Mode selection should be handled through settings/config UI elements rather than a dedicated action:

- `api`:
  - use API-key auth
  - use the standard API endpoint/base URL
- `chatgpt`:
  - use saved ChatGPT credentials
  - use the ChatGPT endpoint/base URL
- `auto`:
  - use ChatGPT mode when valid saved login exists
  - otherwise fall back to API mode

### 3. Minimal UI schema

The application plugin should expose minimal UI schema elements that the frontend can already consume or render manually:

- a global/action-surface item for `login_start`
- a global/action-surface item for `check_status`
- a global/action-surface item for `cancel_login`
- a global/action-surface item for `logout`
- a user-visible status action that reports current login state
- a settings/config select for auth and endpoint mode with values `api`, `chatgpt`, `auto`

For the very first frontend proof of concept, it is acceptable if the mobile app calls these actions directly from a dedicated connection/auth panel instead of relying entirely on generic action rendering. The backend contract should still be application-plugin based so the frontend remains optional/thin.

### 4. Plugin-visible runtime environment contract

Add a first-class way for plugins to access the same env anchors used during config placeholder resolution.

Minimum requirement:

- application plugins must be able to read `CONFIG_DIR`
- same should be available to core-side plugins used in the auth-consumption path

Implemented shape:

- `AgentApplication` computes the full resolution env used for `${env:...}` placeholders
- it also installs an application-owned runtime overlay into `os.environ`
- the runtime overlay includes keys such as `CONFIG_DIR`, `WORKING_DIR`, `BUILTIN_PLUGINS`, and explicit `env_overrides`
- plugins then read runtime anchors normally via `os.environ[...]`
- the full resolved env is also retained on the application object for inspection APIs

Requirements for this addition:

- do not force plugin authors to guess `CONFIG_DIR` via `os.getcwd()` or hardcoded relative paths
- document the contract in canonical docs under `plugins/docs`
- tests should assert `CONFIG_DIR` reaches plugin runtime through the real process environment
- lifecycle semantics must be explicit because process env is global and multiple `AgentApplication` instances may exist in one Python process

### 5. Provider-side auth consumption for OpenAI Responses

Add a provider-side plugin component, tentatively a feature or extension in:

- `plugins/openai_responses/...`
- or a separate plugin package such as `plugins/chatgpt-auth-openai-responses`

Responsibilities:

- read saved credentials from the configured `CONFIG_DIR`-rooted auth file
- decide whether current provider config should use API-key auth or ChatGPT auth
- inject the appropriate runtime request configuration into OpenAI Responses
- switch endpoint/base URL as needed between normal API mode and ChatGPT-hosted mode

Proof-of-concept requirement:

- do not require changes to every provider
- focus only on OpenAI Responses first
- explicit UI/config-driven switching between `api`, `chatgpt`, and `auto` is enough
- ChatGPT-backed requests should use top-level `instructions` compiled by the system message feature
- ChatGPT-backed requests are streaming-only in this proof of concept

Suggested mode model:

- `auth_mode = "api"`:
  - use `config.api_key` or `OPENAI_API_KEY`
  - use existing API base URL logic
- `auth_mode = "chatgpt"`:
  - load saved ChatGPT credential file
  - use ChatGPT-specific auth header/token handling
  - use ChatGPT-compatible endpoint/base URL selected by config/UI
- `auth_mode = "auto"`:
  - prefer ChatGPT mode when valid saved credentials exist
  - otherwise fall back to API mode

### 6. UI-driven endpoint/auth mode switching

The proof of concept should include a simple UI-driven control path for switching how OpenAI Responses authenticates and which endpoint family it uses.

This should be implemented through plugin-exposed UI/config/actions, not hardcoded frontend logic.

Minimum requirement:

- user can choose between:
  - `api`
  - `chatgpt`
  - `auto`
- effective provider runtime respects that choice

Implementation options to evaluate:

- session override / config key consumed by provider-side feature
- application-level setting stored in a file under `CONFIG_DIR`
- agent/provider config override patch written by an application action

For the POC, prefer the least invasive option that does not mutate unrelated user config unexpectedly.

## Implementation plan

### Phase 1. Runtime env plumbing

1. Add a documented runtime contract exposing config-resolution env values to plugins.
2. Thread this into:
   - application plugin init/action context
   - any core-side feature/extension context needed by auth consumers
3. Add tests proving a plugin can read `CONFIG_DIR`.

Likely files:

- `core/python/agent_app/config.py`
- `core/python/agent_app/application_future.py`
- `core/python/agent_app/app_plugins.py`
- docs under `plugins/docs`

### Phase 2. ChatGPT auth application plugin

1. Add new plugin package `plugins/chatgpt-auth-app`.
2. Implement config schema and state initialization.
3. Implement actions:
   - `login_start`
   - `check_status`
   - `cancel_login`
   - `logout`
4. Implement background polling lifecycle started by `login_start`.
5. Persist credentials atomically under `${env:CONFIG_DIR}/...`.
6. Return simple status payloads only; no event-driven UX required for POC.
7. Expose a visible status action and auth-mode settings UI elements.

Likely tests:

- unit tests for action validation and state transitions
- integration tests through `AgentApplication.execute_application_action(...)`

### Phase 3. Minimal frontend proof of concept

1. Add a minimal auth panel/button set to the connection screen or equivalent frontend surface.
2. Actions needed:
   - `Sign in with ChatGPT`
   - `Check status`
   - `Cancel`
   - `Logout`
3. Display returned:
   - verification URL
   - user code
   - textual status
4. No automatic polling is required for the first pass.

Important: the frontend should not be responsible for saving credentials. `login_start` must start backend polling immediately.

### Phase 4. OpenAI Responses auth-consumption plugin path

1. Add provider-side feature/extension logic that reads the saved credential file.
2. Add a settings/config select that chooses `api`, `chatgpt`, or `auto`.
3. Inject runtime base URL / auth header changes for OpenAI Responses.
4. Route top-level `instructions` through the system message feature rather than a provider config key.
5. Explicitly reject non-streaming ChatGPT-mode requests with a clear error.
6. Add tests that verify:
   - `api` mode still works as today
   - ChatGPT mode uses saved credentials
   - `auto` prefers ChatGPT when logged in and falls back to API otherwise
   - missing/expired credentials fail clearly
   - non-streaming ChatGPT mode fails clearly
   - switching modes changes effective request config

Likely files:

- `plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py`
- new feature/extension file under `plugins/openai_responses/src/openai_responses_plugins/`
- `plugins/feature-system-message/src/feature_system_message/system_message_feature.py`
- provider/unit integration tests in `plugins/openai_responses/tests/`

### Phase 5. Documentation and examples

1. Document:
   - plugin-visible env contract
   - application plugin login action contract
   - provider-side auth consumption pattern
2. Add a minimal example config using `${env:CONFIG_DIR}` for auth path.

Primary doc locations:

- `plugins/docs/application-plugins.md`
- `plugins/docs/actions.md`
- `plugins/docs/ui-elements.md`
- `plugins/docs/provider-plugins.md`

## Technical decisions to preserve during implementation

- `login_start` must begin backend-side background polling immediately.
- `check_status` must be observational only; it should never be required to complete persistence.
- `cancel_login` must stop the background poller for the specific attempt.
- auth files must be rooted in plugin-configured paths derived from `CONFIG_DIR`.
- the frontend should remain optional/thin and not own persistence.
- auth-control actions should live at the application-plugin layer even if their UI appears in a session-like surface.
- auth and endpoint mode selection should be driven by settings/config UI, not a dedicated mutation action.
- `auto` must prefer ChatGPT when valid saved login exists and otherwise fall back to API behavior.
- OpenAI Responses ChatGPT mode should consume top-level `instructions` compiled by the system message feature.
- OpenAI Responses ChatGPT mode is streaming-only in this proof of concept.

## Testing requirements

Minimum test coverage expected:

- config/env:
  - runtime env contract includes `CONFIG_DIR`
  - plugin receives it through `os.environ`
- auth application plugin:
  - `login_start` returns verification info and marks attempt pending
  - background task saves credentials on simulated success
  - `check_status` reports pending/success/failure
  - `cancel_login` halts polling and reports canceled
  - `logout` clears saved credentials
- OpenAI Responses auth integration:
  - `api` mode unchanged
  - ChatGPT mode reads saved auth file
  - `auto` falls back to API when ChatGPT login is unavailable
  - system-message-driven top-level `instructions` are used for ChatGPT mode
  - non-streaming ChatGPT mode fails clearly
  - mode switch updates effective behavior
- server/frontend contract:
  - `/actions` shape remains compatible with the existing generic action executor

Relevant existing test surfaces:

- `core/python/tests/test_application_layer_app_plugins_basic.py`
- `application/python/tests/test_application_actions_endpoints.py`
- `plugins/openai_responses/tests/test_openai_responses_provider_unit.py`
- `plugins/openai_responses/tests/test_agent_application_openai_responses_provider_switch.py`

## Resolved design notes

- The login flow uses the Codex-style ChatGPT deviceauth protocol under `https://auth.openai.com`.
- The working ChatGPT-backed OpenAI Responses base URL is `https://chatgpt.com/backend-api/codex`.
- `auth_mode` is currently a provider/config setting exposed through plugin UI rather than a separate persisted auth-settings file.
- Pending login attempts remain in memory for the POC; saved credentials are durable, but in-flight login attempts do not survive process restart.

## Future directions after the POC

- Frontend-mediated OAuth:
  - mobile app or desktop app receives OAuth callback and hands tokens/code back via a plugin action
- Event-based status UX:
  - publish auth lifecycle events so frontend can update without manual `Check status`
- Better action/UI schema support for global app actions:
  - a dedicated UI type for connection/account actions rather than reusing session-oriented surfaces
- Multi-account/workspace support
- Refresh-token support and silent re-auth
- Rich account surfaces:
  - email
  - plan type
  - usage/rate limits
- Bridge-assisted public callback flow:
  - allow browser auth without device code if the bridge can safely proxy callback completion
- Expand auth-consumption support beyond OpenAI Responses to other providers/plugins that can use ChatGPT-backed credentials

## Canonical docs to consult while implementing

- `plugins/docs/application-plugins.md`
- `plugins/docs/actions.md`
- `plugins/docs/ui-elements.md`
- `plugins/docs/provider-plugins.md`
- `plugins/docs/plugin-packaging-and-loading.md`

## Execution plan

Added during completion planning after user approval.

### Execution approach

Implement this in staged checkpoints so each seam is testable before the real login backend is involved:

1. runtime env overlay plumbing
2. ChatGPT auth application plugin with background device-code polling
3. minimal auth UI schema and visible status action wiring
4. durable credential persistence helpers
5. OpenAI Responses auth consumption with `api` / `chatgpt` / `auto` mode switching
6. docs and semiautomated manual integration coverage

### Implementation plan

1. Add plugin-visible runtime env plumbing in the application layer.
   - Keep `build_config_resolution_env(...)` as the full placeholder-resolution source of truth.
   - Add a smaller runtime overlay env built from application-owned keys plus explicit `env_overrides`.
   - Install that overlay into `os.environ` during `AgentApplication` startup so plugins can use normal env access.
   - Add cleanup and restore behavior for app shutdown and tests.
   - Add focused tests proving `CONFIG_DIR`, `WORKING_DIR`, and explicit `env_overrides` are visible to plugins and match config resolution behavior.

2. Implement a new application plugin for the ChatGPT device login POC.
   - Add a plugin package, likely `plugins/chatgpt-auth-app`.
   - Config includes:
     - `credentials_path`
     - optional `attempts_path`
     - `device_code_poll_interval_seconds`
     - `login_timeout_seconds`
     - optional provider/auth endpoint settings if the device-code backend is configurable
   - `init(...)` resolves paths using the plugin-visible env contract and initializes in-memory pending-attempt state.
   - Implement actions:
     - `login_start`
     - `check_status`
     - `cancel_login`
     - `logout`
   - `login_start` starts the device-code flow, stores the attempt in plugin state, spawns a background poller, and returns `verification_url`, `user_code`, `login_id`.
   - The background poller owns persistence: when authorization completes it writes credentials atomically under `CONFIG_DIR`.
   - `check_status` is read-only: it reports pending/completed/failed/canceled state and reads persisted credentials if present.
   - `cancel_login` stops the poller and marks the attempt canceled.
   - `logout` removes or clears saved credentials and resets the plugin-visible auth state.

3. Surface the minimal UI schema for the existing frontend.
   - Contribute application-plugin UI elements that are intentionally minimal:
     - `Sign in with ChatGPT`
     - `Check login status`
     - `Cancel login`
     - `Log out`
     - a visible status action or status-oriented UI element that makes the current login state clear
   - Keep the action results rich enough for the frontend to display the verification URL and code without needing any special protocol beyond returned fields.
   - Use existing generic action plumbing; no event stream UX is required in the POC.

4. Define the on-disk credential format and persistence helpers.
   - Save under `${env:CONFIG_DIR}/...`, configured by plugin config rather than hardcoded.
   - Use one stable JSON document for the authenticated state, with fields like:
     - `auth_mode`
     - `endpoint_mode`
     - `access_token`
     - `refresh_token` if available
     - `expires_at`
     - `account_email`
     - `account_id`
     - `plan_type`
     - timestamps and metadata for debugging
   - Write atomically and make reads resilient to missing or corrupt files.
   - Keep pending-attempt state in memory for the POC; if needed, optionally persist a light attempts file later.

5. Add a provider-side auth bridge for OpenAI Responses.
   - Add either:
     - a feature plugin that injects ChatGPT-derived auth/runtime config into request config before provider execution, or
     - a provider extension/plugin-local helper if that turns out to be the cleaner seam in this repo
   - The feature or extension should:
     - read the saved auth file
     - activate when mode selection allows ChatGPT auth
     - switch the provider to the ChatGPT-compatible endpoint/base URL
     - inject the correct auth token/header shape
   - Preserve existing API-key behavior when `api` is selected or when `auto` falls back to API.

6. Extend the OpenAI Responses provider for `api`, `chatgpt`, and `auto` modes.
   - Keep the current API-key path as default and backwards compatible.
   - Add explicit config/runtime handling for mode selection using UI/config elements rather than an action.
   - Refactor auth/base-url resolution so it can consume either:
     - API key from config/env
     - ChatGPT credentials injected via the feature/extension
   - Make the provider fail clearly when `chatgpt` mode is selected but no saved credentials are available.
   - In `auto`, prefer ChatGPT when valid saved credentials exist, otherwise fall back to API mode.
   - Add provider UI elements so the user can choose `api`, `chatgpt`, or `auto` in existing settings/config surfaces.

7. Document the POC plugin authoring pattern.
   - Update canonical docs under `plugins/docs`.
   - Cover:
     - application-plugin action flow for background auth
     - real process env contract for runtime anchors such as `CONFIG_DIR`
     - durable file persistence under `CONFIG_DIR`
     - provider-side consumption via feature/extension
     - semantics of `api`, `chatgpt`, and `auto`
     - limits of the current POC UX

8. Add a small manual/demo path for end-to-end verification.
   - Provide a documented local config example and a minimal operator flow:
     - start backend
     - run `login_start`
     - open URL and enter code
     - run `check_status`
     - switch provider mode
     - send a request through OpenAI Responses using saved auth

### Test plan

1. Unit tests for config/env plumbing.
   - `build_config_resolution_env(...)` remains the placeholder-resolution source of truth.
   - app initialization installs the expected app-owned runtime env overlay into `os.environ`.
   - plugin sees `CONFIG_DIR` correctly when config path and `env_overrides` change.
   - incompatible live overlays fail clearly.
   - Misconfigured paths still produce deterministic behavior.

2. Unit tests for the auth application plugin.
   - `login_start` returns the expected shape and creates one pending attempt.
   - Background poller starts exactly once per attempt.
   - `check_status` reports `pending`, `authenticated`, `failed`, `canceled`, `logged_out` correctly.
   - `cancel_login` stops polling and leaves no live pending attempt.
   - `logout` removes persisted credentials.
   - Timeout paths mark an attempt failed or expired cleanly.
   - Corrupt or missing credential files are handled without crashing.

3. Persistence tests.
   - Credential writes are atomic.
   - Parent directories are created under `CONFIG_DIR`.
   - Completed login writes a JSON file that a fresh plugin instance can read.
   - Restart-style tests: after writing credentials, a new `AgentApplication` instance can observe authenticated state via `check_status`.

4. Application action and UI-schema tests.
   - New plugin actions appear in app-layer action enumeration.
   - UI elements are emitted as expected and can be consumed by the current generic action frontend.
   - Status UI/action wiring exposes current login state clearly.
   - The auth mode select exposes `api`, `chatgpt`, and `auto` in both config and settings-oriented UI surfaces.

5. Provider and feature integration tests for OpenAI Responses.
   - `api` mode preserves current behavior.
   - `chatgpt` mode reads persisted credentials and switches base URL/header construction.
   - `auto` uses ChatGPT when credentials are present and falls back to API otherwise.
   - Missing credentials in `chatgpt` mode yields a clear error.
   - Mode switching is reflected in effective provider config and UI schema.
   - A focused test should confirm that no API key is required when valid ChatGPT credentials are present.

6. Mocked integration tests across app plugin and provider.
   - Use a fake device-code auth backend:
     - issue `verification_url` and `user_code`
     - simulate pending responses for some polls
     - then return success with token payload
   - Verify the full flow:
     - `login_start`
     - background completion
     - `check_status`
     - provider request in ChatGPT mode
     - provider request in `auto` mode
   - This should be the main CI-safe integration path.

7. Semiautomated human-in-the-loop integration test.
   - Mark it separately, likely with a pytest marker such as `manual_integration` or `chatgpt_login`.
   - Flow:
     - start the real device-code login
     - print the verification URL and user code
     - wait up to 300 seconds
     - optionally poll every few seconds in test code
     - pass if credentials are saved and `check_status` becomes authenticated
   - Keep it opt-in only, never in normal CI.
   - A second manual test can verify that OpenAI Responses can actually use the saved credentials afterward.

8. Documentation validation.
   - Example config in docs matches the implemented schema.
   - Any example snippets used in docs are covered by a lightweight smoke test where practical.

## Completion Notes

Updated during implementation completion and follow-up cleanup.

- Replaced the initial plugin-only `_resolved_env` plan with a real process-environment overlay owned by `AgentApplication`.
- Added `RuntimeEnvOverlay` in `core/python/agent_app/runtime_env.py` and wired it into `AgentApplication` startup and shutdown.
- Kept `build_config_resolution_env(...)` as the full placeholder-resolution env source of truth, retained the full resolved env on the application object, and installed only application-owned overlay keys into `os.environ`:
  - `CONFIG_DIR`
  - `WORKING_DIR`
  - `BUILTIN_PLUGINS`
  - explicit `env_overrides`
- Added explicit cleanup via `AgentApplication.close()` plus fallback cleanup via `weakref.finalize(...)`.
- Added conflict detection for incompatible live overlays and stale-owner cleanup for abandoned app instances.
- Kept `AgentApplication.get_resolved_env()` for inspection/debugging, while runtime plugin behavior reads `CONFIG_DIR` and related anchors from `os.environ`.
- Implemented `plugins/chatgpt-auth-app` with device-code `login_start`, `check_status`, `cancel_login`, and `logout` actions plus session-action UI entries.
- Implemented background polling with backend-owned credential persistence under `CONFIG_DIR`.
- Added `openai_responses_chatgpt_auth` feature support for `api`, `chatgpt`, and `auto` auth modes plus a settings UI element.
- Updated the OpenAI Responses provider to respect effective auth mode and endpoint selection without requiring API-key auth at init time.
- Aligned ChatGPT auth defaults with Codex backend behavior:
  - issuer `https://auth.openai.com`
  - Codex client id
  - deviceauth endpoints under `auth.openai.com`
- Aligned ChatGPT-mode request defaults with the working live path:
  - base URL `https://chatgpt.com/backend-api/codex`
  - `ChatGPT-Account-Id` header support
  - top-level `instructions`
  - `store: false`
- Added `system_message_as_instructions` to `feature-system-message` so OpenAI Responses can compile the configured system prompt directly into `request.instructions`.
- Removed the standalone OpenAI Responses provider `instructions` config key in favor of the system-message feature path.
- Added an explicit non-streaming error for ChatGPT mode:
  - `chatgpt auth_mode requires streaming requests; use send_request_stream or switch auth_mode to api/auto`
- Added durable manual-test credential storage under `plugins/chatgpt-auth-app/tests/.manual-state/` so follow-up integration tests can reuse a successful login.
- Added CI-safe unit coverage plus opt-in semiautomated manual integration tests for both the real device-code login and a live ChatGPT-backed Responses request using the saved credentials.
- Added a second manual integration test that verifies a real ChatGPT-backed OpenAI Responses request succeeds using the saved login and the ChatGPT-specific endpoint.
- Updated canonical plugin docs to describe the real runtime env contract and the auth-bridge feature pattern.
- Added a generic action-result `display` payload contract for plugin actions, with markdown rendering support in both React Native frontends so login instructions can be shown without auth-specific result keys.
- Updated `application/python/agent_terminal_app/default_config/config.json` so the shipped `openai` provider is minimally wired for this flow:
  - `auth_mode: "auto"`
  - `system_message_as_instructions: true`
  - global `chatgpt-auth-app` plugin enabled
  - empty `application.chatgpt_auth` block so built-in defaults activate
- Updated server-side tests that swap global `AgentApplication` instances so they close the previous app before replacing it.
- Fixed provider-extension session-action test wiring so the injected test extension is also registered in the per-agent runtime cache.

## Follow-up plan

Added after the runtime env contract changed from config injection to real process env installation.

1. Evaluate whether `RuntimeEnvOverlay` should remain a reusable helper or be simplified under an explicit single-live-app-per-process policy.
2. Decide whether server and terminal startup paths should call `AgentApplication.close()` explicitly on shutdown so env cleanup is guaranteed outside tests too.
3. Add a small lifecycle note to `AgentApplication` docs explaining:
   - ownership of the runtime env overlay
   - the meaning of `close()`
   - why conflicting live `CONFIG_DIR` overlays are rejected
4. Revisit whether any production code paths still create multiple live `AgentApplication` instances in one process with different `CONFIG_DIR` values; if not, the overlay implementation may be simplifiable later.