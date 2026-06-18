# MCP Auth-Required Runtime Handling And Login Flow

Add regression coverage and implementation steps for MCP servers that require OAuth login. The first goal is to stop auth-required or otherwise unresponsive MCP servers from hanging request preparation; the second goal is to build a generic login flow on top of the action deep-link infrastructure.

## Requirements checklist

- [x] Add a failing regression test showing that an auth-required HTTP MCP server does not hang startup/tool discovery.
- [x] Apply MCP server `startup_timeout_seconds` to the full startup path, including transport open, session creation, `initialize`, and initial `list_tools`.
- [x] Surface MCP startup failures as actionable runtime status instead of silently blocking or returning no user-visible feedback.
- [x] Detect authentication-required MCP failures where practical, including HTTP `401` / `WWW-Authenticate` challenges and MCP SDK OAuth/auth errors.
- [x] Expose auth-required MCP server status through the existing MCP runtime status action.
- [ ] Add a login affordance for auth-required MCP servers that uses generic application actions and display payloads.
- [ ] Implement OAuth login using the MCP SDK auth primitives where possible, rather than hand-rolling OAuth protocol behavior.
- [ ] Route OAuth callback completion through the generic action deep-link format with required connection id and session id.
- [ ] Keep mobile deep-link routing generic; do not add MCP-specific routing logic to the frontend.
- [x] Add deterministic tests for timeout/status/auth-required behavior before adding heavier OAuth integration coverage.

Parent Task: `tasks/20260611-mcp-oauth-action-deeplinks/000-main.md`

## Background

The generic action deep-link infrastructure already supports links of the form:

```text
crystal-lattice://action/<connection-id>/<session-id>/<action-id>?result=approved&nonce=n-123
crystal-lattice://action/<connection-id>/<session-id>/<plugin-id>/<action-id>?result=approved&nonce=n-123
```

This task should use that infrastructure for MCP login callback completion. It should not introduce MCP-specific mobile routing.

The current MCP runtime code is shared by multiple MCP tool plugins, so the first fix should be generic runtime reliability rather than an OAuth-only UI patch. If an MCP server requires login, or if any MCP server stalls during startup, request preparation should return within a bounded time and show actionable status.

Important starting points:

- `plugins/mcp-shared/src/mcp_shared/runtime.py`
  - `MCPRuntimeManager.start`
  - `MCPRuntimeManager._connect_server`
  - `MCPRuntimeManager._open_session`
  - `MCPServerRuntimeSpec.startup_timeout_seconds`
  - `MCPServerSnapshot`
- `plugins/mcp-shared/src/mcp_shared/registry.py`
  - Runtime reuse and snapshot propagation.
- `plugins/mcp-runtime-app/src/mcp_runtime_app/__init__.py`
  - Existing `mcp_show_status`, `mcp_reconnect_servers`, and `mcp_clear_runtime` actions.
- `plugins/claude-tools/src/claude_tools/claude_mcp_tool.py`
  - Builds `MCPRuntimeConfig` and calls the shared runtime.
- `plugins/codex-tools/src/codex_tools/mcp_tool.py`
  - Builds `MCPRuntimeConfig` and calls the shared runtime.

## Standard MCP OAuth References

There does not appear to be an official "everything server with OAuth required" equivalent. Use the official MCP authorization model and conformance tooling as references, but prefer a deterministic local fixture for the first regression.

Relevant standards and examples:

- MCP Authorization specification:
  `https://modelcontextprotocol.io/specification/2025-06-18/basic/authorization`
- MCP authorization tutorial:
  `https://modelcontextprotocol.io/docs/tutorials/security/authorization`
- MCP conformance framework:
  `https://github.com/modelcontextprotocol/conformance`
- Python SDK simple auth example:
  `https://github.com/modelcontextprotocol/python-sdk/tree/main/examples/servers/simple-auth`

The installed Python MCP SDK includes client auth primitives:

- `mcp.client.auth.OAuthClientProvider`
- `mcp.client.auth.TokenStorage`

The installed MCP HTTP transports accept an `auth=` parameter:

- `mcp.client.streamable_http.streamablehttp_client(..., auth=...)`
- `mcp.client.sse.sse_client(..., auth=...)`

Use those primitives where possible for the real OAuth flow.

## Execution plan

### 1. Add the failing regression first

Add a test under:

```text
plugins/mcp-shared/tests/test_runtime.py
```

Suggested test name:

```python
test_http_mcp_auth_required_does_not_hang_startup
```

The regression should simulate an HTTP MCP server or MCP transport that requires authentication and does not complete normal startup unless OAuth is handled.

The test should assert:

- `MCPRuntimeManager.start(config)` returns within `startup_timeout_seconds`.
- `manager.status_snapshot()` contains the configured server.
- The server state is either:
  - a new explicit state such as `auth_required`, or
  - `failed` with an actionable auth-related error if a new state is deferred.
- `manager.list_tools()` returns an empty list.
- No exception escapes when `fail_on_startup_error=False`.

This test is expected to fail against the current implementation because `_connect_server` calls `_open_session`, `session.initialize`, and `session.list_tools` without wrapping the full startup path in a timeout.

### 2. Fix generic MCP startup hangs

Apply `MCPServerRuntimeSpec.startup_timeout_seconds` around the full per-server startup path:

- transport open
- session creation
- `session.initialize()`
- initial `session.list_tools()`

Use a default timeout if no per-server timeout is configured. The default should be long enough for normal local stdio startup but finite so a server cannot hang the whole request forever.

When startup times out:

- close any partially opened stack/session
- store a snapshot for the server
- keep the request moving when `fail_on_startup_error=False`
- re-raise only when `fail_on_startup_error=True`

The error message should be user-facing enough to explain what happened, for example:

```text
Timed out while starting MCP server '<name>' after <n>s.
```

### 3. Detect auth-required failures

Classify authentication-required startup failures where practical.

Inputs to consider:

- HTTP `401 Unauthorized`
- `WWW-Authenticate` challenges
- MCP SDK OAuth errors such as `OAuthFlowError`, `OAuthTokenError`, or related auth exceptions
- protected resource metadata failures that clearly indicate auth is required

Preferred snapshot shape:

```python
MCPServerSnapshot(
    name="server",
    enabled=True,
    transport="http",
    state="auth_required",
    tool_count=0,
    error="Authentication required. Open MCP status to sign in.",
)
```

If introducing `auth_required` is too disruptive, use `state="failed"` initially but make the error actionable and include enough information for the app plugin to show a login affordance.

### 4. Improve MCP runtime status UX

Update `plugins/mcp-runtime-app/src/mcp_runtime_app/__init__.py` so `mcp_show_status` clearly shows failed/auth-required MCP servers.

For an auth-required server, the display should include:

- server name
- state
- concise actionable message
- a login follow-up action if enough metadata is available to start login

The follow-up action should use the standard action display shapes, for example:

```json
{
  "kind": "run_action",
  "id": "mcp-start-login-<server>",
  "label": "Sign in",
  "plugin": "mcp_runtime_app",
  "action_id": "mcp_start_login",
  "fixed_params": {
    "server_name": "<server>"
  }
}
```

Do not add MCP-specific behavior to the mobile link handler. The runtime app should expose actions; the frontend should render and execute them generically.

### 5. Add a deterministic local auth-required fixture

Do not make the first regression depend on a real external OAuth provider.

Create a small in-test fixture or helper server that behaves like a protected MCP resource:

- `POST /mcp` returns `401 Unauthorized`
- response includes a `WWW-Authenticate` header with protected resource metadata
- `GET /.well-known/oauth-protected-resource` returns JSON similar to:

```json
{
  "resource": "http://127.0.0.1:<port>/mcp",
  "authorization_servers": ["http://127.0.0.1:<port>/auth"]
}
```

This is enough to test auth-required detection and no-hang behavior. A later integration test can use the Python SDK `simple-auth` example or the official MCP conformance auth suite.

### 6. Implement real OAuth login after the no-hang fix

After runtime startup is bounded and auth-required status is visible, add the real login path.

Use the MCP SDK auth primitives:

- `OAuthClientProvider`
- `TokenStorage`
- transport `auth=` parameter

Likely work:

- Add token/client-info storage keyed by MCP server identity.
- Build an `OAuthClientProvider` for HTTP/SSE MCP transports when auth is configured or required.
- Make the provider's redirect/login path produce an application display payload rather than blocking indefinitely.
- Add an action such as `mcp_start_login` that returns:
  - `open_url` action for the authorization URL
  - `copy_text` action for the authorization URL
- Add an action such as `mcp_complete_login` that:
  - receives query inputs and `redirect_url` from the generic action deep-link parser
  - completes the OAuth token exchange
  - stores tokens
  - clears/reconnects the relevant MCP runtime
  - returns a clear completion display/status

Callback links should use the generic route:

```text
crystal-lattice://action/<connection-id>/<session-id>/mcp_complete_login?...
```

or the plugin-qualified form only when exact dispatch is required:

```text
crystal-lattice://action/<connection-id>/<session-id>/mcp_runtime_app/mcp_complete_login?...
```

### 7. Add test coverage in layers

Add tests in this order:

1. Runtime regression: auth-required MCP startup does not hang.
2. Runtime timeout: startup timeout covers `initialize` and initial `list_tools`.
3. Runtime status: auth challenges become `auth_required` or actionable failed status.
4. Runtime app status: `mcp_show_status` renders auth-required status clearly.
5. Runtime app action: auth-required status exposes a generic `run_action` login affordance when possible.
6. Login action unit tests: `mcp_start_login` returns `open_url` and `copy_text` display actions.
7. Callback action unit tests: `mcp_complete_login` accepts generic deep-link callback inputs and updates stored auth state.
8. SDK/app integration: generated callback links parse and execute through session-scoped action execution.
9. React Native integration: `handleIncomingUrl(url)` routes the callback by connection and session, using the already generic mobile deep-link handler.
10. Optional later conformance/integration: run the MCP conformance `auth` suite or Python SDK `simple-auth` example against the implementation.

## Validation plan

Start with focused tests:

```bash
pytest plugins/mcp-shared/tests/test_runtime.py -q
pytest plugins/mcp-runtime-app/tests/test_mcp_runtime_app.py -q
```

Then run the MCP tool plugin tests that consume the shared runtime:

```bash
pytest plugins/claude-tools/tests/test_claude_mcp_tool.py -q
pytest plugins/codex-tools/tests/test_mcp_tool.py -q
```

If login actions touch generic action-deep-link behavior, also run:

```bash
pytest application/python/tests/test_application_actions_endpoints.py -q
npm --workspace @crystal-lattice/frontend-sdk test
cd mobile/crystal-lattice-control-rn && npm run tsc
cd mobile/crystal-lattice-control-rn && npm test -- --runInBand
```

If native/mobile callback behavior is touched, also verify the iOS build:

```bash
xcodebuild -workspace mobile/crystal-lattice-control-rn/ios/CrystalLatticeControlRN.xcworkspace \
  -scheme CrystalLatticeControlRN \
  -configuration Debug \
  -sdk iphonesimulator \
  -destination 'generic/platform=iOS Simulator' \
  build -quiet
```

Always finish with:

```bash
git diff --check
```

## Completion Notes

Add notes here during completion, including:

- final server state model for auth-required MCP servers
- timeout defaults and where they apply
- whether `auth_required` was added or actionable `failed` status was used
- login action ids and callback route grammar
- test commands and results

Progress update during completion:

- Added `auth_required` as a shared MCP server snapshot state.
- Added a same-task startup timeout around the full per-server startup path in `MCPRuntimeManager`, covering transport/session open, `initialize`, and initial `list_tools`.
- Avoided `asyncio.wait_for` for successful runtime startup because it opens the MCP/anyio transport in a child task and then closes from the caller task, which breaks real stdio MCP cleanup.
- Added actionable auth-required startup errors: `Authentication required for this MCP server. Open MCP status to sign in. ...`
- Added deterministic tests for:
  - startup does not hang when `initialize` stalls
  - startup timeout covers initial `list_tools`
  - HTTP 401-style startup failures are classified as `auth_required`
  - `mcp_show_status` displays auth-required server state and message
- Validation passed:
  - `pytest plugins/mcp-shared/tests/test_runtime.py plugins/mcp-runtime-app/tests/test_mcp_runtime_app.py plugins/claude-tools/tests/test_claude_mcp_tool.py plugins/codex-tools/tests/test_mcp_tool.py -q`
  - `python -m black --check plugins/mcp-shared/src/mcp_shared/runtime.py plugins/mcp-shared/tests/test_runtime.py plugins/mcp-runtime-app/tests/test_mcp_runtime_app.py`
  - `git diff --check`