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

## Follow-up plan: move generic callback plugin to `plugins/` and test generated copy links

Added after completion for explicit approval before implementation.

### Goal

Move the generic callback test plugin out of `core/python/tests` and into
`plugins/`, modeled after `plugins/dummy-settings-app`, and make it exercise the
full flow:

1. A plugin action generates a callback deep link.
2. The action result exposes that link through a copy-link display button.
3. SDK and mobile integration tests use the generated copied URL as the input to
   the deep-link parser/routing flow.

This keeps the callback feature generic and verifies it before any real plugin,
such as an MCP/OAuth plugin, depends on it.

### Plugin location

Create a first-party plugin project:

```text
plugins/generic-callback-app/
```

Expected structure:

```text
plugins/generic-callback-app/
  README.md
  pyproject.toml
  agent_plugin.json
  src/generic_callback_app/__init__.py
  tests/test_generic_callback_app.py
```

This replaces the current test-only fixture:

```text
core/python/tests/generic_callback_app_plugin.py
```

After the move, tests should load the plugin via path config:

```json
"path:${env:BUILTIN_PLUGINS}/generic-callback-app"
```

or a direct path entry where appropriate, rather than importing
`tests.generic_callback_app_plugin`.

### Plugin actions

The plugin should expose at least two actions.

#### `start_external_flow`

Purpose: generate a generic callback deep link and return a display payload with
a copy-link button.

Inputs:

```python
{
    "connection_id": {"type": "string", "required": True},
    "result": {"type": "string", "required": False},
    "nonce": {"type": "string", "required": False},
}
```

Execution context:

- `session_id` comes from the session-scoped route context.
- `connection_id` comes from action inputs, supplied by the frontend action caller.
- `result` can default to `"approved"`.
- `nonce` can default to a generated or deterministic test value.

Generated link:

```text
crystal-lattice://action/<connection-id>/<session-id>/complete_external_flow?result=approved&nonce=n-123
```

By default, the generated link should omit `plugin-id`. That is the point of the
feature: the callback-producing plugin and callback-executing plugin can be
decoupled.

Optionally, for exact-dispatch coverage, support a boolean or alternate action
that includes the plugin id:

```text
crystal-lattice://action/<connection-id>/<session-id>/generic_callback_app/complete_external_flow?result=approved&nonce=n-123
```

Display payload should follow the ChatGPT login plugin pattern:

```python
{
    "display": {
        "display_id": "generic-callback-flow",
        "title": "Generic Callback Link",
        "variant": "info",
        "markdown": "...",
        "actions": [
            {
                "kind": "copy_text",
                "id": "copy-generic-callback-link",
                "label": "Copy link",
                "text": callback_url,
                "copied_label": "Copied",
            }
        ],
    }
}
```

#### `complete_external_flow`

Purpose: receive the deep-link callback and echo what arrived.

Inputs:

```python
{
    "result": {"type": "string", "required": True},
    "nonce": {"type": "string", "required": False},
    "redirect_url": {"type": "string", "required": True},
}
```

Return shape:

```json
{
  "message": "Generic action complete",
  "handled": true,
  "action": "complete_external_flow",
  "inputs": {
    "result": "approved",
    "nonce": "n-123",
    "redirect_url": "..."
  },
  "context": {
    "session_id": "..."
  }
}
```

### Frontend action calling

To let `start_external_flow` generate a correct route, action execution needs
access to the active mobile connection id.

Add `connectionId` to the frontend action runner context:

```ts
export interface RunActionContext {
  sessionId?: string;
  connectionId?: string;
  ...
}
```

Then update mobile call sites that invoke `runApplicationAction` to pass their
current connection id.

Relevant call sites include session-list and chat/session action surfaces, where
the active connection id is already known through screen props or app state.

Expected context shape:

```ts
context: {
  ...existingContext,
  sessionId,
  connectionId,
}
```

Then the plugin UI/action definition can use existing action input mapping if
available, or a minimal generic mapping extension if needed:

```python
"params": {
    "connection_id": "$context.connection_id"
}
```

If the current action runner only maps session/message fields and not connection
id, extend it generically. Do not add plugin-specific frontend logic.

Important distinction:

- `connection_id` is an action input for `start_external_flow`, because the
  plugin needs it to generate a link.
- `connection_id` is not an input for `complete_external_flow`, because the
  callback route already uses connection id for frontend routing.

### UI element for starting the flow

The plugin should expose a session action UI element for `start_external_flow`.

Suggested shape:

```python
{
    "ui_type": "session_action",
    "id": "generic_callback_start_external_flow",
    "label": "Create callback link",
    "action_id": "start_external_flow",
    "params": {
        "connection_id": "$context.connection_id"
    }
}
```

Exact field names should follow existing action runner mapping conventions, but
the intent is that the frontend supplies the active connection id automatically.

### Test updates

#### Plugin unit tests

Add tests under:

```text
plugins/generic-callback-app/tests/
```

Assert:

- `start_external_flow` receives or requires `connection_id`.
- Given `connection_id="test-connection"` and context
  `session_id="session-123"`, it generates:

  ```text
  crystal-lattice://action/test-connection/session-123/complete_external_flow?...
  ```

- Display payload includes a copy action:
  - `kind == "copy_text"`
  - `id == "copy-generic-callback-link"`
  - `label == "Copy link"`
  - `text == generated callback URL`
  - `copied_label == "Copied"`
- `complete_external_flow` echoes `result`, `nonce`, `redirect_url`, and context
  session id.

#### Backend/app tests

Update current tests to load the plugin from `plugins/generic-callback-app`
instead of `core/python/tests/generic_callback_app_plugin.py`.

Add app-layer/server coverage for:

- calling `start_external_flow` through `/sessions/{session_id}/actions`
- passing `connection_id`
- receiving a display payload with the copy-link action
- parsing/executing the generated URL through omitted-plugin
  `complete_external_flow`

#### SDK integration test

Upgrade the current SDK integration from “manually build callback URL” to the
full flow:

1. Start real backend with `generic-callback-app`.
2. Create a session.
3. Call:

   ```ts
   backend.executeSessionAction({
     sessionId,
     pluginId: "generic_callback_app",
     actionId: "start_external_flow",
     inputs: {
       connection_id: "test-connection",
       result: "approved",
       nonce: "n-123",
     },
   })
   ```

4. Extract the copy-link action from `response.result.display.actions`.
5. Assert the copy action text is the expected deep link.
6. Parse the copied link with `parseActionDeepLink`.
7. Execute the parsed link with omitted plugin id:

   ```ts
   backend.executeSessionAction({
     sessionId: parsed.sessionId,
     pluginId: parsed.pluginId, // undefined
     actionId: parsed.actionId,
     inputs: parsed.inputs,
   })
   ```

8. Assert resolved plugin is `generic_callback_app` and completion result echoes
   inputs.

#### React Native integration test

Upgrade the RN integration similarly:

1. Start real backend with `generic-callback-app`.
2. Create a session.
3. Use `backend.executeSessionAction` or a rendered session action flow to invoke
   `start_external_flow` with `connection_id="test-connection"`.
4. Extract the copy-link text from the display result.
5. Pass that URL to:

   ```ts
   handleIncomingUrl(copiedUrl)
   ```

6. Assert handler routes to:
   - connection `test-connection`
   - the created session id
   - omitted plugin id
   - session-scoped backend action
7. Assert completion result is `Generic action complete`.

A fuller RN component test could later press the actual copy button, but this
integration should stay focused on `handleIncomingUrl(url)` and the generated
link payload first.

### Documentation updates

Update `plugins/docs/ui-elements.md` action deep-link section to mention:

- Plugins can return `copy_text` display actions containing
  `crystal-lattice://action/...` links.
- Link-generating actions need the frontend connection id.
- The frontend should pass connection id as action context/params when invoking
  link-generating session actions.
- Completion links should normally omit plugin id when the callback should be
  handled by whichever plugin currently provides the action.

Add `plugins/generic-callback-app/README.md` explaining this plugin is a
test/demo fixture for generic external callback flows.

### Migration from current work

Concrete changes from the current implementation:

- Delete `core/python/tests/generic_callback_app_plugin.py`.
- Add `plugins/generic-callback-app`.
- Update Python configs/tests:
  - replace `"tests.generic_callback_app_plugin.GenericCallbackAppPlugin"`
  - with a path plugin entry for `plugins/generic-callback-app`
- Update SDK integration config similarly.
- Update RN integration backend config similarly.
- Add `start_external_flow` and copy-link assertions.
- Extend action runner context to include `connectionId`.
- Update mobile `runApplicationAction` call sites to pass active connection id.

### Validation plan

After implementation, run:

```bash
pytest application/python/tests/test_application_actions_endpoints.py application/python/tests/test_provider_extension_session_actions_endpoints.py application/python/tests/test_feature_plugin_context_enrichment.py -q
pytest plugins/generic-callback-app/tests -q
npm --workspace @crystal-lattice/frontend-sdk test
cd packages/frontend-sdk && npx vitest run --config vitest.integration.config.ts src/integration/__tests__/actionDeepLinks.integration.test.ts
cd mobile/crystal-lattice-control-rn && npm run tsc
cd mobile/crystal-lattice-control-rn && npm test -- --runInBand
cd mobile/crystal-lattice-control-rn && npm run test:integration -- --runTestsByPath __integration__/actionDeepLinkRouting.realBackend.integration.test.ts
git diff --check
```

This validates the complete generic story: a plugin generates a copyable deep
link, the SDK/mobile parse and route it by connection/session, and the backend
resolves the omitted executing plugin id in the app layer.

### Follow-up implementation notes

Added during implementation.

- Moved the generic callback fixture to `plugins/generic-callback-app`.
- Added `start_external_flow`, which generates a
  `crystal-lattice://action/<connection>/<session>/complete_external_flow` URL
  and returns it in a `copy_text` display action.
- Kept `complete_external_flow` as the omitted-plugin callback target.
- Updated backend, SDK integration, and React Native integration tests to call
  `start_external_flow`, extract the generated copy-link text, then execute that
  generated URL through the deep-link parser/routing path.
- Added generic `$context.*` action input mapping and passed mobile
  `connectionId` through action contexts.
- Installed the new plugin package with
  `python -m pip install -e "plugins/generic-callback-app[dev]"`.
- Validation results for this follow-up:
  - Passed: `pytest plugins/generic-callback-app/tests -q`
  - Passed: `pytest application/python/tests/test_application_actions_endpoints.py application/python/tests/test_provider_extension_session_actions_endpoints.py application/python/tests/test_feature_plugin_context_enrichment.py -q`
  - Passed: `npm --workspace @crystal-lattice/frontend-sdk test`
  - Passed: `cd packages/frontend-sdk && npx vitest run --config vitest.integration.config.ts src/integration/__tests__/actionDeepLinks.integration.test.ts`
  - Passed: `cd mobile/crystal-lattice-control-rn && npm run tsc`
  - Passed: `cd mobile/crystal-lattice-control-rn && npm test -- --runInBand`
  - Passed: `cd mobile/crystal-lattice-control-rn && npm run test:integration -- --runTestsByPath __integration__/actionDeepLinkRouting.realBackend.integration.test.ts`
  - Passed: `npm --workspace @crystal-lattice/frontend-rn-components test`
  - Passed: `python -m black --check plugins/generic-callback-app/src/generic_callback_app plugins/generic-callback-app/tests application/python/tests/test_application_actions_endpoints.py`
  - Passed: `git diff --check`

## Execution plan

Added during completion.

- Update the SDK parser and tests to require `connectionId` and `sessionId` path segments, using only generic fixture names and query parameters.
- Move optional-plugin resolution into `AgentApplication` by adding a metadata-returning action execution API and making `execute_action` accept omitted plugin ids.
- Pass the session route id to the application layer as execution context from `/sessions/{session_id}/actions`, without injecting it into application action inputs.
- Allow `executeSessionAction` in the frontend SDK to omit `pluginId`, matching app-level action execution.
- Refactor mobile deep-link execution into a testable handler that routes by required connection id and always calls the session-scoped action endpoint.
- Add generic app/plugin fixtures and tests for app-layer/server resolution, SDK integration, and React Native handler routing.