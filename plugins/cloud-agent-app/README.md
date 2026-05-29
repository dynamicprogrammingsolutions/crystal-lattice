# Cloud Agent App

Cloud agent application plugin and managed SSH transfer adapter.

This README is the primary reference for the cloud profile schema, bundled
script layout, repo-local hook conventions, and cloud-runtime transfer
contract. Keep `application/python/README.md` at the quick-start layer and put
cloud-profile reference detail here.

## Overview

The cloud agent app lets a local server start a cloud runtime for a session,
transfer the workspace and session state, connect through the orchestrator, and
later sync changes back down.

The current profile model is built around:

- `transfer_up_profiles`
- `sync_down_profiles`
- `container_profiles`

`transfer_up_profiles` now own the full transfer/setup/install/validation
contract directly. There are no separate bundled `cloud_setup_profiles` or
`install_profiles`.

## Standard Repo-Local Hooks

These three hooks are the standard repo-local extension points:

- `.cloud-agent/local-stage`
- `.cloud-agent/install-cloud`
- `.cloud-agent/validate-cloud`

They are addressed in config through:

- `local_stage_script`
- `install_script`
- `validation_script`

Default conventional paths:

```text
${env:WORKING_DIR}/.cloud-agent/local-stage
${env:WORKING_DIR}/.cloud-agent/install-cloud
${env:WORKING_DIR}/.cloud-agent/validate-cloud
```

Behavior:

- If one of those fields resolves to its standard conventional path and the
  file does not exist, the hook is treated as a no-op.
- If you point one of those fields at some other path and that file does not
  exist, resolution fails with a clear error.
- `validation_script` is part of the config and transfer contract now, but this
  task does not implement the validation command or orchestrated execution of
  that hook yet.

## Bundled Script Layout

Bundled scripts live under the default config asset tree and are derivable
directly from config section, profile id, and script key.

```text
application/python/agent_terminal_app/default_config/cloud-agent/profiles/
  transfer_up/
    working-tree-current-state/
      local_transfer_script
      cloud_setup_script
    working-tree-current-state-branch/
      local_transfer_script
      cloud_setup_script
    clean-head/
      local_transfer_script
      cloud_setup_script
  sync_down/
    working-tree-patch/
      cloud_export_script
      cloud_mark_synced_script
      local_apply_script
    branch-import/
      cloud_export_script
      cloud_mark_synced_script
      local_apply_script
```

Rules:

- Every config-addressable bundled script is self-contained.
- Bundled wrapper hooks are not used for repo-local staging, install, or
  validation.
- Profile ids should represent distinct behaviors, not aliases. For example,
  there is one canonical bundled branch-import sync-down profile because the
  script already handles the optional delegated snapshot path conditionally.

## Complete Example Config

```json
{
  "plugins": [
    "path:${env:BUILTIN_PLUGINS}/cloud-agent-app"
  ],
  "application": {
    "cloud_agent": {
      "orchestrator_url": "${env:CLOUD_ORCHESTRATOR_URL}",
      "orchestrator_token": "${env:CLOUD_ORCHESTRATOR_TOKEN}",
      "workspace_dir": ".",
      "connection_key": "optional-stable-project-or-server-key",
      "transfer_method": "managed_ssh",
      "project_config_path": "${env:WORKING_DIR}/.cloud-agent/cloud-agent.json",
      "default_transfer_up_profile": "working-tree-current-state",
      "default_sync_down_profile": "working-tree-patch",
      "default_container_profile": "default-runtime",
      "transfer_up_profiles": {
        "working-tree-current-state": {
          "label": "Working tree current state",
          "local_stage_script": "${env:WORKING_DIR}/.cloud-agent/local-stage",
          "local_transfer_script": "${env:CONFIG_DIR}/cloud-agent/profiles/transfer_up/working-tree-current-state/local_transfer_script",
          "cloud_setup_script": "${env:CONFIG_DIR}/cloud-agent/profiles/transfer_up/working-tree-current-state/cloud_setup_script",
          "install_script": "${env:WORKING_DIR}/.cloud-agent/install-cloud",
          "validation_script": "${env:WORKING_DIR}/.cloud-agent/validate-cloud",
          "compatible_sync_down_profiles": ["working-tree-patch"]
        },
        "working-tree-current-state-branch": {
          "label": "Working tree current state with branch export",
          "local_stage_script": "${env:WORKING_DIR}/.cloud-agent/local-stage",
          "local_transfer_script": "${env:CONFIG_DIR}/cloud-agent/profiles/transfer_up/working-tree-current-state-branch/local_transfer_script",
          "cloud_setup_script": "${env:CONFIG_DIR}/cloud-agent/profiles/transfer_up/working-tree-current-state-branch/cloud_setup_script",
          "install_script": "${env:WORKING_DIR}/.cloud-agent/install-cloud",
          "validation_script": "${env:WORKING_DIR}/.cloud-agent/validate-cloud",
          "compatible_sync_down_profiles": ["branch-import"]
        },
        "clean-head": {
          "label": "Clean committed HEAD",
          "local_stage_script": "${env:WORKING_DIR}/.cloud-agent/local-stage",
          "local_transfer_script": "${env:CONFIG_DIR}/cloud-agent/profiles/transfer_up/clean-head/local_transfer_script",
          "cloud_setup_script": "${env:CONFIG_DIR}/cloud-agent/profiles/transfer_up/clean-head/cloud_setup_script",
          "install_script": "${env:WORKING_DIR}/.cloud-agent/install-cloud",
          "validation_script": "${env:WORKING_DIR}/.cloud-agent/validate-cloud",
          "compatible_sync_down_profiles": ["branch-import"]
        }
      },
      "sync_down_profiles": {
        "working-tree-patch": {
          "label": "Apply cloud patch to current worktree",
          "cloud_export_script": "${env:CONFIG_DIR}/cloud-agent/profiles/sync_down/working-tree-patch/cloud_export_script",
          "cloud_mark_synced_script": "${env:CONFIG_DIR}/cloud-agent/profiles/sync_down/working-tree-patch/cloud_mark_synced_script",
          "local_apply_script": "${env:CONFIG_DIR}/cloud-agent/profiles/sync_down/working-tree-patch/local_apply_script",
          "compatible_transfer_up_profiles": ["working-tree-current-state"]
        },
        "branch-import": {
          "label": "Import committed cloud branch with optional safety snapshots",
          "cloud_export_script": "${env:CONFIG_DIR}/cloud-agent/profiles/sync_down/branch-import/cloud_export_script",
          "cloud_mark_synced_script": "${env:CONFIG_DIR}/cloud-agent/profiles/sync_down/branch-import/cloud_mark_synced_script",
          "local_apply_script": "${env:CONFIG_DIR}/cloud-agent/profiles/sync_down/branch-import/local_apply_script",
          "compatible_transfer_up_profiles": [
            "working-tree-current-state-branch",
            "clean-head"
          ]
        }
      },
      "container_profiles": {
        "default-runtime": {
          "label": "Default cloud agent runtime",
          "image": "cloud-agent-runtime:latest"
        }
      },
      "managed_ssh": {
        "adapter_script": null,
        "ssh_path": "ssh",
        "rsync_path": "rsync",
        "extra_rsync_args": []
      },
      "disabled_plugins": [
        "path:${env:BUILTIN_PLUGINS}/session-asset-attachments"
      ],
      "config_assets": {
        "include_config_dir": true,
        "exclude": [".env", ".env.*", ".plugin_cache", "logs", "sessions", "auth", "state"],
        "max_top_level_entry_bytes": 104857600
      },
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
  }
}
```

## Config Reference

### Top-level cloud settings

- `orchestrator_url`: Base URL for the control plane.
- `orchestrator_token`: Optional auth token for orchestrator requests.
- `workspace_dir`: Default local workspace used by cloud actions when the UI
  action input does not override it.
- `connection_key`: Optional stable opaque key for connection reuse. If omitted,
  the plugin derives one from local config and workspace context.
- `transfer_method`: Currently `managed_ssh`.
- `project_config_path`: Optional project-level override file. The default is
  `${env:WORKING_DIR}/.cloud-agent/cloud-agent.json`.
- `default_transfer_up_profile`, `default_sync_down_profile`,
  `default_container_profile`: Selected bundled or project-defined defaults.

### `transfer_up_profiles`

Each profile describes one complete upload/setup/install/validation family.

- `label`: Human-readable label.
- `local_stage_script`: Optional repo-local staging hook.
- `local_transfer_script`: Required local export script.
- `cloud_setup_script`: Required cloud workspace materialization script.
- `install_script`: Optional repo-local cloud install/bootstrap hook.
- `validation_script`: Optional repo-local validation hook contract.
- `compatible_sync_down_profiles`: Optional allow-list for matching sync-down
  profiles.

### `sync_down_profiles`

- `label`: Human-readable label.
- `cloud_export_script`: Required cloud export script.
- `cloud_mark_synced_script`: Optional cloud acknowledgement script that runs
  only after local apply succeeds.
- `local_apply_script`: Required local apply/import script.
- `compatible_transfer_up_profiles`: Optional allow-list for matching
  transfer-up profiles.

### `container_profiles`

- `label`: Human-readable label.
- `image`: Runtime image name. If empty, the resolver falls back to
  `cloud-agent-runtime:latest`.

### Managed SSH adapter settings

- `managed_ssh.adapter_script`: Optional override for unusual transport needs.
- `managed_ssh.ssh_path`, `managed_ssh.rsync_path`, `managed_ssh.extra_rsync_args`:
  Platform-owned transport settings for the managed SSH transfer adapter.

### Portable runtime config settings

- `disabled_plugins`: Exact plugin-spec strings to remove only from the cloud
  runtime config during portable config generation.
- `config_assets`: Policy for copying the local `CONFIG_DIR` asset tree into the
  transfer bundle.
- `runtime_env`: Policy for copying selected environment variables and env files
  into `.cloud-agent/env/runtime.env`.

## Project Overrides

Projects can override the bundled defaults from an optional workdir file at:

```text
.cloud-agent/cloud-agent.json
```

Rules:

- That file may override default profile ids or individual profile fields.
- Script fields can be a string or an ordered fallback list.
- The first existing script path wins.
- Relative paths in the project file resolve from `WORKING_DIR`.
- If a project file provides a fallback list for a script field, inherited
  bundled candidates remain available after the listed project candidates.

## Script Environment Contract

Scripts receive stable environment variables:

- Local stage/transfer/apply:
  `LOCAL_WORKSPACE_DIR`, `CLOUD_WORKSPACE_DIR`, `TRANSFER_DIR`,
  `TRANSFER_STAGE_DIR`, `WORKING_DIR`, `SESSION_ID`
- Cloud setup/install/export/mark-synced:
  `CLOUD_WORKSPACE_DIR`, `TRANSFER_DIR`, `TRANSFER_STAGE_DIR`, `WORKING_DIR`,
  `SESSION_ID`
- Profile selection:
  `CLOUD_AGENT_PROFILE_ID`, `CLOUD_AGENT_TRANSFER_UP_PROFILE_ID`,
  `CLOUD_AGENT_SYNC_DOWN_PROFILE_ID`
- Branch/snapshot flows:
  `CLOUD_AGENT_IMPORTED_BRANCH_NAME`, `CLOUD_AGENT_DELEGATED_SNAPSHOT_REF`,
  `CLOUD_AGENT_CLOUD_FULL_STATE_REF`, `CLOUD_AGENT_LOCAL_IMPORT_STATE_REF`,
  `CLOUD_AGENT_LAST_SYNCED_REF`

## Runtime Bundle Notes

When a cloud session starts, the local action:

- creates `.cloud-agent/config/config.json` for the cloud runtime
- removes the local `application.cloud_agent` control-plane section from that
  portable config
- copies the configured `CONFIG_DIR` asset tree to `.cloud-agent/config/assets/`
- writes `.cloud-agent/env/runtime.env` according to `runtime_env`
- copies the selected cloud setup/install/export/mark-synced scripts into
  `.cloud-agent/scripts/`
- copies `validation_script` into `.cloud-agent/scripts/validate` when present

The current cloud runtime bootstrap executes setup and install during normal
cloud startup. The validation hook is packaged as part of the contract but is
not executed by the orchestrated runtime flow yet.

## License

Crystal Lattice Cloud Agent App is an application plugin for cloud-backed agent
sessions. Copyright (C) 2026 Dynamic Programming Solutions Kft.

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU Affero General Public License as published by the Free
Software Foundation, either version 3 of the License, or (at your option) any
later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE. See the GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License along
with this program. If not, see <https://www.gnu.org/licenses/>.