# Cloud Runtime Startup Optimizations
Capture later optimization ideas for making heavyweight cloud runtimes start faster after the async startup/readiness contract is fixed.

## Requirements checklist

- [ ] Do not implement as part of the immediate async startup/readiness fix unless explicitly pulled forward.
- [ ] Evaluate preinstalling or prewarming built-in/default path plugins in the runtime image.
- [ ] Evaluate slicing portable cloud config to the selected session/agent rather than transferring the whole terminal default config.
- [ ] Evaluate a generic long-running application action/job model for cloud start/sync/close and other slow actions.
- [ ] Preserve explicit transfer scripts and managed-SSH behavior from `tasks/20260429-cloud-agent-orchestrator/018-explicit-transfer-script-contract.md`.

Parent Task: tasks/20260429-cloud-agent-orchestrator/000-main.md

Depends On:

- tasks/20260429-cloud-agent-orchestrator/019-async-runtime-readiness-observability.md

## Background

The default-config Codex cloud E2E exposed that runtime startup can be heavyweight because path plugins are resolved/installed and the cloud runtime builds a full `AgentApplication` during startup. `tasks/20260429-cloud-agent-orchestrator/019-async-runtime-readiness-observability.md` should fix the contract problem first: startup should be asynchronous, readiness should be explicit, and diagnostics should be clear.

After that, these optimizations can reduce actual startup time.

## Optimization Ideas

### 1. Preinstall Or Prewarm Built-In Path Plugins

Current runtime image includes repo-root `plugins`, but path-plugin loading can still install plugin projects into a cache at runtime.

Possible improvements:

- Preinstall default built-in path plugins during `cloud-orchestrator/runtime/python/Dockerfile` build.
- Prewarm the plugin cache in the image for known default config plugins.
- Teach local path plugin resolution to use immutable built-in plugin paths directly when safe, avoiding repeated pip install work.
- Preserve fingerprints/manifests so dirty plugin source still resolves correctly during development.

Watch areas:

- `core/python/agent_app/plugin_sources/local_path.py`
- `core/python/agent_app/application_future.py`
- `cloud-orchestrator/runtime/python/Dockerfile`
- `application/python/agent_terminal_app/default_config/config.json`

### 2. Slice Portable Config For The Selected Cloud Agent

Current portable config preserves broad application config and can include many providers, agents, mixins, and plugins even when starting one cloud session for one agent.

Possible improvement:

- When starting a cloud session for a selected agent, build a cloud config containing only:
  - selected session's current agent
  - required provider
  - required mixins
  - required plugin path references
  - application/runtime pieces needed in the cloud
- Keep full-config transfer as an option if cloud sessions need agent switching.

Tradeoff:

- Slicing improves boot time and reduces transferred config surface.
- Slicing may remove cloud-side agent switching unless additional agents are explicitly included.

Watch areas:

- `plugins/cloud-agent-app/src/cloud_agent_app/cloud_agent_transfer.py`
- `plugins/cloud-agent-app/src/cloud_agent_app/cloud_agent_app_plugin.py`
- `core/python/agent_app/application_future.py`

### 3. Generic Long-Running Action/Job Model

Cloud start, sync-down, and close are naturally long operations. The current app action endpoint is synchronous.

Possible improvement:

- Add action/job APIs:
  - start action -> `{ job_id }`
  - poll action job -> stage/progress/result/error
  - optionally stream action events
- Let `cloud.start_session_agent` return progress stages such as:
  - local transfer script
  - managed SSH slot created
  - rsync upload
  - instance starting
  - runtime ready
  - connection link ready

This would improve UI ergonomics beyond cloud orchestration and reduce pressure on synchronous `/actions` HTTP requests.

Watch areas:

- `application/python/agent_terminal_app/server.py`
- `core/python/agent_app/application_future.py`
- `packages/frontend-sdk/src/backend/restBackend.ts`
- mobile action rendering screens if job progress becomes user-facing

## Suggested Order

1. Complete `tasks/20260429-cloud-agent-orchestrator/019-async-runtime-readiness-observability.md`.
2. Re-run the default-config Codex cloud E2E to identify remaining startup cost.
3. Choose between plugin prewarm and config slicing based on measured bottlenecks.
4. Consider the generic action/job model if UX still suffers from long action execution.