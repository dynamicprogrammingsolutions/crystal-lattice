# Async Runtime Readiness And Startup Observability
Make cloud instance startup asynchronous, split container health from AgentApplication readiness, and surface useful startup diagnostics so heavyweight default-config cloud runtimes do not block or fail opaque synchronous `/instances` requests.

## Requirements checklist

- [ ] Change orchestrator instance startup so `POST /instances` returns promptly after creating/starting the runtime container, with instance state initially `starting`.
- [ ] Add explicit readiness/status polling for runtime AgentApplication readiness; clients should use `GET /instances/{instance_id}` or a similarly clear API to observe transition to `running` or `failed`.
- [ ] Split cloud runtime process health from AgentApplication readiness:
  - `/health` should indicate the FastAPI/runtime process is alive quickly.
  - a separate readiness signal should indicate bootstrap/config/plugin initialization completion.
  - proxy/export/session operations should return clear `503 runtime_not_ready` or orchestrator-level not-ready errors until ready.
- [ ] Improve startup diagnostics across orchestrator and runtime:
  - record startup stage and last error on the instance record
  - capture/surface runtime container logs when startup fails
  - include actionable error details in local `cloud.start_session_agent` action results
- [ ] Update `cloud.start_session_agent` to handle asynchronous startup by polling readiness or returning a structured "starting" result with enough data for clients to poll.
- [ ] Update tests so default-config cloud runtime startup no longer depends on one long synchronous `/instances` request.
- [ ] Preserve the managed-SSH transfer and explicit four-script contract from `tasks/20260429-cloud-agent-orchestrator/018-explicit-transfer-script-contract.md`.

Parent Task: tasks/20260429-cloud-agent-orchestrator/000-main.md

Depends On:

- tasks/20260429-cloud-agent-orchestrator/018-explicit-transfer-script-contract.md

## Background

While adding a default-config Codex cloud E2E after completing `018`, the test exposed a real architecture issue rather than a simple timeout problem.

Current startup chain:

```text
frontend test
  -> local backend /actions
  -> cloud.start_session_agent
  -> orchestrator POST /instances
  -> Docker runner starts runtime container
  -> runner waits for runtime /health
  -> runtime FastAPI startup builds AgentApplication
  -> path plugin install/load and default config initialization
```

For small test configs this is acceptable. For the full default config, runtime startup can include many path-plugin installs and AgentApplication initialization work. Because `/health` currently becomes available only after the startup event finishes, `POST /instances` stays open while the runtime initializes. This caused failures such as:

- local backend action returning `timed out`
- `POST /instances failed with HTTP 500: runner_start_failed`
- `Remote end closed connection without response`
- Docker runner reporting `runtime did not become healthy`

This is a contract/design problem: cloud instance creation is currently synchronous and coupled to heavyweight runtime readiness.

## Current Hotspots

- `cloud-orchestrator/lib/cloud_orchestrator/instance_registry.ex`
  - Current `handle_call({:start_instance, params}, ...)` synchronously calls `runner().start_instance(instance, params)` and only stores/returns the instance after the runner reports success. See current lines around `handle_call({:start_instance...})`, especially `runner().start_instance` and the immediate `runner_start_failed` response.
- `cloud-orchestrator/lib/cloud_orchestrator/runner/docker.ex`
  - Current `start_instance/2` runs `docker run`, then blocks in `wait_for_health(proxy_base_url)` before returning `{:ok, started}`.
  - Current `wait_for_health/1` polls `/health`; timeout was widened during testing, but widening is not the real fix.
- `cloud-orchestrator/runtime/python/runtime.py`
  - Current `@app.on_event("startup")` performs `_bootstrap_from_transfer()` and constructs `AgentApplication(...)`.
  - Current `/health` returns only after FastAPI startup has completed and reports `agent_application`.
- `application/python/agent_terminal_app/server.py`
  - Current `/actions` is synchronous and returns an action envelope after `app_instance.execute_action(...)`.
- `plugins/cloud-agent-app/src/cloud_agent_app/cloud_agent_app_plugin.py`
  - Current `cloud.start_session_agent` calls `/instances` and expects a ready connection link result in one action execution.
- `packages/frontend-sdk/src/integration/__tests__/cloud-orchestrator.e2e.integration.test.ts`
  - A new default-config Codex test was started in the working tree. It should become viable after async startup/readiness is implemented.

## Suggested Implementation Shape

1. Orchestrator instance states:
   - `starting`: container/process launched, runtime not AgentApplication-ready yet
   - `running`: runtime reports AgentApplication-ready
   - `failed`: startup failed; include `startup_error`, `startup_stage`, and possibly recent logs
   - `closed`: existing close behavior

2. Runner split:
   - `Runner.Docker.start_instance/2` should start the container and return instance metadata quickly: container id, proxy base URL, paths, port.
   - Do not block container start on AgentApplication readiness.
   - Add a runner callback or registry worker function that probes readiness and updates instance state asynchronously.

3. Runtime API split:
   - `/health`: returns quickly once FastAPI is serving, even if `AgentApplication` is still loading.
   - `/cloud-agent/runtime/ready` or similar: returns `200` when AgentApplication is ready; `503` with stage/details before that.
   - Consider initializing AgentApplication in a background task, with module-level readiness state.

4. Proxy/export guards:
   - `InstanceRegistry.handle_proxy_request`, `export_instance`, and `close_instance` should reject or clearly handle non-running instances.
   - Cloud export should not run until readiness is true.

5. Local action behavior:
   - Conservative option: keep `cloud.start_session_agent` returning only when running, but implement explicit polling against `GET /instances/{id}` with a long operation timeout and staged errors.
   - More UI-friendly option: return a "starting" result immediately with instance id and a pollable link/status. If choosing this, update frontend expectations accordingly.

6. Diagnostics:
   - On Docker runner startup failure, include recent `docker logs <container_id>` output in a controlled `startup_error_detail`.
   - Runtime should log/record progress: transfer materialized, config copied, env loaded, setup script run, AgentApplication init start, AgentApplication ready/failure.
   - `GET /instances/{id}` should expose safe public diagnostics without leaking host filesystem paths.

## Testing Direction

- Add orchestrator unit tests for `POST /instances` returning `starting` promptly and `GET /instances/{id}` transitioning state.
- Add Docker runner tests for non-blocking `start_instance/2` and readiness polling/update behavior.
- Add runtime tests for fast `/health` and separate readiness endpoint before/after AgentApplication initialization.
- Update or re-run the default-config Codex E2E in `packages/frontend-sdk/src/integration/__tests__/cloud-orchestrator.e2e.integration.test.ts`.
- Keep existing checks from `018` green:
  - plugin tests under `plugins/cloud-agent-app/tests`
  - `application/python/tests/test_cloud_agent_runtime.py`
  - `mix test` in `cloud-orchestrator`
  - cloud orchestrator local Docker E2E

## Notes From Failed Test Attempt

The attempted default-config test uses:

```bash
RUN_CLOUD_ORCHESTRATOR_E2E=1 \
RUN_CLOUD_ORCHESTRATOR_CODEX_DEFAULT_CONFIG_E2E=1 \
npm test --prefix packages/frontend-sdk -- cloud-orchestrator.e2e.integration.test.ts -t default-config
```

It starts one orchestrator and runs two provider cases (`codex-openrouter`, `codex-openai`) against derived default config. The test intentionally exercises local -> cloud -> local tool-call chains with shell/shell_command and apply_patch behavior. It should be revisited after this task, rather than made reliable by further timeout tuning.