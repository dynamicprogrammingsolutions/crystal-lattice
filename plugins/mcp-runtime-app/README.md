# MCP Runtime App Plugin

Application-level observability plugin for MCP runtimes.

This plugin exposes session actions for:

- showing MCP runtime status
- clearing stored MCP runtimes
- forcing reconnect on the next request by clearing runtimes
- starting and completing OAuth login for protected HTTP MCP servers

It is intentionally application-scoped rather than tool-scoped so that the UI
can inspect runtime state independent of any one wrapper plugin.

## OAuth configuration

OAuth settings are configured per MCP server under `oauth`. Client identity
fields default to Crystal Lattice values and can be overridden by the user for
providers that require specific registered metadata.

```json
{
  "mcp_enabled": true,
  "mcp_servers": {
    "example": {
      "enabled": true,
      "transport": "http",
      "url": "https://mcp.example.test/mcp",
      "oauth": {
        "client_name": "Crystal Lattice Control",
        "client_uri": "https://crystallattice.dev",
        "software_id": "crystal-lattice-control",
        "software_version": "0.1.0",
        "token_endpoint_auth_method": "none",
        "scope": "mcp:connect",
        "redirect_uri": "crystal-lattice://action/{connection_id}/{session_id}/{plugin_id}/{action_id}?server_name={server_name}",
        "token_exchange": {
          "include_client_secret": false,
          "include_resource": true
        }
      }
    }
  }
}
```

Supported redirect placeholders are `{connection_id}`, `{session_id}`,
`{plugin_id}`, `{action_id}`, and `{server_name}`.

`oauth.token_exchange.include_resource` controls whether the MCP resource is
sent during the authorization-code token exchange. It defaults to true when a
resource was discovered.

`oauth.token_exchange.include_client_secret` supports providers that register a
public client (`token_endpoint_auth_method: "none"`) but still require the
returned dynamic-registration `client_secret` in the token form. Figma's remote
MCP server currently needs this behavior when using the Gemini CLI compatible
client metadata:

```json
{
  "figma": {
    "enabled": true,
    "transport": "http",
    "url": "https://mcp.figma.com/mcp",
    "startup_timeout_seconds": 30,
    "oauth": {
      "client_name": "Gemini CLI MCP Client",
      "client_uri": null,
      "software_id": null,
      "software_version": null,
      "token_endpoint_auth_method": "none",
      "scope": "mcp:connect",
      "redirect_uri": "http://localhost:41793/oauth/callback",
      "token_exchange": {
        "include_client_secret": true,
        "include_resource": true
      }
    }
  }
}
```

Legacy flat keys such as `oauth_authorization_url`, `oauth_token_endpoint`, and
`oauth_client_id` are still accepted, but new configs should use the nested
`oauth` object.

## License

Copyright 2026 Dynamic Programming Solutions Kft.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

<http://www.apache.org/licenses/LICENSE-2.0>

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
