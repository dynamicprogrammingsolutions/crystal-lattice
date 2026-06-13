# MCP OAuth Action Deeplinks
Add generic mobile action-deep-link handling and action-dialog selection capabilities, then use them to implement OAuth login for HTTP MCP servers such as Figma.

## Task checklist

- [ ] `tasks/20260611-mcp-oauth-action-deeplinks/010-generic-action-deeplinks-and-dialog-select.md`
  - SHARED CAPABILITY: Provides generic frontend/backend building blocks that `tasks/20260605-mobile-oauth-login-flows/000-main.md` should reuse for Codex login.
- [ ] `tasks/20260611-mcp-oauth-action-deeplinks/020-mcp-oauth-shared-runtime-and-actions.md`
  - DEPENDS ON `tasks/20260611-mcp-oauth-action-deeplinks/010-generic-action-deeplinks-and-dialog-select.md`
- [ ] `tasks/20260611-mcp-oauth-action-deeplinks/030-figma-remote-mcp-validation-and-codex-handoff.md`
  - DEPENDS ON `tasks/20260611-mcp-oauth-action-deeplinks/020-mcp-oauth-shared-runtime-and-actions.md`
  - HANDOFF TO `tasks/20260605-mobile-oauth-login-flows/000-main.md`

## Related tasks

- `tasks/20260605-mobile-oauth-login-flows/000-main.md`
  - Existing Codex-first mobile OAuth planning task.
  - This MCP task should implement the shared action-dialog and deep-link/action-routing capabilities first, so the Codex login work can reuse them instead of adding a separate callback-routing design.
- `tasks/20260605-mobile-oauth-login-flows/020-auth-ux-and-framework-capability-audit.md`
  - Identifies the need for chip-style login selection.
- `tasks/20260605-mobile-oauth-login-flows/040-frontend-app-link-routing-and-action-resume.md`
  - Identifies the need for mobile app-link/deep-link routing back into application actions.

## Design direction

The mobile/frontend layer should not contain MCP-specific or OAuth-specific callback logic. It should support a generic action deep-link format:

```text
crystal-lattice://action/<plugin-id>/<action-id>?code=...&state=...
crystal-lattice://action/<action-id>?code=...&state=...
```

The frontend parses the route, extracts the optional plugin id, action id, query parameters, and full callback URL, then executes the target application action. Plugin-specific logic remains in the plugin action. For OAuth flows, the plugin can parse and validate `state`, look up the persistent login attempt, exchange the code for tokens, and update its own storage.

When the plugin id is omitted, the backend should resolve by action id:

- If exactly one registered plugin exposes the action id, execute it.
- If no plugin exposes it, return `unknown_action`.
- If multiple plugins expose it, return `ambiguous_action` with candidate plugin ids.

## Current repo findings

- `packages/frontend-rn-components/src/ApplicationActionDialog.tsx`
  - Current action dialogs render form fields as text inputs.
  - It parses text, multiline, integer, number, and boolean values.
  - It does not yet render action-dialog `select` fields as chip-style choices.
- `plugins/docs/ui-elements.md`
  - Config UI already documents `select` as chip-style selection.
  - Session action dialogs document generic `form` inputs but need clearer support for `select`/`dropdown`.
- `packages/frontend-sdk/src/plugins/actionRunner.ts`
  - Already maps `$dialog.<field>` values into action parameters.
  - Existing mapping can carry selected values once the dialog component supports selection inputs.
- `packages/frontend-sdk/src/types/plugins.ts`
  - `open_url` already exists as a display follow-up action.
  - No special resumable `open_url` action is required if callback routing is encoded in the deep link itself.
- `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx` and `mobile/crystal-lattice-control-rn/src/SessionsScreen.tsx`
  - Existing display follow-up actions already open URLs with React Native `Linking.openURL`.
- `plugins/mcp-shared/src/mcp_shared/runtime.py`
  - MCP HTTP transport supports static headers today.
  - It does not yet support OAuth discovery, auth-required state, token refresh, or bearer-token injection from stored credentials.
- `plugins/mcp-runtime-app/src/mcp_runtime_app/__init__.py`
  - Already owns MCP status, reconnect, and clear-runtime application actions.
  - It is the best home for generic MCP login/status actions.

## Product intent

The user selects the session action `MCP Login`. The action presents MCP servers that require login using a chip-style selection field. The user chooses one and opens the provider login URL. On redirect, the mobile app receives a generic action deep link and routes it to the requested plugin/action with URL parameters. The MCP plugin completes the login and stores tokens for the MCP runtime.

For Figma remote MCP, the target server config is expected to look like:

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
      }
    }
  }
}
```

## Expected outcome

- Generic action deep links work on mobile and route to plugin actions.
- Action dialogs can render single-select options as chip-style choices.
- MCP shared runtime can authenticate OAuth-backed HTTP MCP servers.
- `mcp_runtime_app` exposes MCP login actions and enhanced status.
- Figma remote MCP is documented and validated as far as possible with real authentication.
- Codex mobile OAuth login task has a clear handoff to reuse these capabilities.