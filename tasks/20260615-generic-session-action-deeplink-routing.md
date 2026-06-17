# Generic Session Action Deep-Link Routing

Implement the next iteration of generic action deep links so every callback URL routes to a specific mobile connection and session, while keeping only the executing plugin id optional. This makes callback-producing plugins replaceable and allows the triggering plugin to differ from the plugin that executes the resumed action.

## Requirements checklist

- [x] Change the action deep-link grammar so connection id and session id are required path segments.
- [x] Keep plugin id optional, and resolve omitted plugin ids in the application layer rather than in the HTTP server.
- [x] Support session-scoped action execution for application, feature, and provider-extension actions when resolving omitted plugin ids.
- [x] Keep the feature generic: tests and fixtures must not use MCP/OAuth-specific plugin names, action names, or query parameters.
- [x] Add a generic dummy application plugin that can exercise callback completion before any real plugin adopts the feature.
- [x] Add SDK end-to-end integration coverage using the dummy plugin and a real backend server.
- [x] Add React Native integration coverage that calls a testable `handleIncomingUrl(url)`-style entry point and asserts connection/session routing.
- [x] Update plugin/frontend docs for the new route grammar and routing behavior.

## Agreed implementation plan

### Deep-link grammar

Use path slugs for required routing context:

```text
crystal-lattice://action/<connection-id>/<session-id>/<action-id>?result=approved&nonce=n-123
```

Plugin-qualified form:

```text
crystal-lattice://action/<connection-id>/<session-id>/<plugin-id>/<action-id>?result=approved&nonce=n-123
```

Parsing rules:

- Three path segments after `action` mean:
  - `connectionId`
  - `sessionId`
  - `actionId`
- Four path segments after `action` mean:
  - `connectionId`
  - `sessionId`
  - `pluginId`
  - `actionId`
- Any other number of path segments is invalid.
- Query params are action inputs.
- The frontend injects `redirect_url` into action inputs with the full original callback URL.
- `connectionId` and `sessionId` are routing metadata, not ordinary query inputs.

Expected parser shape:

```ts
{
  connectionId: "test-connection",
  sessionId: "session-123",
  pluginId?: "generic_callback_app",
  actionId: "complete_external_flow",
  inputs: {
    result: "approved",
    nonce: "n-123",
    redirect_url: "crystal-lattice://action/..."
  },
  redirectUrl: "crystal-lattice://action/..."
}
```

### Frontend routing behavior

Mobile deep-link handling should:

- Parse the incoming URL.
- Require `connectionId` and `sessionId`; reject links missing either.
- Find the backend connection by `connectionId`.
- Never silently fall back to the current connection when the URL names a different or missing connection.
- If the connection exists and is active, execute through that backend.
- If the connection exists but is inactive, switch/reconnect or queue the action specifically for that connection.
- If no connection exists for `connectionId`, show or record an unknown-connection error and do not execute.
- Always execute against the session-scoped action path because every valid route includes `sessionId`.

Preferred SDK call shape:

```ts
backend.executeSessionAction({
  sessionId: parsed.sessionId,
  pluginId: parsed.pluginId,
  actionId: parsed.actionId,
  inputs: parsed.inputs,
});
```

Extract the mobile route handling into a testable function or hook, such as:

```ts
handleIncomingUrl(url: string): Promise<void>
```

or:

```ts
createActionDeepLinkHandler({
  getBackendForConnection,
  queuePendingAction,
  onActionResult,
  onActionError,
});
```

### Backend ownership

The HTTP server should not resolve omitted plugin ids. It should parse JSON, pass parameters to the app layer, and wrap the result.

Change `AgentApplication.execute_action` so `plugin_id` is optional:

```py
def execute_action(
    self,
    plugin_id: Optional[str],
    action_id: str,
    params: Dict[str, Any],
    *,
    action_owner: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    ...
```

Resolution rules:

- If `plugin_id` is present, preserve exact plugin/action dispatch.
- If `plugin_id` is omitted, resolve by `action_id` using the target session context.
- Because valid deep links always include `sessionId`, omitted-plugin resolution should be able to consider:
  - application actions
  - feature actions available in the session
  - provider-extension actions available in the session
- If exactly one candidate matches, execute it.
- If no candidates match, return/raise `unknown_action`.
- If multiple candidates match, return/raise `ambiguous_action`.

Ambiguity details should include owner information:

```json
{
  "error_type": "ambiguous_action",
  "details": {
    "candidates": [
      {
        "plugin": "generic_callback_app",
        "action_id": "complete_external_flow",
        "action_owner": "application"
      },
      {
        "plugin": "generic_callback_feature",
        "action_id": "complete_external_flow",
        "action_owner": "feature"
      }
    ]
  }
}
```

If the server response needs the resolved plugin id, add an app-layer metadata-returning method rather than doing lookup in the server:

```py
@dataclass(frozen=True)
class ExecutedAction:
    plugin_id: str
    action_id: str
    action_owner: Optional[str]
    result: Dict[str, Any]
```

Then expose:

```py
def execute_action_with_metadata(...) -> ExecutedAction:
    ...
```

and keep `execute_action(...)` as a compatibility wrapper returning only `.result`.

### Generic dummy plugin

Add a generic test plugin or fixture, not an MCP/OAuth-specific one.

Suggested plugin id:

```text
generic_callback_app
```

Suggested action ids:

```text
start_external_flow
complete_external_flow
choose_external_target
```

`complete_external_flow` should echo received inputs and session/context details:

```json
{
  "handled": true,
  "action": "complete_external_flow",
  "inputs": {
    "result": "approved",
    "nonce": "n-123",
    "redirect_url": "..."
  },
  "context": {
    "session_id": "session-123"
  }
}
```

For ambiguity tests, add a second dummy plugin or fixture action exposing the same `complete_external_flow` action id.

## Test plan

Use generic names everywhere:

- `generic_callback_app`
- `generic_callback_feature`
- `complete_external_flow`
- `result=approved`
- `nonce=n-123`
- `test-connection`

Do not use MCP/OAuth-specific names such as `mcp_runtime_app`, `mcp_complete_login`, `code`, or `state` in the primary tests.

### Parser unit tests

Add or update parser tests for:

- action-only session route:
  ```text
  crystal-lattice://action/test-connection/session-123/complete_external_flow?result=approved&nonce=n-123
  ```
- plugin-qualified session route:
  ```text
  crystal-lattice://action/test-connection/session-123/generic_callback_app/complete_external_flow?result=approved
  ```
- rejected routes:
  - missing connection id
  - missing session id
  - missing action id
  - extra path segments
  - wrong scheme/host
- query params become inputs.
- `redirect_url` is injected.
- `connectionId` and `sessionId` are not included as ordinary action inputs.

### Backend/app tests

Add app-layer and endpoint tests for:

- `execute_action(plugin_id=None, session_id=...)` resolves a unique session-scoped candidate.
- exact plugin dispatch remains exact.
- omitted plugin with no matching action returns `unknown_action`.
- omitted plugin with multiple matching candidates returns `ambiguous_action`.
- ambiguity details include `plugin`, `action_id`, and `action_owner`.
- feature/provider-extension action candidates can be resolved with session context.
- the server does not implement candidate lookup itself.

### Option A: SDK end-to-end integration

Add an SDK integration test that starts a real backend server with the generic dummy plugin.

Test flow:

- Start backend with deterministic provider plus `generic_callback_app`.
- Create a real session.
- Parse:
  ```text
  crystal-lattice://action/test-connection/<session-id>/complete_external_flow?result=approved&nonce=n-123
  ```
- Assert parsed values:
  - `connectionId == "test-connection"`
  - `sessionId == <session-id>`
  - `pluginId` is omitted
  - `actionId == "complete_external_flow"`
  - inputs include only `result`, `nonce`, and `redirect_url`
- Execute through the session-scoped SDK action method.
- Assert:
  - response `status == "ok"`
  - resolved plugin is `generic_callback_app`
  - action id is `complete_external_flow`
  - result includes `result == "approved"`
  - result includes `nonce == "n-123"`
  - result includes the full `redirect_url`
  - result/session context matches the created session.

Add variants for:

- Plugin-qualified route exact dispatch.
- Unknown action.
- Ambiguous action.
- Session feature/provider-extension action resolution.

### Option B: React Native integration

Use the test harness from `task/20260615-mobile-component-integration-tests` if it helps. That branch includes:

- `@testing-library/react-native`
- `renderWithMobileProviders`
- `jest.integration.config.js`
- `startMobileComponentBackend`
- a real-backend component integration pattern

It can be merged or cherry-picked into this branch if the harness is still compatible.

RN integration test flow:

- Start a real backend with `generic_callback_app`.
- Create a real session.
- Render a small test host component that uses the real deep-link handler.
- Register a connection:
  ```ts
  {
    connectionId: "test-connection",
    backend: started.backend
  }
  ```
- Call:
  ```ts
  await handleIncomingUrl(
    `crystal-lattice://action/test-connection/${sessionId}/complete_external_flow?result=approved&nonce=n-123`
  );
  ```
- Assert visible UI or captured callback:
  - generic success text such as `Generic action complete`, or
  - result callback receives the expected generic action result.
- Assert backend-visible behavior:
  - action executed on the backend for `test-connection`.
  - session-scoped route was used.
  - resolved plugin is `generic_callback_app`.
  - result includes the generic inputs.

Add RN negative routing tests:

- Unknown connection:
  ```text
  crystal-lattice://action/missing-connection/<session-id>/complete_external_flow?result=approved
  ```
  Assert no backend call and an unknown-connection error.
- Wrong session:
  ```text
  crystal-lattice://action/test-connection/missing-session/complete_external_flow?result=approved
  ```
  Assert backend reports failure and no fallback to another session.
- Plugin-qualified route:
  ```text
  crystal-lattice://action/test-connection/<session-id>/generic_callback_app/complete_external_flow?result=approved
  ```
  Assert exact dispatch works through mobile routing.

## References

- Follow-up from: `tasks/20260611-mcp-oauth-action-deeplinks/010-generic-action-deeplinks-and-dialog-select.md`
- Useful testing harness branch: `task/20260615-mobile-component-integration-tests`

## Completion Notes

Added during completion.

- Implemented the required deep-link grammar:
  - `crystal-lattice://action/<connection-id>/<session-id>/<action-id>?result=approved&nonce=n-123`
  - `crystal-lattice://action/<connection-id>/<session-id>/<plugin-id>/<action-id>?result=approved&nonce=n-123`
- Updated `parseActionDeepLink` to return `connectionId`, `sessionId`, optional `pluginId`, `actionId`, action inputs, and full `redirect_url`.
- Moved omitted-plugin action resolution into `AgentApplication.execute_action_with_metadata`; the server now passes request data and session route context to the application layer and uses returned metadata for the response envelope.
- Omitted-plugin resolution considers application actions and, when session context is present, provider-extension and feature session actions.
- Added `GenericCallbackAppPlugin` as a generic fixture for callback completion tests.
- Added mobile `createActionDeepLinkHandler` and wired `App.tsx` through it. Mobile now routes action links by required connection id, queues existing inactive connections, rejects unknown connections, and always calls the session-scoped action endpoint.
- Added SDK integration coverage using a real backend server and generic callback plugin.
- Added React Native handler tests for successful routing, unknown connection, queued inactive connection, and ignored unrelated URLs.
- Added React Native real-backend integration coverage under `__integration__`, with a separate Jest integration config/script so the normal mobile test and typecheck paths stay fast.
- Test results:
  - Passed: `npm --workspace @crystal-lattice/frontend-sdk test`
  - Passed: `npm --workspace @crystal-lattice/frontend-rn-components test`
  - Passed: `npx vitest run --config vitest.integration.config.ts src/integration/__tests__/actionDeepLinks.integration.test.ts` from `packages/frontend-sdk`
  - Passed: `npm run tsc` from `mobile/crystal-lattice-control-rn`
  - Passed: `npm test -- --runInBand` from `mobile/crystal-lattice-control-rn`
  - Passed: `npm run test:integration -- --runTestsByPath __integration__/actionDeepLinkRouting.realBackend.integration.test.ts` from `mobile/crystal-lattice-control-rn`
  - Passed: `pytest application/python/tests/test_application_actions_endpoints.py application/python/tests/test_provider_extension_session_actions_endpoints.py application/python/tests/test_feature_plugin_context_enrichment.py -q`
  - Passed: `python -m black --check core/python/agent_app/application_future.py core/python/tests/generic_callback_app_plugin.py application/python/tests/test_application_actions_endpoints.py application/python/tests/test_provider_extension_session_actions_endpoints.py application/python/tests/test_feature_plugin_context_enrichment.py`
  - Passed: `git diff --check`

## Execution plan

Added during completion.

- Update the SDK parser and tests to require `connectionId` and `sessionId` path segments, using only generic fixture names and query parameters.
- Move optional-plugin resolution into `AgentApplication` by adding a metadata-returning action execution API and making `execute_action` accept omitted plugin ids.
- Pass the session route id to the application layer as execution context from `/sessions/{session_id}/actions`, without injecting it into application action inputs.
- Allow `executeSessionAction` in the frontend SDK to omit `pluginId`, matching app-level action execution.
- Refactor mobile deep-link execution into a testable handler that routes by required connection id and always calls the session-scoped action endpoint.
- Add generic app/plugin fixtures and tests for app-layer/server resolution, SDK integration, and React Native handler routing.