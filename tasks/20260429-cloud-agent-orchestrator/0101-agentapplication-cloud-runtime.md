# AgentApplication Cloud Runtime
Correct the MVP cloud runtime so a cloud connection runs a real `AgentApplication`-backed agent server, with portable config, env transfer, and config asset transfer.

## Requirements checklist

- [x] Replace or supersede the thin cloud runtime with an `AgentApplication`-backed runtime that can run model/tool loops in the cloud.
- [x] Keep the orchestrator/runner/runtime boundary backend-replaceable: orchestrator delegates requests to the runner; runner owns lifecycle/request handling; runtime is the agent process inside the container/task.
- [x] Generate and transfer a portable cloud config, including path remapping for workspace/session/config roots.
- [x] Transfer selected env vars referenced by config through explicit user-configurable env policy and runtime env files.
- [x] Transfer `CONFIG_DIR`-referenced config assets, including developer/system messages and helper scripts, so cloud-side system message behavior remains intact.
- [x] Add tests, including a gated real OpenRouter E2E that proves local tool-call file creation, cloud-side agent/tool execution, config asset integrity, and sync-back.

Parent Task: tasks/20260429-cloud-agent-orchestrator/000-main.md

Depends On: tasks/20260429-cloud-agent-orchestrator/0100-remote-docker-orchestrator-mvp.md

## Background

The MVP in `tasks/20260429-cloud-agent-orchestrator/0100-remote-docker-orchestrator-mvp.md` proved orchestration, transfer, proxying, cloud transport, workspace sync, and session export/import. However, the current cloud runtime is not a real cloud-side agent server.

Current runtime:

- `cloud-orchestrator/runtime/python/runtime.py`
- `cloud-orchestrator/runtime/python/Dockerfile`

It exposes a small FastAPI facade with session/message/workspace endpoints, including:

- `GET /sessions`
- `GET /sessions/{session_id}/messages`
- `POST /sessions/{session_id}/messages`
- `GET /cloud-agent/workspace/files/{path}`
- `POST /cloud-agent/workspace/files`
- `GET /cloud-agent/sessions/{session_id}/export`

It does not load `AgentApplication`, does not compile system messages, does not execute provider/tool loops, and does not run cloud-side model requests. The existing frontend SDK E2E in `packages/frontend-sdk/src/integration/__tests__/cloud-orchestrator.e2e.integration.test.ts` works because it tests transfer/proxy/session/workspace behavior, not cloud-side model execution.

The desired correction is to make the cloud runtime a real `AgentApplication`-backed runtime so a cloud connection is genuinely another agent server.

## Current Architecture References

Runner behavior is defined in:

- `cloud-orchestrator/lib/cloud_orchestrator/runner.ex`

Current callbacks:

```elixir
@callback start_instance(map(), map()) :: {:ok, map()} | {:error, term()}
@callback export_instance(map(), map()) :: {:ok, map()} | {:error, term()}
@callback close_instance(map(), map()) :: {:ok, map()} | {:error, term()}
```

The current Docker runner is:

- `cloud-orchestrator/lib/cloud_orchestrator/runner/docker.ex`

It currently starts runtime containers with `docker run`, mounts the transfer slot at `/transfer`, mounts workspace storage at `/workspace`, and forwards to the runtime via `proxy_base_url`.

Instance management calls the configured runner from:

- `cloud-orchestrator/lib/cloud_orchestrator/instance_registry.ex`

The proxy route currently lives in:

- `cloud-orchestrator/lib/cloud_orchestrator/router.ex`

The local application cloud action plugin is:

- `core/python/plugins/cloud_agent_app_plugin.py`

It currently:

- creates a temp transfer directory
- optionally runs a project transfer script
- otherwise copies workspace files into `TRANSFER_DIR/workspace`
- writes exported session data into `TRANSFER_DIR/.cloud-agent/sessions/<session_id>.json`
- uploads a tar/gzip bundle to the orchestrator
- calls `/instances`
- supports `cloud.sync_down` and `cloud.close_session`

## Boundary Decision

Use these definitions:

- Orchestrator: always-reachable control plane, auth/token validation, instance registry metadata, stable API surface.
- Runner: backend adapter that owns request handling and lifecycle policy for a cloud instance.
- Runtime: process inside the cloud container/task that runs the agent server.

The runner should own decisions such as:

- whether a runtime is already running
- whether to start a runtime for a request
- whether to stop after request/idle
- whether to answer a request directly from persistent storage
- whether to proxy to Docker, Fargate, Kubernetes, or another backend

Do not put `ensure_runtime` lifecycle policy in orchestrator core. The orchestrator may need a small delegation change so proxy requests are handed to the configured runner, but the policy belongs to runner implementations.

## Proposed Runner Interface Direction

Move toward a runner-owned proxy/request callback. A simple first version can be Plug-coupled because runners live inside the Elixir orchestrator:

```elixir
@callback handle_proxy_request(instance :: map(), conn :: Plug.Conn.t(), path :: String.t()) ::
  Plug.Conn.t()
```

The router should:

1. validate the cloud instance token
2. fetch the instance metadata
3. delegate the proxied request to the configured runner

The Docker runner can initially preserve existing long-running behavior by forwarding to `proxy_base_url`. Future runners can start tasks on demand or serve some routes directly.

Out of scope for this task unless explicitly expanded:

- Fargate backend implementation
- Kubernetes backend implementation
- per-request start/stop lifecycle
- idle shutdown policy
- storage-direct request serving

The interface should not block those future modes.

## Persistent Instance Storage

Introduce a stable per-instance storage layout prepared by the runner:

```text
<instance-root>/
  workspace/
  sessions/
  config/
    config.json
    assets/
  env/
    runtime.env
    runtime.env.d/
  transfer/
  logs/
  state/
```

The runtime should receive canonical env vars:

```text
CLOUD_AGENT_INSTANCE_DIR=/cloud-agent/instance
CLOUD_AGENT_WORKSPACE_DIR=/cloud-agent/instance/workspace
CLOUD_AGENT_SESSIONS_DIR=/cloud-agent/instance/sessions
CLOUD_AGENT_CONFIG_PATH=/cloud-agent/instance/config/config.json
CONFIG_DIR=/cloud-agent/instance/config/assets
```

Keep compatibility env vars only where useful:

```text
CLOUD_WORKSPACE_DIR
TRANSFER_DIR
SESSION_ID
SESSION_DIR
```

## Portable Config

The local cloud plugin should generate a portable cloud config and place it into the transfer payload, for example:

```text
TRANSFER_DIR/.cloud-agent/config/config.json
```

The portable config should:

- preserve providers, plugins, agents, and application settings required by `AgentApplication`
- preserve provider/model settings and tool config
- rewrite local machine paths to cloud paths
- set tool/provider `working_directory` to the cloud workspace
- set `allowed_paths` to the cloud workspace where appropriate
- avoid copying local cache/session/auth/log paths

The target config should be explicit and inspectable. Avoid relying on runtime magic to interpret local paths.

## Runtime Env Transfer

Add an explicit user-owned env transfer policy to default cloud config:

```json
"cloud_agent": {
  "runtime_env": {
    "include_config_env": true,
    "include": [],
    "exclude": [
      "CLOUD_ORCHESTRATOR_URL",
      "CLOUD_ORCHESTRATOR_TOKEN",
      "SERVER_HOST",
      "SERVER_PORT",
      "BRIDGE_URL",
      "BRIDGE_LOCAL_HTTP_BASE",
      "OPENAI_BASE_URL",
      "CONFIG_DIR",
      "BUILTIN_PLUGINS",
      "PLUGIN_CACHE_DIR"
    ],
    "env_files": []
  }
}
```

Behavior:

- scan raw config for `${env:NAME}` placeholders
- transfer present env values when `include_config_env` is true
- transfer env names listed in `include`
- exclude names listed in `exclude`
- copy explicit `env_files`
- write dotenv files under:

```text
TRANSFER_DIR/.cloud-agent/env/runtime.env
TRANSFER_DIR/.cloud-agent/env/runtime.env.d/*.env
```

Code may maintain a small reserved-name list for runtime/application-owned values, such as:

```text
CLOUD_AGENT_INSTANCE_DIR
CLOUD_AGENT_WORKSPACE_DIR
CLOUD_AGENT_SESSIONS_DIR
CLOUD_AGENT_CONFIG_PATH
CLOUD_WORKSPACE_DIR
TRANSFER_DIR
LOCAL_WORKSPACE_DIR
SESSION_ID
SESSION_DIR
CONFIG_DIR
BUILTIN_PLUGINS
```

This reserved list should stay small and documented. Larger policy should remain explicit in config.

Never print secret values in logs, action display payloads, or test output. If action results include env information, include names only.

## CONFIG_DIR Asset Transfer

The default config references files under `${env:CONFIG_DIR}`, including developer/system messages and helper scripts. Local `CONFIG_DIR` paths are not meaningful in the cloud.

The local cloud plugin should:

- detect `${env:CONFIG_DIR}` references
- copy referenced config assets into:

```text
TRANSFER_DIR/.cloud-agent/config/assets/
```

- keep portable config references in the form:

```text
${file:${env:CONFIG_DIR}/...}
```

- set cloud runtime `CONFIG_DIR` to:

```text
/cloud-agent/instance/config/assets
```

For the default config, ensure required developer/system message assets and helper scripts are available in the cloud. Avoid copying auth state, sessions, logs, caches, or `.plugin_cache`.

## AgentApplication Runtime

Replace or supersede the thin runtime with a runtime that starts `AgentApplication` from the portable config and cloud session root.

Prefer reusing `agent_terminal_app.server` where practical. If that is too coupled to local terminal startup, build a cloud-specific FastAPI runtime that still delegates to `AgentApplication`.

The cloud runtime should support the HTTP surface needed by the frontend SDK/mobile app, including:

- health
- sessions
- messages
- send/send_message
- events
- cancel
- agents
- application actions/UI where applicable

The key acceptance point is that cloud runtime can run model/tool loops itself.

## Runtime Image

Update the cloud runtime image so it includes:

- `core/python`
- `application/python`
- built-in plugins
- default tool shared packages such as `plugins/tool-compat-shared` and `plugins/web-fetch-shared`
- the cloud runtime entrypoint

The image must remain generic. Do not bake user secrets, private config, or local machine paths into the image.

## Tests

Add lower-level tests:

- portable config rewrites workspace/session/config paths correctly
- env scanner detects `${env:OPENROUTER_API_KEY}`
- user-defined `runtime_env.exclude` is respected
- reserved runtime names are not transferred
- `CONFIG_DIR` assets are copied and references remain portable
- Docker runner passes env files and mounts persistent instance storage
- cloud runtime boots an `AgentApplication`
- cloud runtime can run a simple echo-provider request

Keep the existing frontend SDK cloud E2E passing.

Add a gated real OpenRouter E2E in or near:

- `packages/frontend-sdk/src/integration/__tests__/cloud-orchestrator.e2e.integration.test.ts`

Gate it with:

```bash
RUN_CLOUD_ORCHESTRATOR_E2E=1
RUN_CLOUD_ORCHESTRATOR_OPENROUTER_E2E=1
OPENROUTER_API_KEY=...
```

The E2E should:

1. start the local Docker orchestrator
2. start a local backend using OpenRouter, tool support, file writing, and the cloud plugin
3. use config with `api_key` from `${env:OPENROUTER_API_KEY}`
4. use a system/developer message from `${env:CONFIG_DIR}`
5. make a real local OpenRouter request that calls a file-writing tool
6. assert the local file exists
7. start the cloud agent
8. assert the locally-created file transferred to the cloud workspace
9. assert `CONFIG_DIR` assets/system message content are present intact in the cloud
10. make a real cloud-side OpenRouter request that calls a file-writing tool
11. assert the cloud file exists
12. sync down
13. assert the cloud-created file exists locally

Use a cheap model from env with a fallback, for example:

```bash
CLOUD_ORCHESTRATOR_OPENROUTER_MODEL=<cheap-tool-capable-model>
```

## Documentation

Update relevant docs after implementation:

- `cloud-orchestrator/README.md`
- `cloud-orchestrator/deploy/remote-docker/README.md`
- `application/python/README.md`
- default config cloud-agent section

Document:

- runner/runtime/orchestrator concepts
- permanent orchestrator vs replaceable runner/runtime
- portable config
- env transfer policy
- `CONFIG_DIR` asset transfer
- how to run the gated real OpenRouter E2E

## Completion Notes

Completed. This task was added to capture the corrected MVP scope: cloud runtime should be a real `AgentApplication` runtime, while lifecycle/request decisions remain runner-owned for future Docker-on-demand, Fargate, and Kubernetes backends.

Added during completion:

- Replaced the thin Python runtime facade with an `AgentApplication`-backed cloud runtime that reuses `agent_terminal_app.server`, bootstraps transferred workspace/session/config/env data, and preserves cloud workspace/config helper routes for sync and test assertions.
- Added cloud transfer packaging helpers that generate `.cloud-agent/config/config.json`, copy `CONFIG_DIR` assets with config-owned excludes and top-level size limits, and write runtime env files from explicit policy. The portable config removes `application.cloud_agent`, sets runtime-owned plugin cache storage, and preserves plugin-owned fields such as `working_directory` and `allowed_paths`.
- Added `AgentApplication.get_config_path()` and `AgentApplication.get_raw_config()` so packaging can preserve unresolved placeholders.
- Moved proxy request handling behind the runner callback, and updated the Docker runner to prepare/mount a persistent per-instance layout under `/cloud-agent/instance`.
- Updated the runtime Docker image to build from the repository root and include `core/python`, `application/python`, repo-root plugins, and shared tool packages.
- Updated local harness, remote Docker deploy, AWS build packaging, default config, and docs for the new runtime image/config/env behavior.
- Added tests for portable config/env/assets, runtime `AgentApplication` boot and echo request execution, runner-owned proxy delegation, local Docker cloud E2E with cloud-side send/config asset integrity/sync-down, and a gated real OpenRouter E2E.
- Verified:
  - `pytest core/python/tests/test_cloud_agent_app_plugin.py -q`
  - `pytest application/python/tests/test_cloud_agent_runtime.py -q`
  - `pytest application/python/tests/test_application_actions_endpoints.py -q`
  - `mix test` in `cloud-orchestrator`
  - `npm test --prefix packages/frontend-sdk -- cloud-orchestrator.e2e.integration.test.ts`
  - `RUN_CLOUD_ORCHESTRATOR_E2E=1 npm test --prefix packages/frontend-sdk -- cloud-orchestrator.e2e.integration.test.ts`
  - `RUN_CLOUD_ORCHESTRATOR_E2E=1 RUN_CLOUD_ORCHESTRATOR_OPENROUTER_E2E=1 npm test --prefix packages/frontend-sdk -- cloud-orchestrator.e2e.integration.test.ts` with `OPENROUTER_API_KEY` loaded from the root `.env`
  - `docker build -t cloud-agent-runtime:latest -f cloud-orchestrator/runtime/python/Dockerfile .`

## Execution plan

Added during completion after user approval.

1. Add a cloud transfer/config packaging helper for the local cloud application plugin.
   - Generate an explicit cloud runtime config under `.cloud-agent/config/config.json`.
   - Preserve plugin-owned configuration values such as `working_directory`, `allowed_paths`, and arbitrary tool/provider paths.
   - Remove `application.cloud_agent` from the generated cloud config because orchestrator/action settings are local-control-plane concerns, not runtime agent concerns.
   - Set only runtime-owned storage values such as `plugin_cache_dir`.
   - Copy the local `CONFIG_DIR` tree broadly into `.cloud-agent/config/assets/`, controlled by config-owned exclude patterns and a per-top-level-entry size limit.
   - Transfer runtime env through `.cloud-agent/env/runtime.env` and optional `.cloud-agent/env/runtime.env.d/`, including config-referenced env vars by policy while excluding reserved runtime-owned names and configured excludes.

2. Replace the thin Python cloud runtime with an `AgentApplication`-backed runtime.
   - Reuse `agent_terminal_app.server` where possible so the cloud runtime supports sessions, messages, send/send_message, events, cancel, agents, and actions consistently.
   - Bootstrap the persistent instance layout, import transferred sessions/config/assets/env, and expose compatibility cloud workspace/session helper routes used by sync-down and close.
   - Set canonical runtime env vars including `CONFIG_DIR`, `WORKING_DIR`, `BUILTIN_PLUGINS`, `CLOUD_AGENT_INSTANCE_DIR`, `CLOUD_AGENT_WORKSPACE_DIR`, `CLOUD_AGENT_SESSIONS_DIR`, and `CLOUD_AGENT_CONFIG_PATH`.

3. Move proxy handling to the runner boundary and update Docker runner lifecycle/materialization.
   - Add a runner `handle_proxy_request/3` callback.
   - Keep Docker runner behavior long-running for now, but let it own forwarding to `proxy_base_url`.
   - Prepare a stable per-instance storage layout and mount it into the runtime container.

4. Update the runtime image/build path.
   - Build the runtime image from a repo-root context so it includes `core/python`, `application/python`, and repo-root built-in plugins/shared packages.
   - Update local harness, remote Docker deploy, AWS builder, and docs build commands accordingly.

5. Add tests at the right layers.
   - Python unit tests for portable config boundaries, env policy, config asset excludes, size limits, and built-in plugin path preservation.
   - Runtime tests proving the cloud runtime boots `AgentApplication` and can run an echo-provider request.
   - Elixir tests for runner-owned proxy delegation and Docker runner env/mount/layout behavior.
   - Keep the existing cloud orchestrator frontend SDK E2E passing and extend it to prove cloud-side send/tool-loop execution.
   - Add a gated real OpenRouter E2E for local tool execution, cloud tool execution, config asset integrity, env transfer, and sync-back.

6. Update documentation and defaults.
   - Document the orchestrator/runner/runtime split, portable config, config asset copy policy, env transfer policy, runtime image expectations, and gated E2E commands.