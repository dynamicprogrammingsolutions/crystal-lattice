# Cloud Runtime Working Directory
Fix cloud runtime tool execution so relative paths resolve inside the transferred project workspace, not the runtime application directory.

## Requirements checklist

- [x] Change the cloud runtime startup to `chdir` into the materialized cloud workspace before initializing `AgentApplication`.
- [x] Verify shell/apply-patch tools default to the transferred project directory when config uses `working_directory: "."` without request-time absolute path overrides.
- [x] Keep this first fix limited to runtime cwd behavior; do not solve path-policy/config override concerns in the same change unless needed by tests.
- [x] Document or test the remaining issue: some directory references, such as `allowed_paths: [".."]`, may need cloud-specific config overrides during transfer.

Parent Task: `tasks/20260429-cloud-agent-orchestrator/000-main.md`

Depends On: `tasks/20260429-cloud-agent-orchestrator/060-connection-scoped-cloud-routing.md`
Depends On: `tasks/20260429-cloud-agent-orchestrator/062-clean-up-e2e-test-realism.md`

## Issue

When a cloud agent is asked to list the current directory, it can show runtime application files instead of project files:

```text
__pycache__/
poem.md
runtime.py
```

The transferred project files are present in the cloud workspace, for example:

```text
/cloud-agent/instance/workspace/committed.txt
```

The problem is that tools resolve relative `working_directory: "."` from the runtime process current directory. In the cloud container, that process cwd is the runtime app/code directory, which contains `runtime.py`, rather than the materialized workspace.

Relevant current code:

- `cloud-orchestrator/runtime/python/runtime.py`
  - `_initialize_runtime()` bootstraps the transfer and then constructs `AgentApplication`.
  - It passes env overrides including `WORKING_DIR: str(workspace_dir())`, but does not change process cwd.
- `cloud-orchestrator/lib/cloud_orchestrator/runner/docker.ex`
  - Sets `WORKING_DIR`, `CLOUD_WORKSPACE_DIR`, and `CLOUD_AGENT_WORKSPACE_DIR` to `/cloud-agent/instance/workspace`.
- `plugins/codex-tools/src/codex_tools/workdir.py`
  - `resolve_turn_cwd()` resolves relative `working_directory` from `Path.cwd()`.
- `application/python/agent_terminal_app/default_config/config.json`
  - Provider defaults use `working_directory: "."`.

## Immediate Solution

Change the cloud runtime startup to set the process cwd to the cloud workspace before `AgentApplication` is initialized.

Expected shape in `cloud-orchestrator/runtime/python/runtime.py`:

```python
_bootstrap_from_transfer()
os.chdir(workspace_dir())
server_mod._agent_app = AgentApplication(...)
```

This preserves the meaning of `working_directory: "."` and makes shell/apply-patch tools behave as if the cloud runtime was started from the transferred project directory.

After this change, new cloud agents should see project files such as `committed.txt` by default, and sync-back should include files created through normal shell/apply-patch tool usage.

Existing already-started cloud instances need to be restarted to pick up the cwd fix.

## Follow-Up Concern: Transfer-Time Config Overrides

Changing cwd fixes the immediate wrong-directory bug, but it does not fully solve all path policy questions.

Some config entries may still carry local assumptions that are not ideal in cloud, for example:

```json
"allowed_paths": [".", "..", "${env:CONFIG_DIR}"]
```

The `..` entry may mean something different or be broader than intended once the cloud runtime lives under `/cloud-agent/instance/workspace`.

For that, the cloud plugin/transfer packaging layer should eventually support applying extra cloud-specific config overrides while building the portable runtime config. The plugin should own this policy because it understands local-to-cloud transfer semantics.

Possible future behavior:

- Project/cloud-agent config declares additional runtime config overrides.
- `prepare_cloud_transfer()` applies those overrides after mixin resolution and agent/provider pruning.
- Overrides can adjust path-related settings such as `working_directory`, `allowed_paths`, and any provider/tool fields that should differ in cloud.
- The override mechanism should be plugin-agnostic and deterministic, not a hardcoded filter for specific plugin names.

Do not block the immediate `chdir` fix on designing this full override mechanism.

## Test Realism Note

The default-config Codex e2e previously used cloud request overrides:

```ts
working_directory: "/cloud-agent/instance/workspace",
allowed_paths: ["/cloud-agent/instance/workspace"]
```

That masks this bug. The regression test for this task should exercise the default config behavior directly, with `working_directory: "."` resolving from the cloud runtime process cwd after startup changes to `os.chdir(workspace_dir())`.

## Execution plan

Added during completion.

1. Update `cloud-orchestrator/runtime/python/runtime.py` so `_initialize_runtime()` calls `os.chdir(workspace_dir())` after `_bootstrap_from_transfer()` and before `AgentApplication` is initialized.
2. Keep the fix limited to runtime cwd behavior. Do not rewrite `working_directory`, `allowed_paths`, portable transfer config, or request-time overrides.
3. Add a focused regression test that imports the runtime module with temporary cloud paths, fakes `AgentApplication`, calls `_initialize_runtime()`, and asserts the process cwd is the materialized workspace at app construction time.
4. Run the focused regression and nearby cloud-agent transfer tests that do not require cloud credentials.
5. Record in completion notes that the broader cloud-specific path policy issue remains, especially configs such as `allowed_paths: [".."]`.

## Completion Notes

Added during completion.

- Updated `cloud-orchestrator/runtime/python/runtime.py` so `_initialize_runtime()` changes the process cwd to `workspace_dir()` immediately after transfer bootstrap and before `AgentApplication` construction.
- Added `application/python/tests/test_cloud_runtime_workdir.py`, which materializes a fake transferred workspace, fakes `AgentApplication`, and asserts app initialization observes the workspace as `Path.cwd()`.
- Left transfer-time path policy untouched. Config entries such as `allowed_paths: [".."]` may still need a later cloud-specific override mechanism in `prepare_cloud_transfer()`.
- Verification:
  - `pytest application/python/tests/test_cloud_runtime_workdir.py -q`
  - `PYTHONPATH=plugins/cloud-agent-app/src pytest plugins/cloud-agent-app/tests/test_cloud_agent_app_plugin.py -q`
  - `mix test` from `cloud-orchestrator`
- Additional gated e2e attempt after provider credentials were loaded from `.env`:
  - `RUN_CLOUD_ORCHESTRATOR_E2E=1 RUN_CLOUD_ORCHESTRATOR_CODEX_DEFAULT_CONFIG_E2E=1 npm test --prefix packages/frontend-sdk -- cloud-orchestrator.e2e -t "runs local-cloud-local bash and apply_patch chain with codex-openrouter"`
  - Result: failed after the cloud turn timed out waiting for `/cloud-agent/workspace/files/chain.txt` to contain `local1=alpha\ncloud2=alpha-bravo`.
  - Broader cloud e2e runs are deferred until tasks `tasks/20260429-cloud-agent-orchestrator/066-connection-created-session-routing.md` and `tasks/20260429-cloud-agent-orchestrator/067-cloud-transfer-endpoint-configuration.md` are complete or explicitly cleared for testing.
