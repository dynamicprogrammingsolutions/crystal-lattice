# MCP OAuth Manual Flow

This manual helper validates an OAuth-protected MCP server end to end:

1. start OAuth and produce an authorization URL
2. finish OAuth by pasting the browser callback URL
3. verify the saved login by connecting to the MCP server and listing tools

The default scenario targets Figma MCP with Codex-like client metadata and a
localhost redirect. That shape is intentional: current Figma diagnostics showed
that Figma accepts `client_name: "Codex"` with loopback redirects, while it
rejects the Crystal custom scheme and public HTTPS callback unless Figma
explicitly allows that client/redirect combination.

## Commands

Run from the repository root.

Start the login:

```bash
python plugins/mcp-shared/tests/manual_mcp_oauth_flow.py start
```

The command prints an authorization URL. Open it in your browser, approve the
login, then copy the full callback URL from the browser address bar. The
browser may show a connection error for `127.0.0.1`; that is expected because no
local callback server is running.

Finish the login:

```bash
python plugins/mcp-shared/tests/manual_mcp_oauth_flow.py finish
```

Paste the full callback URL when prompted.

Verify the saved login:

```bash
python plugins/mcp-shared/tests/manual_mcp_oauth_flow.py verify
```

Expected success:

```text
MCP verification succeeded.
Status:
- figma: connected (... tools)

Tool count: ...
```

## Alternate Config

Use `--config` for another MCP server:

```bash
python plugins/mcp-shared/tests/manual_mcp_oauth_flow.py start --config /path/to/server.json
python plugins/mcp-shared/tests/manual_mcp_oauth_flow.py finish --config /path/to/server.json
python plugins/mcp-shared/tests/manual_mcp_oauth_flow.py verify --config /path/to/server.json
```

The config shape is intentionally close to application MCP config. Test-only
metadata lives under `mcp_oauth_manual`; server configuration lives under
`mcp_servers`.

```json
{
  "id": "provider-name",
  "mcp_oauth_manual": {
    "server_name": "provider",
    "connection_id": "manual-connection",
    "session_id": "manual-session",
    "plugin_id": "mcp_runtime_app",
    "action_id": "mcp_complete_login",
    "callback_port": 41793
  },
  "mcp_servers": {
    "provider": {
      "enabled": true,
      "transport": "http",
      "url": "https://mcp.example.test/mcp",
      "startup_timeout_seconds": 30,
      "oauth": {
        "client_name": "Crystal Lattice Control",
        "client_uri": "https://crystallattice.dev",
        "software_id": "crystal-lattice-control",
        "software_version": "0.1.0",
        "token_endpoint_auth_method": "none",
        "scope": "mcp:connect",
        "redirect_uri": "http://127.0.0.1:{port}/callback"
      }
    }
  }
}
```

Supported `redirect_uri` placeholders:

- `{connection_id}`
- `{session_id}`
- `{plugin_id}`
- `{action_id}`
- `{server_name}`
- `{port}`

`{port}` comes from `mcp_oauth_manual.callback_port`.

## Saved State

The helper writes local state to:

```text
plugins/mcp-shared/.manual-state/<scenario-id>/
```

Files:

- `<server>.pending.json`: authorization URL, PKCE verifier, dynamic client
  metadata, and token endpoint from `start`
- `<server>.token.json`: saved token from `finish`

`.manual-state/` is gitignored. Treat these files as local secrets because they
can contain OAuth client secrets and access tokens.

To use another state directory:

```bash
python plugins/mcp-shared/tests/manual_mcp_oauth_flow.py start --state-root /tmp/mcp-oauth-state
python plugins/mcp-shared/tests/manual_mcp_oauth_flow.py finish --state-root /tmp/mcp-oauth-state
python plugins/mcp-shared/tests/manual_mcp_oauth_flow.py verify --state-root /tmp/mcp-oauth-state
```

## Noninteractive Finish

If you prefer not to paste at the prompt:

```bash
python plugins/mcp-shared/tests/manual_mcp_oauth_flow.py finish \
  --callback-url 'http://127.0.0.1:41793/callback?code=...&state=...'
```

## Pytest Guard

The accompanying pytest file no longer contacts the provider. It only guards
that the default scenario and convenient command parser exist:

```bash
pytest plugins/mcp-shared/tests/test_mcp_oauth_manual_integration.py -q
```