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
        "redirect_uri": "crystal-lattice://action/{connection_id}/{session_id}/{plugin_id}/{action_id}?server_name={server_name}"
      }
    }
  }
}
```

Supported redirect placeholders are `{connection_id}`, `{session_id}`,
`{plugin_id}`, `{action_id}`, and `{server_name}`.

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
