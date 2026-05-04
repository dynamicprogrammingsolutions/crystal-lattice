# Cloud Profile Configuration Without Behavior Change
Introduce a structured cloud profile configuration model while keeping the current default transfer/sync behavior automatic and unchanged.

## Requirements checklist

- [ ] Add a profile configuration model with separate `transfer_up_profiles`, `install_profiles`, `sync_down_profiles`, and `container_profiles`.
- [ ] Move the current single four-script setup into explicit profile entries in the default config.
- [ ] Keep the plugin using the configured default profiles automatically; do not add user-facing profile selection in this task.
- [ ] Resolve profile script paths with env placeholders such as `${env:CONFIG_DIR}`, `${env:WORKING_DIR}`, and repo-root-relative paths.
- [ ] Ensure default script paths are relative to `${env:CONFIG_DIR}` so they are packaged into the portable cloud config.
- [ ] Add compatibility validation between transfer-up profiles, install profiles, and sync-down profiles.
- [ ] Avoid `requires: {"git": true}` style dependency declarations; dependencies belong in container images/Dockerfiles or install scripts.
- [ ] Remove the old direct four-script config shape from the default config; no migration/backward compatibility is required.
- [ ] Cover stable behavior with focused unit tests and an integration-style plugin test.

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
