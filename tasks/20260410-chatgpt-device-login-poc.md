# ChatGPT Device Login POC Via Plugins

Create a minimum proof-of-concept ChatGPT login flow for cross-device use, using application plugins for login management, generic action endpoints for control, and a provider-side plugin hook so OpenAI Responses can use saved ChatGPT credentials instead of only API keys.

## Requirements checklist

- [ ] Implement an extremely minimal cross-device login UX based on device-code style auth:
  - `login_start` returns a verification URL, user code, and login id.
  - backend/plugin starts background polling immediately after `login_start`.
  - user can manually run `check_status`.
  - user can manually run `cancel_login`.
- [ ] Implement the login control flow as plugins, using application plugin actions and UI schema elements discoverable by existing frontend action plumbing.
- [ ] Support use from the existing frontend with only minimal URL/code display and manual `Check status` / `Cancel` actions; no event-driven UX is required for the proof of concept.
- [ ] Persist credentials under a path rooted in `CONFIG_DIR`, not a hardcoded path.
- [ ] Expose config-resolution environment variables such as `CONFIG_DIR` to plugin code in a first-class way, so plugins can compute paths from the same resolved environment used by config placeholder resolution.
- [ ] Make the saved credentials accessible to runtime provider logic via a feature or extension plugin.
- [ ] Add an OpenAI Responses auth integration that can switch between API-key mode and ChatGPT-auth mode, including endpoint/base-url selection and UI-driven switching.
- [ ] Cover the proof of concept with focused tests across config/env plumbing, application actions, persistence, cancellation, and provider-side credential usage.
- [ ] Document the proof-of-concept plugin authoring approach under the canonical docs in `plugins/docs`.

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
- optional `set_auth_mode` or `set_endpoint_mode`

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
- `set_auth_mode`

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

Suggested `set_auth_mode` result:

```json
{
  "status": "ok",
  "auth_mode": "api_key" | "chatgpt",
  "endpoint_mode": "api" | "chatgpt"
}
```

### 3. Minimal UI schema

The application plugin should expose minimal UI schema elements that the frontend can already consume or render manually:

- a global/action-surface item for `login_start`
- a global/action-surface item for `check_status`
- a global/action-surface item for `cancel_login`
- a global/action-surface item for `logout`
- a UI element or config control for `auth_mode` / endpoint selection

For the very first frontend proof of concept, it is acceptable if the mobile app calls these actions directly from a dedicated connection/auth panel instead of relying entirely on generic action rendering. The backend contract should still be application-plugin based so the frontend remains optional/thin.

### 4. Plugin-visible resolved environment contract

Add a first-class way for plugins to access the same resolved env mapping used during config placeholder resolution.

Minimum requirement:

- application plugins must be able to read `CONFIG_DIR`
- same should be available to core-side plugins used in the auth-consumption path

Preferred shape:

- add a top-level runtime-only mapping such as `_plugin_runtime.env` or `_resolved_env`
- or pass `resolution_env` into application plugin `init(...)` state/context through a documented contract

Requirements for this addition:

- do not force plugin authors to guess `CONFIG_DIR` via `os.getcwd()` or hardcoded relative paths
- document the contract in canonical docs under `plugins/docs`
- tests should assert `CONFIG_DIR` reaches plugin runtime

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
- explicit UI-driven switching between API and ChatGPT mode is enough

Suggested mode model:

- `auth_mode = "api_key"`:
  - use `config.api_key` or `OPENAI_API_KEY`
  - use existing API base URL logic
- `auth_mode = "chatgpt"`:
  - load saved ChatGPT credential file
  - use ChatGPT-specific auth header/token handling
  - use ChatGPT-compatible endpoint/base URL selected by config/UI

### 6. UI-driven endpoint/auth mode switching

The proof of concept should include a simple UI-driven control path for switching how OpenAI Responses authenticates and which endpoint family it uses.

This should be implemented through plugin-exposed UI/config/actions, not hardcoded frontend logic.

Minimum requirement:

- user can choose between:
  - API mode
  - ChatGPT mode
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
   - optional `set_auth_mode`
4. Implement background polling lifecycle started by `login_start`.
5. Persist credentials atomically under `${env:CONFIG_DIR}/...`.
6. Return simple status payloads only; no event-driven UX required for POC.

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
2. Add a mode switch that selects API auth vs ChatGPT auth.
3. Inject runtime base URL / auth header changes for OpenAI Responses.
4. Add tests that verify:
   - API mode still works as today
   - ChatGPT mode uses saved credentials
   - missing/expired credentials fail clearly
   - switching modes changes effective request config

Likely files:

- `plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py`
- new feature/extension file under `plugins/openai_responses/src/openai_responses_plugins/`
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

## Testing requirements

Minimum test coverage expected:

- config/env:
  - resolved env contract includes `CONFIG_DIR`
  - plugin receives it
- auth application plugin:
  - `login_start` returns verification info and marks attempt pending
  - background task saves credentials on simulated success
  - `check_status` reports pending/success/failure
  - `cancel_login` halts polling and reports canceled
  - `logout` clears saved credentials
- OpenAI Responses auth integration:
  - API mode unchanged
  - ChatGPT mode reads saved auth file
  - mode switch updates effective behavior
- server/frontend contract:
  - `/actions` shape remains compatible with the existing generic action executor

Relevant existing test surfaces:

- `core/python/tests/test_application_layer_app_plugins_basic.py`
- `application/python/tests/test_application_actions_endpoints.py`
- `plugins/openai_responses/tests/test_openai_responses_provider_unit.py`
- `plugins/openai_responses/tests/test_agent_application_openai_responses_provider_switch.py`

## Open questions to resolve during implementation

- Which exact provider/device-code protocol will be used for ChatGPT auth in the proof of concept?
- What is the ChatGPT-hosted base URL / endpoint contract for OpenAI Responses in auth mode?
- Should `auth_mode` be stored:
  - in a dedicated auth settings file under `CONFIG_DIR`
  - in application config overrides
  - or in session overrides for per-session experimentation?
- Do we want pending login attempts to survive server restart in the POC, or is in-memory attempt state acceptable?

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