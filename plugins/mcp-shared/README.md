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