# MCP Shared Runtime Helpers

Internal helper package for MCP-backed tool wrappers.

This package is intentionally not a plugin bundle and does not expose
`agent_plugin.json`. It exists only to share vendor-neutral MCP runtime logic
across wrapper plugins such as Codex, Kimi, and Gemini MCP tool adapters.

## Shared package boundary

This package owns only:

- transport/runtime config dataclasses
- application-scoped MCP runtime registry
- MCP client lifecycle management
- raw tool discovery
- raw tool execution
- runtime reuse helpers
- server status snapshots
- shared OAuth login-start helpers and manual OAuth diagnostics

It does not own:

- tool naming visible to the model
- wrapper-specific config parsing
- schema shaping or sanitization policies
- provider-native or wrapper-specific result formatting
- UI elements

Wrapper plugins should parse their own config and convert it to the canonical
runtime config types exported here.

`MCPRegistry` is the MCP-specific object intended to be stored inside the
application-owned generic `runtime_store`. The store itself remains generic and
MCP-agnostic; only the registry knows how to cache and reuse live MCP runtimes.

## Manual OAuth diagnostics

The manual start-phase OAuth matrix lives in
`tests/README-mcp-oauth-manual.md`. It can be used with any OAuth-protected MCP
server by providing a JSON scenario that defines the server URL, client
metadata, and redirect URI matrix.

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
