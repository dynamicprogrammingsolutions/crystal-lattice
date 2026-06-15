# `read_mcp_resource`

Reads a specific MCP resource by server name + URI.

## Handler behavior (implementation notes)

- Codex proxies the read call to the MCP server.
- Resource content is returned as tool output (typically as text or content items).
