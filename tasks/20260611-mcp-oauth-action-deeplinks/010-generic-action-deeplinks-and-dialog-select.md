# Generic Action Deeplinks And Dialog Select
Implement the shared frontend/backend capabilities for generic action deep links and chip-style action-dialog selection fields.

## Requirements checklist

- [ ] Add action-dialog support for `select` inputs rendered as chip-style single-choice controls.
- [ ] Document action-dialog `select` and `dropdown` behavior in `plugins/docs/ui-elements.md`.
- [ ] Add generic mobile handling for `crystal-lattice://action/...` deep links.
- [ ] Add a backend action-resolution path for optional plugin ids.
- [ ] Pass query parameters and the full callback URL to the invoked action.
- [ ] Add tests for dialog selection, action-deep-link parsing, successful routing, unknown actions, and ambiguous action ids.

Parent Task: `tasks/20260611-mcp-oauth-action-deeplinks/000-main.md`

## Related tasks

- `tasks/20260605-mobile-oauth-login-flows/020-auth-ux-and-framework-capability-audit.md`
- `tasks/20260605-mobile-oauth-login-flows/040-frontend-app-link-routing-and-action-resume.md`

## Design

The deep-link format should be generic and plugin-oriented:

```text
crystal-lattice://action/<plugin-id>/<action-id>?code=...&state=...
crystal-lattice://action/<action-id>?code=...&state=...
```

The first form executes an exact plugin/action pair. The second form asks the backend to resolve the action id across registered application plugins.

Frontend should pass action inputs like:

```json
{
  "code": "abc",
  "state": "xyz",
  "redirect_url": "crystal-lattice://action/mcp_runtime_app/mcp_complete_login?code=abc&state=xyz"
}
```

The frontend must not contain OAuth-specific logic. It should only route action links.

## Backend resolution rules

When a plugin id is present:

- Execute only that plugin's action.
- Return the normal action error if the plugin or action is missing.

When plugin id is absent:

- Find registered application actions whose `id` equals the requested action id.
- Execute if exactly one match exists.
- Return `unknown_action` if there are no matches.
- Return `ambiguous_action` if there are multiple matches, including candidate plugin ids in error details.

## Dialog selection behavior

Action-dialog inputs should support:

```json
{
  "name": "server_name",
  "type": "select",
  "label": "MCP server",
  "options": [
    {"value": "figma", "label": "Figma"}
  ],
  "required": true
}
```

Implementation notes:

- Reuse the existing `select` semantics already documented for config UI.
- Keep submitted values as strings.
- Use chip-style rendering for `select`.
- A later `dropdown` rendering can use the same option model if needed.
- Existing `$dialog.server_name` parameter mapping in `packages/frontend-sdk/src/plugins/actionRunner.ts` should continue to work without special cases.

## Starting points

- `packages/frontend-rn-components/src/ApplicationActionDialog.tsx`
  - Add select rendering and value initialization.
- `packages/frontend-sdk/src/types/plugins.ts`
  - Add or refine dialog input typings if needed.
- `packages/frontend-sdk/src/plugins/actionRunner.ts`
  - Likely only needs tests; existing `$dialog.*` mapping should handle selected values.
- `mobile/crystal-lattice-control-rn/App.tsx`
  - Likely home for app-level deep-link listener and route dispatch.
- `mobile/crystal-lattice-control-rn/src/ConnectedRoot.tsx`
  - May need a callback for executing application actions against the current backend/connection.
- `application/python/agent_terminal_app/server.py`
  - Add optional-plugin action resolution endpoint or extend existing action execution shape.
- `core/python/agent_app/application_future.py`
  - Add app-layer helper to resolve actions by id when plugin id is omitted, if the server should delegate resolution to `AgentApplication`.

## Test expectations

- Unit tests for `ApplicationActionDialog` select rendering and submitted values.
- Frontend parser tests for:
  - `crystal-lattice://action/plugin/action?code=a&state=b`
  - `crystal-lattice://action/action?code=a&state=b`
  - malformed routes.
- Backend tests for:
  - exact plugin/action dispatch.
  - omitted plugin with one action match.
  - omitted plugin with no action match.
  - omitted plugin with ambiguous action ids.

## Completion notes template

When completing this task, record:

- The final deep-link route grammar.
- The endpoint or SDK method used for optional-plugin action execution.
- Any frontend behavior when no backend connection is available.
- Test commands and results.