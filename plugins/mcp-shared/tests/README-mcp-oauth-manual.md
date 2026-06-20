# MCP OAuth Manual Start Matrix

This manual integration test validates the first half of OAuth login for any
OAuth-protected MCP server. It probes the MCP server, discovers OAuth metadata,
attempts client registration or metadata-url client creation, and asserts that a
successful start produces an authorization URL with the exact redirect URI under
test.

The test is intentionally JSON-driven. Client identity and redirect choices are
tester-provided data, not hardcoded product behavior.

## Run

From the repository root:

```bash
MCP_OAUTH_MANUAL_SCENARIO=plugins/mcp-shared/tests/manual_oauth_scenarios/figma.example.json \
pytest plugins/mcp-shared/tests/test_mcp_oauth_manual_integration.py \
  -m "manual_integration" -s
```

Run one redirect variant:

```bash
MCP_OAUTH_MANUAL_SCENARIO=plugins/mcp-shared/tests/manual_oauth_scenarios/figma.example.json \
MCP_OAUTH_MANUAL_VARIANT=in-app \
pytest plugins/mcp-shared/tests/test_mcp_oauth_manual_integration.py \
  -m "manual_integration" -s
```

Use a custom callback port for redirect templates containing `{port}`:

```bash
MCP_OAUTH_MANUAL_CALLBACK_PORT=41800 ...
```

## Scenario Shape

```json
{
  "id": "provider-name",
  "server": {
    "name": "provider",
    "config": {
      "enabled": true,
      "transport": "http",
      "url": "https://mcp.example.test/mcp",
      "oauth": {
        "client_name": "Crystal Lattice Control",
        "client_uri": "https://crystallattice.dev",
        "software_id": "crystal-lattice-control",
        "software_version": "0.1.0",
        "token_endpoint_auth_method": "none",
        "scope": "mcp:connect"
      }
    }
  },
  "defaults": {
    "connection_id": "manual-connection",
    "session_id": "manual-session",
    "plugin_id": "mcp_runtime_app",
    "action_id": "mcp_complete_login",
    "callback_port": 41793,
    "expected_start_outcomes": ["authorization_url"]
  },
  "redirect_matrix": [
    {
      "id": "in-app",
      "oauth": {
        "redirect_uri": "crystal-lattice://action/{connection_id}/{session_id}/{plugin_id}/{action_id}?server_name={server_name}"
      }
    }
  ]
}
```

Each redirect matrix entry is merged over `server.config.oauth`. This lets one
scenario test custom schemes, localhost callbacks, public HTTPS callbacks, and
provider-specific client metadata without changing code.

Supported redirect placeholders:

- `{connection_id}`
- `{session_id}`
- `{plugin_id}`
- `{action_id}`
- `{server_name}`
- `{port}`

The `{port}` placeholder is handled by the manual test before redirect-template
rendering.

## Assertions

For a successful start, the test asserts:

- the authorization URL contains the exact redirect URI for the variant
- the authorization URL state matches the stored pending state
- PKCE uses `S256`
- token endpoint, client info, resource, state, and code verifier are written to
  a local pending-state file

For provider diagnostics, a scenario may allow `"start_error"` in
`expected_start_outcomes`. This is useful for redirect/client matrices where a
provider may reject dynamic registration, for example with `403 Forbidden`.

## Local State

The test writes reports to:

```text
plugins/mcp-shared/.manual-state/<scenario-id>/<variant-id>.json
```

Override with:

```bash
MCP_OAUTH_MANUAL_STATE_DIR=/tmp/mcp-oauth-state
```

`.manual-state/` is gitignored. These files can contain OAuth pending state such
as PKCE verifiers and client information, so treat them as local test artifacts.