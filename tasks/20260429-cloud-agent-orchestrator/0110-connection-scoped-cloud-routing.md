# Connection-Scoped Cloud Routing
Introduce a first-class cloud connection model so one UI cloud connection can route to one or more cloud agent instances, while preserving the current one-session-per-instance behavior as a compatible default.

## Requirements checklist

- [x] Add an orchestrator-level connection concept with opaque plugin-provided grouping keys.
- [x] Add orchestrator routing from `(connection_id, session_id)` to `instance_id`.
- [x] Keep runner ownership focused on concrete runtime/container execution for a selected instance.
- [x] Preserve existing instance-scoped behavior and proxy routes during migration.
- [x] Update the cloud plugin to choose/reuse connection keys without hardcoding server-id semantics into the orchestrator.
- [x] Update frontend cloud connection records/transports to connect to a connection rather than one fixed instance.
- [x] Add tests for current, shared-connection/multi-instance, and route lookup behavior.

Parent Task: `tasks/20260429-cloud-agent-orchestrator/000-main.md`

## Background

The current cloud implementation treats the public UI connection as a single orchestrator instance. The plugin starts one instance for one local session, emits a link containing `instance_id`, and the frontend cloud transport sends every request to `/instances/:instance_id/proxy/...`.

That supports:

```text
session1 => connection1, instance1
session2 => connection2, instance2
```

The next target should also support:

```text
session1 => connection1, instance1
session2 => connection1, instance2
```

And the future Docker runner optimization should be representable without another orchestrator redesign:

```text
session1 => connection1, instance1
session2 => connection1, instance1
session3 => connection1, instance2
```

After comparing options, the simplest maintainable direction is for the orchestrator to own generic connection/session/instance routing, while the plugin chooses the opaque connection grouping policy and the runner continues to execute concrete runtime instances.

## Current Implementation Notes

Current ownership:

- The cloud plugin packages the workspace/session/config, creates transfers, starts an orchestrator instance, builds the cloud link, and stores `session.metadata.cloud_agent`.
- The orchestrator owns in-memory transfer and instance registries.
- The Docker runner starts/stops/probes/proxies one selected runtime container.
- The runtime container owns an isolated `AgentApplication` and session store for that instance.
- The frontend `CloudTransport` is fixed to one `instanceId`.

Important current references:

- `cloud-orchestrator/lib/cloud_orchestrator/router.ex`
  - `POST /instances` starts an instance.
  - `GET /instances/:instance_id`, export, close, and proxy are instance-scoped.
  - `/instances/:instance_id/proxy/*path` authorizes a token whose claims include the same `instance_id`.
- `cloud-orchestrator/lib/cloud_orchestrator/instance_registry.ex`
  - `InstanceRegistry` stores an in-memory `%{instance_id => instance_map}`.
  - It creates `instance_id`, stores `session_id`, signs instance-scoped tokens, monitors readiness, and delegates concrete work to the runner.
- `cloud-orchestrator/lib/cloud_orchestrator/runner.ex`
  - Runner callbacks are currently instance-oriented: `start_instance`, `runtime_status`, `export_instance`, `close_instance`, and `handle_proxy_request`.
- `cloud-orchestrator/lib/cloud_orchestrator/runner/docker.ex`
  - Docker runner creates per-instance directories, starts one runtime container, records `container_id`/`proxy_base_url`, and forwards selected-instance requests.
- `cloud-orchestrator/runtime/python/runtime.py`
  - Runtime materializes one transferred session/config/workspace into its isolated session dir and starts a normal `AgentApplication`.
- `plugins/cloud-agent-app/src/cloud_agent_app/cloud_agent_app_plugin.py`
  - `_start_session_agent` currently posts only `session_id` and `transfer_ref` to `/instances`.
  - `_cloud_agent_metadata` currently stores `instance_id`, `session_id`, `token`, status, and connection link under `session.metadata.cloud_agent`.
- `packages/frontend-sdk/src/transport/cloudTransport.ts`
  - `CloudConnectionLink` currently requires `instanceId`.
  - Requests go to `/instances/:instance_id/proxy/...`.

## Proposed Design

Add first-class orchestrator concepts:

```text
Connection
  connection_id
  optional opaque connection_key / metadata chosen by plugin
  token / state / created_at / updated_at
  default_instance_id

Instance
  instance_id
  connection_id
  state / startup fields
  transfer_ref
  runner fields

Route
  connection_id
  session_id
  instance_id
```

The orchestrator may understand `session_id` as part of the agent API routing model. This is acceptable because the orchestrator is already an agent orchestrator and the frontend/server API is session-shaped.

The orchestrator should not hardcode what a connection key means. The plugin can choose:

- a unique connection per start, matching current behavior
- a stable local-server key, giving one cloud connection per local server
- another grouping later, such as workspace/project/user

## API Shape

Keep existing instance-scoped routes for compatibility:

```text
POST /instances
GET /instances/:instance_id
POST /instances/:instance_id/export
POST /instances/:instance_id/close
ANY /instances/:instance_id/proxy/*
```

Add connection-scoped routes:

```text
POST /connections
GET /connections/:connection_id
ANY /connections/:connection_id/proxy/*
GET /connections/:connection_id/sessions
```

Instance creation can either be explicit or implicit through an extended `POST /instances`:

```json
{
  "connection_ref": {
    "connection_id": "optional-existing-id",
    "connection_key": "plugin-owned-opaque-key",
    "reuse": true
  },
  "session_id": "local-session-id",
  "transfer_ref": {"transfer_id": "tr_..."}
}
```

The orchestrator resolves or creates a connection, starts a new instance through the current runner, and registers:

```text
(connection_id, session_id) -> instance_id
```

## Routing Rules

For connection proxy requests, the orchestrator should parse session IDs from known API shapes:

```text
/sessions/:session_id/...
/events?session_id=...
```

Then it resolves:

```text
(connection_id, session_id) -> instance_id
```

and delegates to the existing runner proxy path for that selected instance.

For non-session-specific endpoints:

```text
/api/data
/agents
/application/actions
/application/ui-schema
```

use `default_instance_id` or the first running instance in the connection. Keep this behavior explicit and tested.

For `GET /sessions`, the orchestrator should aggregate across instances in the connection. A simple implementation can query each running instance's `/sessions` endpoint and merge summaries, filtering to sessions registered in the connection route table.

## Frontend/Plugin Changes

Frontend:

- Extend cloud connection links to support connection-scoped links:

```text
crystal-lattice-cloud://connect?orchestrator=...&connection_id=...&token=...
```

- Keep old instance-scoped links during migration.
- Update `CloudConnectionRecord` to store `connectionId` and token as the primary identity, with optional `initialSessionId`/`initialInstanceId` hints.
- Add/update `CloudTransport` to use `/connections/:connection_id/proxy/...`.

Plugin:

- Choose an opaque connection key based on config/policy.
- For the immediate desired behavior, use a stable local-server key so multiple sessions from the same local server share one cloud connection.
- Store both connection and instance metadata under `session.metadata.cloud_agent`.
- Keep lifecycle actions (`check`, `sync`, `close`) session/instance-aware because sync/export/close still target concrete instances.

Runner:

- Keep the current instance-oriented callback model for the first implementation.
- Future runner work can add "attach session to existing instance" while leaving the orchestrator route model intact.

## Acceptance Criteria

- Current one-session-per-cloud-connection flow still works.
- New flow can start two cloud sessions that share one `connection_id` but use separate `instance_id` values.
- A connection-scoped frontend transport can list sessions across all instances in that connection.
- Session-specific chat/message/event requests route to the correct instance.
- Existing instance-scoped links/routes continue to work during migration.
- Tests cover route registration, connection token auth, session route lookup, `/sessions` aggregation, and compatibility with old instance-scoped proxy.

## Notes

This task intentionally chooses the simpler orchestrator-owned route table rather than making the runner own all connection/session routing. The runner remains the concrete runtime executor. The plugin controls grouping policy through opaque connection keys, so the orchestrator does not hardcode server-id semantics.

## Execution plan

Added during completion planning after reviewing the current orchestrator, cloud plugin, frontend SDK, mobile app, and existing cloud orchestrator e2e tests.

Use staged checkpoints because this change crosses the Elixir orchestrator, Python cloud plugin, TypeScript frontend SDK, mobile saved connection records, and integration/e2e coverage.

1. Add a first-class `CloudOrchestrator.ConnectionRegistry`.

   Create a new GenServer started by `CloudOrchestrator.Application` alongside `InstanceRegistry`. It should maintain:

   ```elixir
   %{
     connections: %{connection_id => connection},
     keys: %{connection_key => connection_id},
     routes: %{{connection_id, session_id} => instance_id}
   }
   ```

   Public API should cover creating/reusing connections, looking up a connection, starting an instance for a connection, resolving `(connection_id, session_id) -> instance_id`, selecting a default instance, listing connection instances, closing instances with route cleanup, and resetting test state.

   `start_instance/1` should resolve or create the connection from `connection_ref`, call `InstanceRegistry.start_instance/1` with `connection_id`, then register the route. Keep the runner callback model instance-oriented.

2. Extend `InstanceRegistry` only where it remains the instance authority.

   Add `connection_id` to stored/public instances when supplied. New instance tokens should include both `instance_id` and `connection_id` when available:

   ```elixir
   %{
     "instance_id" => instance_id,
     "connection_id" => connection_id,
     "session_id" => session_id
   }
   ```

   Keep existing instance-scoped behavior and proxy authorization working for legacy clients.

3. Add connection routes to `CloudOrchestrator.Router`.

   Preserve existing instance routes:

   ```text
   POST /instances
   GET /instances/:instance_id
   POST /instances/:instance_id/export
   POST /instances/:instance_id/close
   ANY /instances/:instance_id/proxy/*
   ```

   Add:

   ```text
   POST /connections
   GET /connections/:connection_id
   GET /connections/:connection_id/sessions
   ANY /connections/:connection_id/proxy/*
   ```

   Route behavior:

   - `POST /connections` uses control auth and supports `connection_key`, `metadata`, and `reuse`.
   - Extended `POST /instances` delegates to `ConnectionRegistry.start_instance/1`.
   - Without `connection_ref`, `POST /instances` should create a unique connection so current one-session-per-instance behavior remains compatible.
   - `/connections/:connection_id/proxy/*path` authorizes tokens with a matching `connection_id`.
   - For `/sessions/:session_id/...`, parse the session ID from the proxied path and route to the registered instance.
   - For `/events?session_id=...`, parse the session ID from the query string.
   - For non-session-specific paths such as `/api/data`, `/agents`, `/application/actions`, and `/application/ui-schema`, use `default_instance_id` or the first running instance.

4. Implement connection session aggregation.

   For `GET /connections/:connection_id/sessions` and proxied `GET /sessions`, query running instances in the connection, merge their `/sessions` responses, and filter to sessions registered in the connection route table. Prefer explicit errors over silent partial results for the first implementation unless tests show the UI needs partial success.

5. Update the cloud plugin.

   Add a helper to choose an opaque connection key:

   - Use `application.cloud_agent.connection_key` when configured.
   - Otherwise derive a stable opaque key from local control-plane context, such as resolved config path and workspace path, without exposing server-id semantics to the orchestrator.

   Start instances with:

   ```json
   {
     "connection_ref": {
       "connection_key": "...",
       "reuse": true,
       "metadata": {"source": "cloud-agent-app"}
     },
     "session_id": "...",
     "transfer_ref": {"transfer_id": "..."}
   }
   ```

   Store `connection_id`, `instance_id`, `session_id`, token, and connection link under `session.metadata.cloud_agent`. Keep check/sync/export/close session and instance-aware because lifecycle operations still target concrete instances.

6. Update frontend SDK cloud links and transport.

   Change `CloudConnectionLink` to accept either modern `connectionId` or legacy `instanceId`.

   Parser/formatter rules:

   - New links use `connection_id`, `token`, optional `session_id`, and optional `instance_id`.
   - Old links with `instance_id`, `session_id`, and `token` must continue to parse.
   - Require at least one of `connection_id` or `instance_id`.

   Update `CloudTransport` to accept `connectionId?: string` and `instanceId?: string`. Prefer `/connections/:connection_id/proxy/...` when `connectionId` exists and fall back to `/instances/:instance_id/proxy/...`.

7. Update saved cloud connection records and mobile wiring.

   Make cloud records connection-primary while preserving old saved records:

   ```ts
   connectionId?: string;
   instanceId?: string;
   initialSessionId?: string;
   sessionId?: string;
   token: string;
   ```

   Mobile should store `connectionId` when present, pass it into `CloudTransport`, and continue reopening legacy instance-scoped cloud records.

8. Add and update tests.

   Unit and focused tests:

   - Elixir registry tests for creating/reusing connection keys and registering two sessions to one connection with two instances.
   - Elixir router tests for connection token auth, session route lookup, default route lookup, `/connections/:connection_id/sessions`, proxied `GET /sessions`, and legacy `/instances/:instance_id/proxy`.
   - Python plugin tests for `connection_ref`, connection metadata, and connection-scoped links.
   - Frontend SDK tests for new and old cloud link parsing, formatting, and transport URL selection.

   Existing integration/e2e tests must also be updated:

   - Update `packages/frontend-sdk/src/integration/__tests__/cloud-orchestrator.e2e.integration.test.ts` so current scenarios use connection-scoped links/transports where available.
   - Update helpers such as `waitForCloudInstanceRunning` to handle modern links with `connectionId` plus an instance hint, while still supporting old `instanceId`.
   - Keep sync/close action inputs instance-scoped.
   - Assert generated links include `connection_id` while preserving enough instance/session hints for lifecycle and initial navigation.

   Add a new integration/e2e scenario in the same cloud orchestrator e2e file:

   - Start one local backend and orchestrator.
   - Create two local sessions.
   - Run `cloud.start_session_agent` for both sessions.
   - Assert both links share the same `connectionId` and have different instance IDs or instance hints.
   - Create one connection-scoped `CloudTransport`.
   - Verify `cloudBackend.listSessions()` returns both session IDs through the shared connection.
   - Verify session-specific message/event requests for each session route to the correct runtime/session.
   - Optionally probe `/connections/:connection_id` directly for route/debug metadata.

9. Update docs and run verification.

   Update cloud README/application README examples to show connection-scoped links and note that old instance links still work during migration.

   Required verification commands:

   ```bash
   cd cloud-orchestrator && mix test
   pytest plugins/cloud-agent-app/tests/test_cloud_agent_app_plugin.py -q
   cd packages/frontend-sdk && npm test -- cloudTransport
   cd packages/frontend-sdk && RUN_CLOUD_ORCHESTRATOR_E2E=1 npm test -- cloud-orchestrator.e2e.integration.test.ts
   cd mobile/crystal-lattice-control-rn && npm run tsc
   ```

   If AWS/OpenRouter environment variables are available, ensure the updated cloud e2e paths remain compatible with those modes as well. Local Docker orchestrator e2e is the required integration verification for this task.

## Completion Notes

Added during completion after implementation.

- Added `CloudOrchestrator.ConnectionRegistry` for connection records, opaque `connection_key` reuse, route registration, default-instance lookup, close cleanup, and connection session aggregation.
- Extended instance creation to attach `connection_id` and sign tokens that support both legacy instance proxy authorization and new connection proxy authorization.
- Added `/connections`, `/connections/:connection_id`, `/connections/:connection_id/sessions`, and `/connections/:connection_id/proxy/*path` while preserving the existing `/instances` API.
- Updated the cloud plugin to send `connection_ref`, derive an opaque stable connection key, store `connection_id`, and emit connection-scoped links with instance/session hints for migration.
- Updated `CloudTransport`, cloud link parsing/formatting, saved cloud connection records, and mobile cloud connection creation to prefer `connectionId` while preserving legacy `instanceId` links/records.
- Updated existing cloud orchestrator e2e coverage to use connection-scoped transports and added a shared-connection/two-instance e2e scenario.
- Updated AWS EC2 e2e support so CloudFront remains the orchestrator HTTP endpoint while managed SSH transfers use the EC2 origin host.
- Opened the AWS EC2 managed transfer port range (`22000-22099`) in the secure-origin template and documented it.
- Updated the managed-SSH rsync adapter to exclude its own key and known-hosts helper files from upload/download payloads.
- Updated docs in `cloud-orchestrator/README.md` and `application/python/README.md`.

Verification completed:

```bash
cd cloud-orchestrator && mix format && mix test
PYTHONPATH=plugins/cloud-agent-app/src pytest plugins/cloud-agent-app/tests/test_cloud_agent_app_plugin.py -q
cd packages/frontend-sdk && npm test -- cloudTransport
cd packages/frontend-sdk && npm test -- cloud-orchestrator.e2e.integration.test.ts
cd packages/frontend-sdk && RUN_CLOUD_ORCHESTRATOR_E2E=1 npm test -- cloud-orchestrator.e2e.integration.test.ts
cd packages/frontend-sdk && RUN_CLOUD_ORCHESTRATOR_E2E=1 RUN_CLOUD_ORCHESTRATOR_OPENROUTER_E2E=1 RUN_CLOUD_ORCHESTRATOR_CODEX_DEFAULT_CONFIG_E2E=1 npm test -- cloud-orchestrator.e2e.integration.test.ts
cd cloud-orchestrator && ALLOW_AWS_DEPLOY=1 RUN_AWS_CLOUD_ORCHESTRATOR_TESTS=1 deploy/aws-ec2/build.sh --profile secure --stack-name crystal-lattice-cloud-orchestrator-e2e-codex-routing --region us-east-1 --builder codebuild --json
cd packages/frontend-sdk && RUN_CLOUD_ORCHESTRATOR_E2E=1 RUN_AWS_CLOUD_ORCHESTRATOR_TESTS=1 CLOUD_ORCHESTRATOR_E2E_MODE=aws-ec2-cloudfront RUN_CLOUD_ORCHESTRATOR_CODEX_DEFAULT_CONFIG_EC2_E2E=1 AWS_STACK_NAME=crystal-lattice-cloud-orchestrator-e2e-codex-routing npm test -- cloud-orchestrator.e2e.integration.test.ts -t "runs EC2 local-cloud-local bash and apply_patch chain"
cd packages/frontend-sdk && RUN_CLOUD_ORCHESTRATOR_E2E=1 RUN_AWS_CLOUD_ORCHESTRATOR_TESTS=1 CLOUD_ORCHESTRATOR_E2E_MODE=aws-ec2-cloudfront RUN_CLOUD_ORCHESTRATOR_CODEX_DEFAULT_CONFIG_EC2_E2E=1 AWS_STACK_NAME=crystal-lattice-cloud-orchestrator-e2e-codex-routing npm test -- cloud-orchestrator.e2e.integration.test.ts -t "runs EC2 local-cloud-local bash and apply_patch chain with codex-openai"
```

`cd mobile/crystal-lattice-control-rn && npm run tsc` was also run, but it failed on pre-existing unrelated TypeScript errors in `restBackend`, theme/style fields, and plugin settings styles before surfacing any cloud connection record issue.

Additional verification notes:

- The local provider-gated e2e run passed with 5 tests and 2 EC2-gated tests skipped.
- The EC2 gated pair initially exposed deployment/transfer issues. After fixing AWS transfer host selection, transfer port ingress, download `transfer_public_host`, and rsync helper-file exclusions, the pair was rerun. In the final pair run, `codex-openrouter` passed and `codex-openai` timed out once during the cloud file-edit wait; rerunning the single `codex-openai` EC2 test passed.