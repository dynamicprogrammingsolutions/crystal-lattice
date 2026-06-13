# Figma Remote MCP Validation And Codex Handoff
Validate the new MCP OAuth flow against Figma remote MCP as far as possible, document the setup, and update the Codex mobile login task to reuse the shared capabilities.

## Requirements checklist

- [ ] Add or document Figma remote MCP config using HTTP transport and OAuth auth.
- [ ] Run a real/manual smoke against `https://mcp.figma.com/mcp` as far as credentials and provider behavior allow.
- [ ] Verify that unauthenticated Figma startup reports an authentication-required state rather than a generic failure.
- [ ] Verify that successful login enables MCP tool discovery, if a real login can be completed.
- [ ] Document any Figma-specific OAuth limitations or required callback URI registration.
- [ ] Update `tasks/20260605-mobile-oauth-login-flows` with a handoff note to reuse generic action deep links and action-dialog selection.
- [ ] Add final docs or README notes for configuring OAuth-backed HTTP MCP servers.

Parent Task: `tasks/20260611-mcp-oauth-action-deeplinks/000-main.md`
Depends On: `tasks/20260611-mcp-oauth-action-deeplinks/020-mcp-oauth-shared-runtime-and-actions.md`

## Figma target

Figma's remote MCP endpoint is expected to be:

```text
https://mcp.figma.com/mcp
```

The target Crystal config shape should be:

```json
{
  "mcp_enabled": true,
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

## Validation scope

This task may require a real Figma login and possibly provider-side callback URI behavior that cannot be fully automated in CI. Treat this as a real/manual integration smoke unless a deterministic provider test endpoint is available.

Minimum useful validation:

- With Figma configured and no token, `MCP status` shows Figma as needing login.
- `MCP Login` starts the Figma login flow and opens the authorization URL.
- The redirect URL uses the generic action deep-link format:

```text
crystal-lattice://action/mcp_runtime_app/mcp_complete_login?code=...&state=...
```

- The mobile app routes the deep link to `mcp_runtime_app.mcp_complete_login`.
- If real login succeeds, subsequent status shows Figma authenticated and tool discovery works.

## Codex handoff

After the shared framework work exists, update the existing Codex task files so they do not redesign callback routing:

- `tasks/20260605-mobile-oauth-login-flows/040-frontend-app-link-routing-and-action-resume.md`
  - Note that generic action deep links now exist or are planned in this MCP task.
- `tasks/20260605-mobile-oauth-login-flows/050-complete-codex-browser-login-flow.md`
  - Note that Codex browser login should use the same action-dialog selection and deep-link action routing.

Codex should be able to use a callback route like:

```text
crystal-lattice://action/chatgpt_auth_app/codex_complete_browser_login?code=...&state=...
```

or, if action ids are unique:

```text
crystal-lattice://action/codex_complete_browser_login?code=...&state=...
```

## Documentation expectations

Document:

- How to configure an OAuth-backed HTTP MCP server.
- How to start `MCP Login`.
- What action deep-link callback URI a provider must allow.
- How to clear MCP credentials.
- Known limitations, especially if a provider requires HTTPS universal links rather than custom-scheme callbacks.

## Completion notes template

When completing this task, record:

- Exact Figma config used.
- Whether auth completed successfully.
- Tools discovered after login, if any.
- Any provider errors or callback URI restrictions.
- Task files updated for Codex reuse.