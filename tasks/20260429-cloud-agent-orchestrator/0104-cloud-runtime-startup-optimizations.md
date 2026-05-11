# Cloud Runtime Startup Optimizations
Capture later optimization ideas for making heavyweight cloud runtimes start faster after the async startup/readiness contract is fixed.

## Requirements checklist

- [x] Implement deterministic selected-agent cloud config reduction: resolve mixins, keep selected agent, keep only providers referenced by remaining agents.
- [x] Do not hard-code provider or plugin names into the reduction policy.
- [x] Move cloud runtime plugin cache to a persistent shared cache mounted by the orchestrator runner.
- [x] Extend the shared runtime cache to pip downloads/wheels via `PIP_CACHE_DIR`.
- [x] Preserve explicit transfer scripts and managed-SSH behavior from `tasks/20260429-cloud-agent-orchestrator/0102-explicit-transfer-script-contract.md`.

Parent Task: tasks/20260429-cloud-agent-orchestrator/000-main.md

Depends On:

- tasks/20260429-cloud-agent-orchestrator/0103-async-runtime-readiness-observability.md

## Execution plan

Added during completion after user approval.

1. Update the cloud-agent transfer preparation to accept the selected session `agent_id`.
2. Build the portable cloud config by resolving mixins on the raw config, then keeping only the selected agent and providers referenced by the remaining agents.
3. Keep the policy plugin-agnostic: no allowlists for specific providers or plugins.
4. Rewrite the cloud plugin cache path to a shared runtime cache location.
5. Mount a persistent orchestrator runtime cache into Docker runtime containers and set `PIP_CACHE_DIR`/`XDG_CACHE_HOME`.
6. Add focused tests for config reduction and Docker runner cache args.
7. Re-run targeted Python/Elixir/frontend and cloud E2E tests, including the default-config Codex E2E.

## Background

The default-config Codex cloud E2E exposed that runtime startup can be heavyweight because path plugins are resolved/installed and the cloud runtime builds a full `AgentApplication` during startup. `tasks/20260429-cloud-agent-orchestrator/0103-async-runtime-readiness-observability.md` should fix the contract problem first: startup should be asynchronous, readiness should be explicit, and diagnostics should be clear.

After that, these optimizations can reduce actual startup time.

## Follow-up Test Evidence

After `tasks/20260429-cloud-agent-orchestrator/0103-async-runtime-readiness-observability.md` was completed, the full default-config Codex cloud E2E was re-run with:

```bash
RUN_CLOUD_ORCHESTRATOR_E2E=1 \
RUN_CLOUD_ORCHESTRATOR_CODEX_DEFAULT_CONFIG_E2E=1 \
npm test --prefix packages/frontend-sdk -- cloud-orchestrator.e2e.integration.test.ts -t default-config
```

The baseline cloud orchestrator Docker E2E passed, but the full default-config Codex E2E failed for both `codex-openrouter` and `codex-openai` because each cloud runtime reached `runtime_readiness_timeout` after 300 seconds. The new diagnostics showed the runtime process was healthy and `/cloud-agent/runtime/ready` was returning `503` while `AgentApplication` was still installing unrelated default path plugins such as `gemini-tools`, `grok-tools`, and `qwen-tools`.

This confirms the remaining blocker is startup cost, not the async readiness contract. Do not solve this by only increasing timeouts; use the optimization ideas below.

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

1. Complete `tasks/20260429-cloud-agent-orchestrator/0103-async-runtime-readiness-observability.md`.
2. Re-run the default-config Codex cloud E2E to identify remaining startup cost.
3. Choose between plugin prewarm and config slicing based on measured bottlenecks.
4. Consider the generic action/job model if UX still suffers from long action execution.

## Completion Notes

Added during completion.

Implemented deterministic selected-agent config reduction in the cloud-agent transfer path. The portable cloud config now resolves mixins first, keeps only the selected session agent, keeps only providers referenced by the remaining agents, and removes the now-unneeded mixin sections. The policy is plugin-agnostic and does not special-case provider or plugin names.

Moved the cloud runtime plugin cache to `/cloud-agent/cache/plugin_cache/plugins`, mounted a persistent orchestrator runtime cache into Docker runtime containers at `/cloud-agent/cache`, and set `PIP_CACHE_DIR=/cloud-agent/cache/pip` plus `XDG_CACHE_HOME=/cloud-agent/cache/xdg`. Added a file lock around path-plugin target installs so shared cache installs do not collide.

Updated the default-config Codex E2E to assert that the compiled default Codex developer message is present and substituted. For OpenAI Responses, the test overrides `system_message_as_instructions=false` and `strip_leading_system_or_developer_message=false` so the compiled message is observable through REST session messages while still using the default config's Codex developer text.

Verification completed:

- `PYTHONPATH=plugins/cloud-agent-app/src:core/python pytest plugins/cloud-agent-app/tests/test_cloud_agent_app_plugin.py -q` passed.
- `PYTHONPATH=core/python:application/python pytest application/python/tests/test_cloud_agent_runtime.py -q` passed.
- `mix test` in `cloud-orchestrator` passed.
- `mix format --check-formatted` in `cloud-orchestrator` passed.
- `npm test --prefix packages/frontend-sdk -- cloud-orchestrator.e2e.integration.test.ts` passed in skipped/compile mode.
- `RUN_CLOUD_ORCHESTRATOR_E2E=1 npm test --prefix packages/frontend-sdk -- cloud-orchestrator.e2e.integration.test.ts` passed.
- `RUN_CLOUD_ORCHESTRATOR_E2E=1 RUN_CLOUD_ORCHESTRATOR_CODEX_DEFAULT_CONFIG_E2E=1 npm test --prefix packages/frontend-sdk -- cloud-orchestrator.e2e.integration.test.ts -t default-config` passed with both provider cases.