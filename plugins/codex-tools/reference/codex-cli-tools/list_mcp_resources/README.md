# `list_mcp_resources`

Lists MCP resources, optionally per server.

## Handler behavior (implementation notes)

- Codex proxies this request to configured MCP servers and returns a structured resource listing.
- Pagination uses an opaque cursor.
