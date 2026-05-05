# Cloud Profile Configuration Without Behavior Change
Introduce a structured cloud profile configuration model while keeping the current default transfer/sync behavior automatic and unchanged.

## Requirements checklist

- [x] Add a profile configuration model with separate `transfer_up_profiles`, `install_profiles`, `sync_down_profiles`, and `container_profiles`.
- [x] Move the current single four-script setup into explicit profile entries in the default config.
- [x] Keep the plugin using the configured default profiles automatically; do not add user-facing profile selection in this task.
- [x] Resolve profile script paths with env placeholders such as `${env:CONFIG_DIR}`, `${env:WORKING_DIR}`, and repo-root-relative paths.
- [x] Ensure default script paths are relative to `${env:CONFIG_DIR}` so they are packaged into the portable cloud config.
- [x] Add compatibility validation between transfer-up profiles, install profiles, and sync-down profiles.
- [x] Avoid `requires: {"git": true}` style dependency declarations; dependencies belong in container images/Dockerfiles or install scripts.
- [x] Remove the old direct four-script config shape from the default config; no migration/backward compatibility is required.
- [x] Support a single optional workdir override file, defaulting to `${env:WORKING_DIR}/.cloud-agent/cloud-agent.json`, that can override profile defaults or individual profile script paths.
- [x] Allow script fields to be strings or ordered fallback lists of strings; pick the first existing script after env expansion and path resolution.
- [x] Cover stable behavior with focused unit tests and an integration-style plugin test.

## Task checklist

- [x] Add cloud profile resolver/model with single-file project override support.
- [x] Wire `CloudAgentAppPlugin` to resolved default profiles without adding UI selection.
- [x] Update bundled default config, scripts, and package data.
- [x] Update docs and e2e config helpers to the new profile shape.
- [x] Add/update focused tests and run verification.

Parent Task: `tasks/20260429-cloud-agent-orchestrator/000-main.md`

Depends On: `tasks/20260429-cloud-agent-orchestrator/068-real-tool-sync-back-e2e.md`

## Background

The current plugin reads direct script fields under `application.cloud_agent`:

```json
{
  "local_transfer_script": ".cloud-agent/transfer-up",
  "cloud_setup_script": ".cloud-agent/setup-cloud",
  "cloud_export_script": ".cloud-agent/export-cloud",
  "local_apply_script": ".cloud-agent/apply-down"
}
```

This task should replace that default shape with profile config, without changing what happens when the user starts or syncs a cloud agent.

## Proposed Config Shape

Use explicit profile sections. Names can be adjusted during implementation, but keep the concepts separate:

```json
{
  "application": {
    "cloud_agent": {
      "default_transfer_up_profile": "working-tree-current-state",
      "default_sync_down_profile": "working-tree-patch",
      "default_container_profile": "default-runtime",
      "transfer_up_profiles": {
        "working-tree-current-state": {
          "label": "Working tree current state",
          "local_transfer_script": "${env:CONFIG_DIR}/cloud-agent/profiles/working-tree-current-state/transfer-up",
          "install_profile": "repo-install",
          "compatible_sync_down_profiles": ["working-tree-patch"]
        }
      },
      "install_profiles": {
        "repo-install": {
          "label": "Repository install",
          "cloud_install_script": "${env:CONFIG_DIR}/cloud-agent/profiles/repo-install/install"
        }
      },
      "sync_down_profiles": {
        "working-tree-patch": {
          "label": "Apply cloud patch to current worktree",
          "cloud_export_script": "${env:CONFIG_DIR}/cloud-agent/profiles/working-tree-patch/export",
          "local_apply_script": "${env:CONFIG_DIR}/cloud-agent/profiles/working-tree-patch/apply-down",
          "compatible_transfer_up_profiles": ["working-tree-current-state"]
        }
      },
      "container_profiles": {
        "default-runtime": {
          "label": "Default cloud agent runtime",
          "image": "cloud-agent-runtime:latest"
        }
      }
    }
  }
}
```

The install profile is about package/dependency installation, not workspace materialization. The default install profile should be no-op unless a repo/config script is defined.

## Path Resolution Rules

- Expand `${env:...}` placeholders before resolving relative paths.
- Profile paths defined in default config should normally use `${env:CONFIG_DIR}`.
- Repo-owned paths may be repo-root-relative.
- Cloud runtime path resolution must work after portable config generation, where `CONFIG_DIR` points to copied config assets and `WORKING_DIR`/`CLOUD_WORKSPACE_DIR` point to the materialized workspace.
- All scripts must receive explicit path env vars; do not rely on implicit cwd.

## Testing Notes

Add tests for:

- profile resolver loading the new shape
- env placeholder expansion
- default profile selection
- compatibility validation failures
- plugin still invoking the same effective transfer/install/export/apply scripts with no UI selection
- portable config generation including default scripts under copied config assets

## Execution plan

Added during completion on 2026-05-04 after code investigation and user approval.

1. Add a small cloud profile resolver module for `application.cloud_agent` that understands `transfer_up_profiles`, `install_profiles`, `sync_down_profiles`, and `container_profiles`.
2. Support one optional project override JSON at `project_config_path`, defaulting to `${env:WORKING_DIR}/.cloud-agent/cloud-agent.json`. The base app config is merged first; the project file shallowly overrides top-level defaults and profile entries by id.
3. Resolve profile script fields after env-placeholder expansion. Script fields may be a string or ordered fallback list of strings; resolver selects the first existing candidate and keeps clear errors for missing required scripts.
4. Preserve automatic behavior by resolving only configured default profiles in this task. Store selected/effective script paths and selected profile ids in plugin state; do not add user-facing profile inputs or selection controls.
5. Validate profile graph compatibility: transfer-up profile references an install profile; sync-down profile and transfer-up profile compatibility declarations agree when provided; default profile ids exist; container profile exists; `requires` fields are rejected.
6. Pass the selected container image to orchestrator instance creation as `runtime_image`, using the current `cloud-agent-runtime:latest` default profile so runtime behavior stays unchanged.
7. Move the default four-script setup into explicit bundled default profile entries. Default script paths should use `${env:CONFIG_DIR}/cloud-agent/...`; add bundled scripts under `application/python/agent_terminal_app/default_config/cloud-agent/...` and include them in package data.
8. Update docs and e2e config helpers from direct script fields to the new profile shape, keeping their project scripts as workdir overrides where useful.
9. Add focused resolver tests plus integration-style plugin tests proving the same effective transfer/install/export/apply scripts run with no UI selection, project override/fallback behavior works, compatibility failures are reported, and portable config/assets include bundled profile scripts.

## Completion Notes

Added during completion on 2026-05-04 after implementation and verification.

- Added `cloud_agent_app.cloud_agent_profiles.resolve_cloud_agent_profiles` to resolve default cloud profiles, load one optional workdir override file at `.cloud-agent/cloud-agent.json`, merge project profile entries shallowly, reject `requires`, validate compatibility, and resolve script fallback lists.
- Wired `CloudAgentAppPlugin` to use resolved default profiles automatically and pass the selected container profile image to orchestrator instance creation as `runtime_image`.
- Replaced the top-level four-script shape in the bundled default cloud config with profile sections and added bundled patch/archive default scripts under `application/python/agent_terminal_app/default_config/cloud-agent/profiles/`.
- Updated package data so the bundled cloud-agent profile scripts are included in installed layouts.
- Updated frontend e2e config helpers to write one workdir `.cloud-agent/cloud-agent.json` file that points at patch/archive project scripts.
- Updated docs and focused tests for resolver behavior, project override/fallback behavior, compatibility validation, default config self-containment, default config bootstrap copying, and stable plugin action behavior.
- After gated e2e verification, corrected the bundled and generated project scripts from simplified rsync behavior to the intended git archive/patch flow. `apply-down` now treats an already-applied patch as success so `cloud.sync_down` followed by `cloud.close_session` remains repeatable.
- Added a two-phase sync acknowledgement for incremental patch syncs. `cloud_export_script` keeps cloud changes staged and retry-safe; after local apply succeeds, the plugin calls `/instances/:id/sync-applied`, the runtime runs `cloud_mark_synced_script`, and the default `mark-synced` script commits the staged cloud changes so later exports contain only new changes.
- Added incremental sync coverage where change 1 is synced down, change 2 is made in the cloud, and close-session syncs only the later change.

Verification:

```bash
PYTHONPATH=plugins/cloud-agent-app/src:core/python pytest plugins/cloud-agent-app/tests/test_cloud_agent_app_plugin.py -q
PYTHONPATH=core/python:application/python pytest application/python/tests/test_runtime_layout.py application/python/tests/test_default_config_effective_agent_configs.py core/python/tests/test_default_system_instructions_docs.py -q
PYTHONPATH=core/python:application/python pytest application/python/tests/test_cloud_agent_runtime.py -q
cd packages/frontend-sdk && npm test -- cloud-orchestrator.e2e.integration.test.ts
ruff check plugins/cloud-agent-app/src/cloud_agent_app plugins/cloud-agent-app/tests/test_cloud_agent_app_plugin.py application/python/tests/test_runtime_layout.py application/python/tests/test_default_config_effective_agent_configs.py core/python/tests/test_default_system_instructions_docs.py
```

Additional gated verification:

```bash
cd packages/frontend-sdk && RUN_CLOUD_ORCHESTRATOR_E2E=1 npm test -- src/integration/__tests__/cloud-orchestrator.e2e.integration.test.ts -t "opens a cloud session through CloudTransport and syncs workspace files back down"
cd packages/frontend-sdk && RUN_CLOUD_ORCHESTRATOR_E2E=1 npm test -- src/integration/__tests__/cloud-orchestrator.e2e.integration.test.ts -t "routes two cloud sessions through one connection-scoped CloudTransport"
cd packages/frontend-sdk && RUN_CLOUD_ORCHESTRATOR_E2E=1 RUN_CLOUD_ORCHESTRATOR_OPENROUTER_E2E=1 npm test -- src/integration/__tests__/cloud-orchestrator.e2e.integration.test.ts -t "runs local and cloud OpenRouter tool calls with config assets and sync-back"
cd packages/frontend-sdk && RUN_CLOUD_ORCHESTRATOR_E2E=1 RUN_CLOUD_ORCHESTRATOR_CODEX_DEFAULT_CONFIG_E2E=1 npm test -- src/integration/__tests__/cloud-orchestrator.e2e.integration.test.ts -t "runs local-cloud-local bash and apply_patch chain with codex-openrouter"
cd packages/frontend-sdk && RUN_CLOUD_ORCHESTRATOR_E2E=1 RUN_CLOUD_ORCHESTRATOR_CODEX_DEFAULT_CONFIG_E2E=1 npm test -- src/integration/__tests__/cloud-orchestrator.e2e.integration.test.ts -t "runs local-cloud-local bash and apply_patch chain with codex-openai"
cd packages/frontend-sdk && AWS_STACK_NAME=crystal-lattice-cloud-orchestrator-e2e-profile-070 AWS_REGION=us-east-1 npm run integration:cloud:aws:build
cd packages/frontend-sdk && AWS_STACK_NAME=crystal-lattice-cloud-orchestrator-e2e-profile-070 AWS_REGION=us-east-1 RUN_CLOUD_ORCHESTRATOR_E2E=1 RUN_AWS_CLOUD_ORCHESTRATOR_TESTS=1 CLOUD_ORCHESTRATOR_E2E_MODE=aws-ec2-cloudfront npm test -- src/integration/__tests__/cloud-orchestrator.e2e.integration.test.ts -t "opens a cloud session through CloudTransport and syncs workspace files back down"
cd packages/frontend-sdk && AWS_STACK_NAME=crystal-lattice-cloud-orchestrator-e2e-profile-070 AWS_REGION=us-east-1 npm run integration:cloud:aws:build
cd packages/frontend-sdk && AWS_STACK_NAME=crystal-lattice-cloud-orchestrator-e2e-profile-070 AWS_REGION=us-east-1 RUN_CLOUD_ORCHESTRATOR_E2E=1 RUN_AWS_CLOUD_ORCHESTRATOR_TESTS=1 CLOUD_ORCHESTRATOR_E2E_MODE=aws-ec2-cloudfront npm test -- src/integration/__tests__/cloud-orchestrator.e2e.integration.test.ts -t "routes two cloud sessions through one connection-scoped CloudTransport"
cd packages/frontend-sdk && AWS_STACK_NAME=crystal-lattice-cloud-orchestrator-e2e-profile-070 AWS_REGION=us-east-1 npm run integration:cloud:aws:build
cd packages/frontend-sdk && AWS_STACK_NAME=crystal-lattice-cloud-orchestrator-e2e-profile-070 AWS_REGION=us-east-1 RUN_CLOUD_ORCHESTRATOR_E2E=1 RUN_AWS_CLOUD_ORCHESTRATOR_TESTS=1 CLOUD_ORCHESTRATOR_E2E_MODE=aws-ec2-cloudfront RUN_CLOUD_ORCHESTRATOR_OPENROUTER_E2E=1 npm test -- src/integration/__tests__/cloud-orchestrator.e2e.integration.test.ts -t "runs local and cloud OpenRouter tool calls with config assets and sync-back"
cd packages/frontend-sdk && AWS_STACK_NAME=crystal-lattice-cloud-orchestrator-e2e-profile-070 AWS_REGION=us-east-1 npm run integration:cloud:aws:build
cd packages/frontend-sdk && AWS_STACK_NAME=crystal-lattice-cloud-orchestrator-e2e-profile-070 AWS_REGION=us-east-1 RUN_CLOUD_ORCHESTRATOR_E2E=1 RUN_AWS_CLOUD_ORCHESTRATOR_TESTS=1 CLOUD_ORCHESTRATOR_E2E_MODE=aws-ec2-cloudfront RUN_CLOUD_ORCHESTRATOR_CODEX_DEFAULT_CONFIG_EC2_E2E=1 npm test -- src/integration/__tests__/cloud-orchestrator.e2e.integration.test.ts -t "runs EC2 local-cloud-local bash and apply_patch chain with codex-openrouter"
cd packages/frontend-sdk && AWS_STACK_NAME=crystal-lattice-cloud-orchestrator-e2e-profile-070 AWS_REGION=us-east-1 npm run integration:cloud:aws:build
cd packages/frontend-sdk && AWS_STACK_NAME=crystal-lattice-cloud-orchestrator-e2e-profile-070 AWS_REGION=us-east-1 RUN_CLOUD_ORCHESTRATOR_E2E=1 RUN_AWS_CLOUD_ORCHESTRATOR_TESTS=1 CLOUD_ORCHESTRATOR_E2E_MODE=aws-ec2-cloudfront RUN_CLOUD_ORCHESTRATOR_CODEX_DEFAULT_CONFIG_EC2_E2E=1 npm test -- src/integration/__tests__/cloud-orchestrator.e2e.integration.test.ts -t "runs EC2 local-cloud-local bash and apply_patch chain with codex-openai"
cd packages/frontend-sdk && AWS_STACK_NAME=crystal-lattice-cloud-orchestrator-e2e-profile-070 AWS_REGION=us-east-1 npm run integration:cloud:aws:down:builder
aws --region us-east-1 cloudformation describe-stacks --query "Stacks[?starts_with(StackName, 'crystal-lattice-cloud-orchestrator-e2e-profile-070')].[StackName,StackStatus]" --output table
```

Additional incremental-sync verification after adding sync acknowledgement:

```bash
PYTHONPATH=plugins/cloud-agent-app/src:core/python pytest plugins/cloud-agent-app/tests/test_cloud_agent_app_plugin.py -q
PYTHONPATH=core/python:application/python pytest application/python/tests/test_cloud_agent_runtime.py -q
cd cloud-orchestrator && mix test test/cloud_orchestrator/router_test.exs test/cloud_orchestrator/registry_test.exs
PYTHONPATH=core/python:application/python pytest application/python/tests/test_runtime_layout.py application/python/tests/test_default_config_effective_agent_configs.py core/python/tests/test_default_system_instructions_docs.py -q
ruff check plugins/cloud-agent-app/src/cloud_agent_app plugins/cloud-agent-app/tests/test_cloud_agent_app_plugin.py application/python/tests/test_runtime_layout.py application/python/tests/test_default_config_effective_agent_configs.py application/python/tests/test_cloud_agent_runtime.py core/python/tests/test_default_system_instructions_docs.py
cd packages/frontend-sdk && RUN_CLOUD_ORCHESTRATOR_E2E=1 npm test -- src/integration/__tests__/cloud-orchestrator.e2e.integration.test.ts -t "opens a cloud session through CloudTransport and syncs workspace files back down"
cd packages/frontend-sdk && AWS_STACK_NAME=crystal-lattice-cloud-orchestrator-e2e-profile-070-incremental AWS_REGION=us-east-1 npm run integration:cloud:aws:build
cd packages/frontend-sdk && AWS_STACK_NAME=crystal-lattice-cloud-orchestrator-e2e-profile-070-incremental AWS_REGION=us-east-1 RUN_CLOUD_ORCHESTRATOR_E2E=1 RUN_AWS_CLOUD_ORCHESTRATOR_TESTS=1 CLOUD_ORCHESTRATOR_E2E_MODE=aws-ec2-cloudfront npm test -- src/integration/__tests__/cloud-orchestrator.e2e.integration.test.ts -t "opens a cloud session through CloudTransport and syncs workspace files back down"
cd packages/frontend-sdk && AWS_STACK_NAME=crystal-lattice-cloud-orchestrator-e2e-profile-070-incremental AWS_REGION=us-east-1 npm run integration:cloud:aws:down:builder
aws --region us-east-1 cloudformation describe-stacks --query "Stacks[?starts_with(StackName, 'crystal-lattice-cloud-orchestrator-e2e-profile-070-incremental')].[StackName,StackStatus]" --output table
```
