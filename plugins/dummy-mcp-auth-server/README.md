# Dummy MCP Auth Server

Local streamable HTTP MCP server for manually testing MCP OAuth login from Crystal Lattice.

The server is intentionally simple:

- unauthenticated `/mcp` requests return an OAuth challenge
- `/authorize` immediately approves and redirects back to the client callback
- `/token` exchanges the authorization code for a bearer token
- authenticated MCP clients can list/call the `dummy_auth_status` tool

## Run

```bash
python -m dummy_mcp_auth_server
```

By default the server binds to `0.0.0.0:8765`, so a phone on the same network can reach it. At startup it prints the LAN URL and a Crystal Lattice config snippet.

Common options:

```bash
python -m dummy_mcp_auth_server --port 8765
python -m dummy_mcp_auth_server --host 0.0.0.0 --public-host 192.168.1.20
```

Use `--public-host` if automatic LAN address detection picks the wrong interface.

## Crystal Lattice Config

The startup output includes a snippet like:

```json
{
  "mcp_enabled": true,
  "mcp_servers": {
    "dummy-auth": {
      "enabled": true,
      "transport": "http",
      "url": "http://192.168.1.20:8765/mcp",
      "startup_timeout_seconds": 5,
      "tool_timeout_seconds": 10
    }
  }
}
```

Manual flow:

1. Start this server.
2. Configure the MCP server URL in Crystal Lattice.
3. On mobile, open the session and enable MCP in session settings if needed.
4. Tap `Check MCP servers`.
5. Tap `Sign in to dummy-auth`.
6. Let the browser redirect back to `crystal-lattice://...`.
7. Tap `Check MCP servers` again if needed; it should show `connected`.