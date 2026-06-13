# Session-Scoped Cloud Action Endpoint
Add a session-addressed action endpoint so session and message actions can route through connection-scoped cloud transports without depending on default-instance fallback.

## Requirements checklist

- [ ] Add a server endpoint for session-scoped actions using the session id in the URL.
- [ ] Keep the existing generic `POST /actions` endpoint for app-global actions and compatibility.
- [ ] Route mobile/frontend `session_action` and `message_action` calls through the new session endpoint.
- [ ] Preserve existing action execution semantics and response envelopes.
- [ ] Ensure cloud connection-scoped routing no longer sends session actions to the wrong instance when a connection has multiple instances.
- [ ] Add backend, frontend SDK, and cloud orchestrator regression coverage for the new flow.

Parent Task: `tasks/20260429-cloud-agent-orchestrator/000-main.md`

Depends On: `tasks/20260429-cloud-agent-orchestrator/0110-connection-scoped-cloud-routing.md`
Depends On: `tasks/20260429-cloud-agent-orchestrator/0113-connection-created-session-routing.md`

## Context

Today the frontend sends application actions to the generic endpoint:

```text
POST /actions
```

with a body like:

```json
{
  "plugin": "chatgpt_auth",
  "action_id": "check_status",
  "action_owner": "application",
  "inputs": {}
}
```

This works locally because the backend can execute the action directly after reading the request body.

It breaks for connection-scoped cloud links when an action request is proxied through:

```text
/connections/:connection_id/proxy/actions
```

because the orchestrator currently routes connection-scoped proxy traffic by:

- `session_id` in the URL path for `/sessions/:session_id/...`
- `session_id` in the query string for `/events?...`
- otherwise the connection `default_instance_id`

References:

- `cloud-orchestrator/lib/cloud_orchestrator/router.ex`
  - `resolve_connection_proxy_instance/3`
- `cloud-orchestrator/lib/cloud_orchestrator/connection_registry.ex`
  - `register_instance/2`
  - `default_instance/1`
- `packages/frontend-sdk/src/transport/cloudTransport.ts`
  - connection-scoped cloud links prefer `/connections/:connection_id/proxy/...`
- `packages/frontend-sdk/src/backend/restBackend.ts`
  - `executeAction(...)` always posts to `/actions`

This means session-scoped actions can be routed to the wrong cloud instance when a connection has multiple instances or when the connection default instance is stale. The observed symptom is that session actions such as ChatGPT login status or session title changes fail from the mobile cloud client even though the target runtime handles the same action successfully when called directly.

The clean API fix is to make session-scoped actions use a session-addressed endpoint:

```text
POST /sessions/:session_id/actions
```

That puts the routing key in the URL where the cloud orchestrator already knows how to route by session.

## Proposed API Shape

Keep the existing generic endpoint:

```text
POST /actions
```

Add a session-scoped endpoint:

```text
POST /sessions/:session_id/actions
```

Use the same body shape for both:

```json
{
  "plugin": "session_title",
  "action_id": "set_session_title",
  "action_owner": "application",
  "inputs": {
    "title": "New title"
  }
}
```

Server behavior for `POST /sessions/:session_id/actions`:

- execute through the same underlying application action path as `POST /actions`
- preserve the same response envelope shape
- inject `inputs.session_id = :session_id` when absent
- reject mismatches if the body already contains `inputs.session_id` with a different value

Frontend behavior:

- `session_action` uses `POST /sessions/:session_id/actions`
- `message_action` uses `POST /sessions/:session_id/actions`
- app-global actions continue to use `POST /actions`

This keeps session scoping explicit without changing the plugin contract for existing action handlers.

## Acceptance Criteria

- Session-scoped actions from cloud mobile clients succeed against the correct runtime instance even when the connection contains multiple instances.
- Generic app-global actions continue to work through `POST /actions`.
- Existing local non-cloud behavior remains unchanged.
- The session-scoped endpoint returns the same success/error envelope structure used by the current action endpoint.
- Cloud routing for session actions no longer depends on `default_instance_id`.

## Execution plan

Added during planning after investigating cloud action failures on a connection-scoped mobile cloud link.

1. Add a backend session-scoped action endpoint.

   In `application/python/agent_terminal_app/server.py`:

   - add `POST /sessions/{session_id}/actions`
   - parse the same payload currently accepted by `POST /actions`
   - merge or validate `inputs.session_id`
   - delegate to the same internal execution helper used by `POST /actions`

   Prefer a small shared helper so the validation, idempotency, and response-envelope logic stay aligned between the two endpoints.

2. Add frontend SDK support for session-scoped action execution.

   In `packages/frontend-sdk/src/backend/restBackend.ts`:

   - keep `executeAction(...)` for generic actions
   - add a session-scoped variant such as `executeSessionAction(...)`
   - post to `/sessions/${encodeURIComponent(sessionId)}/actions`
   - preserve `action_owner`, `inputs`, and idempotency behavior

3. Update the shared action runner to use the session endpoint for session/message surfaces.

   In `packages/frontend-sdk/src/plugins/actionRunner.ts`:

   - when the action element is `session_action` or `message_action`, require `context.sessionId`
   - call the session-scoped backend method
   - keep `POST /actions` for non-session-scoped action surfaces

   This keeps the policy centralized instead of duplicating routing choices in mobile screens.

4. Keep the mobile UI wiring thin.

   `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx` and
   `mobile/crystal-lattice-control-rn/src/SessionsScreen.tsx`
   should continue calling the shared action runner. They should not need special cloud-only handling once the SDK routes by session surface correctly.

5. Add backend tests.

   In `application/python/tests`:

   - test `POST /sessions/{session_id}/actions` success for a session action
   - test injected `session_id` when absent
   - test mismatch rejection when body `inputs.session_id` conflicts with URL `session_id`
   - test response envelope parity with `POST /actions`

6. Add frontend SDK tests.

   In `packages/frontend-sdk/src/plugins/__tests__/actionRunner.test.ts` and/or backend transport tests:

   - verify `session_action` uses `/sessions/:session_id/actions`
   - verify `message_action` uses `/sessions/:session_id/actions`
   - verify non-session-scoped actions still use `/actions`

7. Add cloud regression coverage.

   In `packages/frontend-sdk/src/integration/__tests__/cloud-orchestrator.e2e.integration.test.ts`:

   - create or reuse a shared-connection scenario with two cloud instances on one connection
   - run a session action against one session
   - assert the action mutates only the correct session/runtime

   A practical scenario is a title-change action or another deterministic session action that does not require model-provider success.

8. Verification.

   Focused commands:

   ```bash
   pytest application/python/tests/test_application_actions_endpoints.py -q
   npm test -- packages/frontend-sdk/src/plugins/__tests__/actionRunner.test.ts
   RUN_CLOUD_ORCHESTRATOR_E2E=1 npm test -- packages/frontend-sdk/src/integration/__tests__/cloud-orchestrator.e2e.integration.test.ts
   ```

## Notes

- This task intentionally avoids making the orchestrator parse action request bodies for routing.
- It also avoids cloud-only proxy heuristics in the client for action routing.
- The session-scoped endpoint is additive, so current generic action consumers can migrate incrementally.