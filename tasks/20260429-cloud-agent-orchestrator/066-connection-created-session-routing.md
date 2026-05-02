# Connection-Created Session Routing
Register sessions created through a connection-scoped cloud transport so they route correctly and appear in connection session lists.

## Requirements checklist

- [ ] Make connection proxy handling register sessions returned by proxied `POST /sessions`.
- [ ] Ensure the registered route maps the new cloud-created `session_id` to the selected runtime instance.
- [ ] Update connection `/sessions` aggregation to include cloud-created sessions.
- [ ] Add or update e2e coverage so `cloudBackend.createSession()` followed by `cloudBackend.listSessions()` returns the new session.

Parent Task: `tasks/20260429-cloud-agent-orchestrator/000-main.md`

Depends On: `tasks/20260429-cloud-agent-orchestrator/062-clean-up-e2e-test-realism.md`
Depends On: `tasks/20260429-cloud-agent-orchestrator/060-connection-scoped-cloud-routing.md`

## Context

`packages/frontend-sdk/src/integration/__tests__/cloud-orchestrator.e2e.integration.test.ts:1009-1017` creates a new session through `CloudTransport`. Today that request works because `cloud-orchestrator/lib/cloud_orchestrator/router.ex:207-215` falls back to the connection default instance when no route exists. However, `cloud-orchestrator/lib/cloud_orchestrator/connection_registry.ex:244-262` filters aggregated sessions to registered route-table session IDs, so a cloud-created session may be missing from `GET /sessions`.

The product behavior should be: if a client creates a session through a connection-scoped transport, that session becomes part of that connection and is routable/listable through the same connection.