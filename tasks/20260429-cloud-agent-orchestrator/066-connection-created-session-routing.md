# Connection-Created Session Routing
Register sessions created through a connection-scoped cloud transport so they route correctly and appear in connection session lists.

## Requirements checklist

- [x] Make connection proxy handling register sessions returned by proxied `POST /sessions`.
- [x] Ensure the registered route maps the new cloud-created `session_id` to the selected runtime instance.
- [x] Update connection `/sessions` aggregation to include cloud-created sessions.
- [x] Add or update e2e coverage so `cloudBackend.createSession()` followed by `cloudBackend.listSessions()` returns the new session.

Parent Task: `tasks/20260429-cloud-agent-orchestrator/000-main.md`

Depends On: `tasks/20260429-cloud-agent-orchestrator/062-clean-up-e2e-test-realism.md`
Depends On: `tasks/20260429-cloud-agent-orchestrator/060-connection-scoped-cloud-routing.md`

## Context

`packages/frontend-sdk/src/integration/__tests__/cloud-orchestrator.e2e.integration.test.ts:1009-1017` creates a new session through `CloudTransport`. Today that request works because `cloud-orchestrator/lib/cloud_orchestrator/router.ex:207-215` falls back to the connection default instance when no route exists. However, `cloud-orchestrator/lib/cloud_orchestrator/connection_registry.ex:244-262` filters aggregated sessions to registered route-table session IDs, so a cloud-created session may be missing from `GET /sessions`.

The product behavior should be: if a client creates a session through a connection-scoped transport, that session becomes part of that connection and is routable/listable through the same connection.

## Execution plan

Added during planning. Do not implement as part of this note.

Use a focused routing fix: make session creation through a connection-scoped proxy register a real route instead of relying on default-instance fallback.

1. Add a route-registration API to `CloudOrchestrator.ConnectionRegistry`.

   Add a public function like:

   ```elixir
   register_route(connection_id, session_id, instance_id)
   ```

   Expected behavior:

   - Validate `connection_id` exists.
   - Validate `instance_id` belongs to that connection's `instance_ids`.
   - Validate `session_id` is a non-empty binary.
   - Register `{connection_id, session_id} -> instance_id` in the route table.
   - Return `:ok` or `{:ok, public_connection}`.

2. Refactor proxy forwarding so connection proxy can inspect `POST /sessions` responses.

   Today `InstanceRegistry.handle_proxy_request/3` and `Proxy.forward/3` send the proxied response directly to the client. For `POST /connections/:connection_id/proxy/sessions`, the orchestrator needs to inspect the successful runtime response before sending it onward.

   Suggested shape:

   - Add `CloudOrchestrator.Proxy.forward_result(conn, instance, path)` returning:

     ```elixir
     {:ok, %{status: status, headers: headers, body: body}}
     {:error, reason}
     ```

   - Keep existing `Proxy.forward/3` as a wrapper around `forward_result/3` so legacy instance proxy behavior remains unchanged.
   - Add a small helper to send the returned proxy response back to the client without changing the body.

3. Register cloud-created sessions in the connection proxy route.

   In `cloud-orchestrator/lib/cloud_orchestrator/router.ex`:

   - Detect `POST /connections/:connection_id/proxy/sessions`.
   - Select the default/target instance using existing connection routing rules.
   - Proxy the request with `Proxy.forward_result/3`.
   - If the runtime returns a 2xx response, decode the JSON body and extract:

     ```text
     session.session_id
     ```

     Optionally also accept a top-level `session_id` for compatibility.

   - Call `ConnectionRegistry.register_route(connection_id, session_id, instance["instance_id"])`.
   - Send the original runtime response unchanged.

4. Revisit default-instance fallback for unknown session IDs.

   Keep default-instance routing for non-session-specific paths such as `/agents`, `/api/data`, `/application/actions`, and `/application/ui-schema`.

   For session-specific paths with no registered route, prefer returning `404 route_not_found` after `POST /sessions` registration exists. If compatibility requires keeping fallback, add a test that documents it explicitly so it does not hide missing route registration again.

5. Tests.

   Add/update Elixir tests:

   - A router/registry test where proxied `POST /connections/:connection_id/proxy/sessions` returns a realistic runtime payload and registers the returned `session_id`.
   - A test that `ConnectionRegistry.resolve_route(connection_id, new_session_id)` resolves to the selected instance.
   - A test that proxied `GET /sessions` or `ConnectionRegistry.list_sessions(connection_id)` includes the cloud-created session.
   - Preserve tests for existing local-session route registration and legacy `/instances/:instance_id/proxy` compatibility.

   Add/update frontend e2e:

   - In `packages/frontend-sdk/src/integration/__tests__/cloud-orchestrator.e2e.integration.test.ts`, after `cloudBackend.createSession({ agentId: "default" })`, assert that `cloudBackend.listSessions()` includes the returned session ID.
   - Continue sending a message to that session to prove subsequent session-specific routing uses the route table.

6. Verification.

   Required focused commands:

   ```bash
   cd cloud-orchestrator && mix test
   cd packages/frontend-sdk && RUN_CLOUD_ORCHESTRATOR_E2E=1 RUN_CLOUD_ORCHESTRATOR_OPENROUTER_E2E=1 npm test -- cloud-orchestrator.e2e.integration.test.ts -t "runs local and cloud OpenRouter tool calls"
   ```

   If broader gated tests are requested, run them with the documented gates and dotenv-sourced credentials. Treat failures from known follow-up tasks such as `065` and `067` as real exposed issues, not reasons to weaken this test.

## Revised execution plan

Added during completion after code investigation and approved by the user.

- [x] Add `ConnectionRegistry.register_route/3` for registering a non-empty `session_id` to an instance already attached to the connection.
- [x] Add an inspectable proxy result path while preserving existing Plug response forwarding for legacy instance proxy routes.
- [x] Special-case `POST /connections/:connection_id/proxy/sessions` so successful runtime session creation registers the returned `session.session_id` or top-level `session_id` to the selected instance, then sends the original runtime response unchanged.
- [x] Keep existing default-instance fallback behavior for this task; do not harden unknown session-specific routes here.
- [x] Add focused Elixir coverage for route registration, connection-created session proxy routing, and connection session aggregation.
- [x] Update or confirm frontend SDK e2e expectations so cloud-created sessions are listed after `cloudBackend.createSession()`.
- [x] Before running gated integration/e2e tests, check whether they depend on follow-up tasks `065` and `067`; defer if they require unfinished follow-up work.

## Completion Notes

Added during completion.

- Added `ConnectionRegistry.register_route/3` and validation so connection-scoped proxy code can register cloud-created session IDs to an existing connection instance.
- Added result-returning proxy plumbing through `Proxy.forward_result/3`, `InstanceRegistry.handle_proxy_request_result/3`, and runner callbacks while preserving existing response-sending proxy behavior.
- Updated connection proxy routing so `POST /connections/:connection_id/proxy/sessions` forwards to the selected instance, extracts `session.session_id` or top-level `session_id` from successful runtime responses, registers the route, and returns the original runtime response unchanged.
- Kept existing default-instance fallback behavior for unknown session-specific routes; route hardening is intentionally outside this task.
- Added Elixir coverage for route registration, connection-created session proxy routing, and connection session aggregation filtering.
- Updated frontend e2e assertions so `cloudBackend.createSession()` is followed immediately by `cloudBackend.listSessions()` checking the created session ID.
- Verification:
  - `mix test test/cloud_orchestrator/registry_test.exs test/cloud_orchestrator/router_test.exs`
  - `mix test`
  - `RUN_CLOUD_ORCHESTRATOR_E2E=1 npm test -- src/integration/__tests__/cloud-orchestrator.e2e.integration.test.ts -t "opens a cloud session through CloudTransport and syncs workspace files back down"` from `packages/frontend-sdk`
  - `env -u OPENROUTER_API_KEY RUN_CLOUD_ORCHESTRATOR_E2E=1 RUN_CLOUD_ORCHESTRATOR_OPENROUTER_E2E=1 npm test -- src/integration/__tests__/cloud-orchestrator.e2e.integration.test.ts -t "runs local and cloud OpenRouter tool calls"` from `packages/frontend-sdk`
- E2E dependency check:
  - Task `065` is complete.
  - Local-mode cloud e2e does not require task `067`; it was run and passed.
  - AWS CloudFront/external transfer e2e still depends on task `067` because managed SSH transfer public host configuration is not yet productized.
  - The TypeScript cloud orchestrator e2e gates are flag-only; provider credentials are resolved by the backend application dotenv path. The OpenRouter test was verified with `OPENROUTER_API_KEY` unset in the Node process and root `.env` discovered from the current directory/parents.

Additional verification after dependent follow-up tasks were reported complete:

- Passed:
  - `mix test` from `cloud-orchestrator`
  - `PYTHONPATH=plugins/cloud-agent-app/src pytest plugins/cloud-agent-app/tests/test_cloud_agent_app_plugin.py -q`
  - `pytest application/python/tests/test_cloud_runtime_workdir.py -q`
  - `RUN_CLOUD_ORCHESTRATOR_E2E=1 npm test -- src/integration/__tests__/cloud-orchestrator.e2e.integration.test.ts -t "routes two cloud sessions through one connection-scoped CloudTransport"` from `packages/frontend-sdk`
- Previously failed, then rerun and passed:
  - `env -u OPENROUTER_API_KEY -u OPENAI_API_KEY RUN_CLOUD_ORCHESTRATOR_E2E=1 RUN_CLOUD_ORCHESTRATOR_CODEX_DEFAULT_CONFIG_E2E=1 npm test -- src/integration/__tests__/cloud-orchestrator.e2e.integration.test.ts -t "runs local-cloud-local bash and apply_patch chain with codex-openrouter"` initially timed out waiting for cloud `chain.txt`, then passed on rerun.
  - `env -u OPENROUTER_API_KEY -u OPENAI_API_KEY RUN_CLOUD_ORCHESTRATOR_E2E=1 RUN_CLOUD_ORCHESTRATOR_CODEX_DEFAULT_CONFIG_E2E=1 npm test -- src/integration/__tests__/cloud-orchestrator.e2e.integration.test.ts -t "runs local-cloud-local bash and apply_patch chain with codex-openai"` initially timed out waiting for cloud `chain.txt`, then passed on rerun.
- Not run:
  - AWS EC2/CloudFront e2e was initially deferred because `--profile secure` was mistaken for an AWS CLI profile. It is actually the orchestrator deploy profile/state suffix; AWS commands use the default credential chain plus `--region`.
- AWS EC2/CloudFront verification after correcting the deploy profile interpretation:
  - `RUN_AWS_CLOUD_ORCHESTRATOR_TESTS=1 ./deploy/aws-ec2/build.sh --profile secure --stack-name crystal-lattice-cloud-orchestrator-e2e-manual-066 --region us-east-1 --json` from `cloud-orchestrator` passed and built the orchestrator/runtime/transfer SSH images.
  - `env RUN_AWS_CLOUD_ORCHESTRATOR_TESTS=1 AWS_STACK_NAME=crystal-lattice-cloud-orchestrator-e2e-manual-066 CLOUD_ORCHESTRATOR_E2E_MODE=aws-ec2-cloudfront RUN_CLOUD_ORCHESTRATOR_E2E=1 npm test -- src/integration/__tests__/cloud-orchestrator.e2e.integration.test.ts -t "opens a cloud session through CloudTransport and syncs workspace files back down"` from `packages/frontend-sdk` passed.