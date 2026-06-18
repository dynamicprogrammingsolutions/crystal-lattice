# MCP OAuth Shared Runtime And Actions
Add OAuth support for HTTP MCP servers in the shared MCP runtime and expose MCP login actions through the MCP runtime application plugin.

## Requirements checklist

- [ ] Extend MCP server config to describe OAuth-backed HTTP MCP servers.
- [ ] Add persistent MCP OAuth attempt and token storage owned by MCP shared/runtime code.
- [ ] Add PKCE login-start and callback-completion helpers.
- [ ] Add token refresh where supported by the OAuth server.
- [ ] Inject bearer tokens into HTTP MCP transport requests.
- [ ] Represent authentication-required and authenticated states in MCP status.
- [ ] Add MCP login, complete-login, clear-login, and enhanced-status actions to `mcp_runtime_app`.
- [ ] Add the session action `MCP Login` with chip-style server selection.
- [ ] Add unit tests with deterministic fake OAuth/MCP behavior.

Parent Task: `tasks/20260611-mcp-oauth-action-deeplinks/000-main.md`
Depends On: `tasks/20260611-mcp-oauth-action-deeplinks/010-generic-action-deeplinks-and-dialog-select.md`

## Current state

`plugins/mcp-shared/src/mcp_shared/runtime.py` currently supports these transports:

- `stdio`
- `sse`
- `http`

For HTTP/SSE, config supports:

- `url`
- `headers`

This is enough for static bearer-token or API-key style auth, but not for Figma-style browser/OAuth login.

`plugins/mcp-runtime-app/src/mcp_runtime_app/__init__.py` currently exposes:

- `mcp_show_status`
- `mcp_reconnect_servers`
- `mcp_clear_runtime`

This plugin should be extended to own MCP login actions because it is already the application-level owner of MCP runtime status and controls.

## Config design

Extend MCP server config with an auth block, for example:

```json
{
  "mcp_servers": {
    "figma": {
      "enabled": true,
      "transport": "http",
      "url": "https://mcp.figma.com/mcp",
      "auth": {
        "type": "oauth"
      },
      "startup_timeout_seconds": 30,
      "tool_timeout_seconds": 60
    }
  }
}
```

Keep static headers supported:

```json
{
  "headers": {
    "Authorization": "Bearer ${env:FIGMA_MCP_TOKEN}"
  }
}
```

If both static headers and OAuth are configured, define deterministic precedence. Recommended: explicit static `Authorization` header wins unless config opts into OAuth-managed authorization.

## Storage design

MCP shared/runtime code should own persistent auth storage. Store project-specific data under `.crystal`, consistent with existing project-local storage direction.

Suggested logical records:

- OAuth login attempts:
  - attempt id
  - server name
  - plugin/action callback route
  - state
  - PKCE verifier
  - redirect URI
  - created/expiry timestamp
  - session id if the login was started from a session action
- OAuth tokens:
  - server name
  - access token
  - refresh token, if present
  - expiry timestamp, if present
  - scopes/resource metadata, if present

Do not store routing-critical attempt state only in frontend memory. The backend/plugin must be able to complete a callback using `state` and persistent attempt storage.

## Action design

Add actions to `mcp_runtime_app`:

```text
mcp_login
mcp_start_login
mcp_complete_login
mcp_clear_login
mcp_show_status
```

Recommended behavior:

- `mcp_login`
  - Entry-point action for the `MCP Login` session action.
  - If one server requires login, start login directly.
  - If multiple servers require login, present a form with `type: "select"` for `server_name`.
- `mcp_start_login`
  - Creates an OAuth attempt and returns an `open_url` action.
  - Redirect URI should use the generic action deep-link format:

```text
crystal-lattice://action/mcp_runtime_app/mcp_complete_login
```

- `mcp_complete_login`
  - Receives `code`, `state`, and `redirect_url`.
  - Validates state against persistent attempt storage.
  - Exchanges the code for tokens.
  - Stores tokens.
  - Clears or marks the attempt complete.
  - Returns a success/error display.
- `mcp_clear_login`
  - Clears stored credentials for one server.
- `mcp_show_status`
  - Include auth status per server, such as `not_configured`, `authentication_required`, `authenticated`, `expired`, or `failed`.

## Runtime behavior

When starting an OAuth-backed HTTP server:

- If a valid access token exists, inject `Authorization: Bearer <token>`.
- If the token is expired and a refresh token exists, refresh first.
- If no valid token exists, mark the server `authentication_required` instead of collapsing into a generic startup failure.
- If config `fail_on_startup_error` is true, decide whether `authentication_required` should fail startup or be reported as a recoverable status. Prefer recoverable unless the user explicitly asks for fatal auth failures.

## Starting points

- `plugins/mcp-shared/src/mcp_shared/runtime.py`
- `plugins/mcp-shared/src/mcp_shared/registry.py`
- `plugins/mcp-runtime-app/src/mcp_runtime_app/__init__.py`
- `plugins/mcp-shared/tests`
- `plugins/mcp-runtime-app/tests`
- `application/python/tests`

## Test expectations

Use deterministic tests before real-network validation:

- Fake OAuth metadata/token exchange flow.
- Fake HTTP MCP server requiring auth.
- Login start produces an authorization URL with a generic action deep-link redirect URI.
- Completion validates state and stores tokens.
- Runtime injects bearer token after login.
- Status action reports authentication-required before login and authenticated after login.
- Clear-login removes credentials and returns to authentication-required.

## Completion notes template

When completing this task, record:

- Exact config schema additions.
- Exact storage path(s) under `.crystal`.
- Whether OAuth discovery is fully implemented or initially config-driven.
- Test commands and results.