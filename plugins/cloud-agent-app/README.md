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

For a model-oriented authoring guide with examples, see
[`docs/cloud-script-authoring.md`](docs/cloud-script-authoring.md). The default
`cloud-script-author` agent points at this guide through
`${env:BUILTIN_PLUGINS}/cloud-agent-app/docs/cloud-script-authoring.md` so the
same path works from source checkouts and bundled CLI installs. Keep the guide
in sync with this reference when changing container profile fields, since the
authoring agent reads it before inspecting plugin source.

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
- `validation_script` is executed by `crystal-lattice validate-cloud` after the
  shared transfer/setup/install/runtime smoke passes.

## Validation Command

Run local cloud validation from the main CLI:

```bash
crystal-lattice validate-cloud
```

Optional flags:

```bash
crystal-lattice validate-cloud --workspace-dir /path/to/project
crystal-lattice validate-cloud --keep-temp-dir
crystal-lattice validate-cloud --cache-dir /path/to/stable/cache
crystal-lattice validate-cloud --runtime-build-context /path/to/context --runtime-dockerfile /path/to/Dockerfile
```

Behavior:

- resolves the configured standard cloud profiles for the current workspace
- runs the normal local-stage and transfer-up flow
- writes the portable config/assets/env/runtime script bundle
- builds or reuses the configured local-Docker validation runtime without the
  orchestrator service, using explicit runtime-layout build metadata when a
  default/local image needs to be built
- waits for runtime readiness
- runs a deterministic built-in smoke check
- runs the optional `validation_script` hook when present
- bind-mounts `--cache-dir` at `/cloud-agent/cache` when provided so plugin and
  pip caches survive between validation runs

The command is contributed by `cloud-agent-app` as a CLI binding onto the
application action `cloud.validate_cloud`. The action remains the executable
contract; the command only defines the CLI shape.

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
      "managed_ssh": {
        "adapter_script": null,
        "ssh_path": "ssh",
        "rsync_path": "rsync",
        "extra_rsync_args": []
      },
      "disabled_plugins": [
        {"$raw": "path:${env:BUILTIN_PLUGINS}/session-asset-attachments"}
      ],
      "config_assets": {
        "include_config_dir": true,
        "exclude": [".env", ".env.*", ".plugin_cache", "logs", "sessions", "auth", "state"],
        "include_excluded": [],
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
- `default_transfer_up_profile`, `default_sync_down_profile`: Selected bundled
  or project-defined transfer/sync defaults.
- `default_container_profile`: Optional selected container profile. When omitted,
  the cloud-agent plugin supplies `default-runtime`.

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
- `mode`: Optional `image` or `dockerfile`. When omitted, the resolver infers
  `dockerfile` if `dockerfile` is present, otherwise `image`.
- `image`: Required runtime image name. In Dockerfile mode this is the image
  name the deployment-wired builder produces and the runner starts.
- `dockerfile`: Dockerfile source path. Required for Dockerfile mode. Env
  placeholders are expanded; relative paths resolve relative to the
  current/project directory. The Dockerfile is copied into the staged context
  and sent to the builder as a staged relative path.
- `context`: Source directory copied into a sanitized staged build context.
  Required for Dockerfile mode. Env placeholders are expanded; relative paths
  resolve relative to the current/project directory. The staged copy, not the
  live workspace directory, is used as the Docker build context.
- `target`: Optional Docker build target. Included in the build digest.
- `build_args`: Optional string build arguments. Included in the build digest.
  Do not use build args for secrets.
- `build_assets`: Optional list of file or directory assets copied into the
  staged build context before digesting/building. Each entry has `source` and
  `target`. `source` follows the same env-placeholder and relative-path rules.
  `target` is a safe relative path inside the staged context. Lockfiles and
  package manifests are ideal assets. Generated files, large directories,
  frequently changing source trees, and secret-containing paths are allowed by
  the parser but will cause rebuilds, larger artifact uploads, or unsafe images.
- `cache_mounts`: Optional persistent runtime mounts shared between instances.
  Each entry has `id`, `target`, and optional `scope` (`profile`, `connection`,
  `global`, or `instance`; default `profile`).
- `mounts`: Optional persistent runtime mounts for large mutable data that
  should not live in Docker image layers. Entries have the same shape as
  `cache_mounts`.

### Managed SSH adapter settings

- `managed_ssh.adapter_script`: Optional override for unusual transport needs.
- `managed_ssh.ssh_path`, `managed_ssh.rsync_path`, `managed_ssh.extra_rsync_args`:
  Platform-owned transport settings for the managed SSH transfer adapter.

### Portable runtime config settings

- `disabled_plugins`: Exact plugin-spec strings to remove only from the cloud
  runtime config during portable config generation. It works by string comparison, so most of the time you need to use
  the formula `{"$raw": "path:${env:BUILTIN_PLUGINS}/session-asset-attachments}`.
- `config_assets`: Policy for copying the local `CONFIG_DIR` asset tree into the
  transfer bundle.
- `runtime_env`: Policy for copying selected environment variables and env files
  into `.cloud-agent/env/runtime.env`.

`config_assets.exclude` keeps broad local-only config and secret directories out
of the transfer by default. Use `config_assets.include_excluded` for narrow,
intentional exceptions that should keep their config-relative path in the cloud
runtime. For example, to copy only saved ChatGPT credentials without copying the
whole `auth` directory:

```json
{
  "config_assets": {
    "include_excluded": [
      "auth/chatgpt-auth.json",
      "auth/chatgpt-rate-limits.json"
    ]
  }
}
```

For env files, prefer `runtime_env.env_files` when the file should be loaded as
runtime environment variables:

```json
{
  "runtime_env": {
    "env_files": [".env.cloud"]
  }
}
```

Use `config_assets.include_excluded` for `.env` or `.env.cloud` only when the
file itself must exist under the cloud runtime `CONFIG_DIR`; otherwise
`runtime_env.env_files` is usually the tighter transfer.

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
cloud startup. The local validation command then calls a runtime validation
endpoint that runs:

- a built-in smoke check proving the prepared runtime/workspace/session bundle
  is coherent
- the optional packaged `validation_script`

## Runtime Image Parity

`crystal-lattice validate-cloud` runs the same resolved
`container_profiles.<id>` selected by the cloud profile. In image mode, local
validation reuses the selected runtime image. In Dockerfile mode, validation
stages the configured build context and declared build assets, computes the
digest, builds/reuses the local image, and then runs the same runtime contract.

Image-mode validation still supports explicit runtime image build metadata:

```text
cloud_runtime_build_context
cloud_runtime_dockerfile
```

For the standard default `cloud-agent-runtime:latest`, validation computes a
digest from those declared build inputs, compares it with the Docker image label
`org.crystal-lattice.cloud-runtime.digest`, and rebuilds only when the image is
missing or stale. Builds also tag an immutable digest image such as
`cloud-agent-runtime:sha-<digest>`.

Custom runtime image names are treated as user-owned. If a custom image is
already present locally, validation trusts it. If it is missing, validation
fails clearly unless you pass explicit `--runtime-build-context` and
`--runtime-dockerfile` overrides for that command run.

Dockerfile-mode validation stages the selected container profile context and
build assets directly. The default packaged runtime Dockerfile and runtime app
are owned by this plugin under `cloud_agent_app/bundled_runtime`.

## Testing Guidance

Validation coverage is intentionally layered:

- unit tests in `plugins/cloud-agent-app/tests`
- runtime endpoint tests in `application/python/tests/test_cloud_agent_runtime.py`
- Docker-backed command tests in
  `application/python/tests/test_cloud_validation_command_docker.py`
- bundled binary smoke in `application/python/tests/test_binary_distribution_docker.py`
- fixture-backed frontend/orchestrator profile e2e in
  `packages/frontend-sdk/src/integration/__tests__/cloud-orchestrator.profiles.e2e.integration.test.ts`

This repository is the first real adopter of the shared validation flow through
its repo-local hooks:

- `.cloud-agent/local-stage`
- `.cloud-agent/install-cloud`
- `.cloud-agent/validate-cloud`

For the standard working-tree transfer profile, files staged into
`TRANSFER_STAGE_DIR` are copied directly into the cloud workspace root by the
bundled `cloud_setup_script`. A minimal `.env` handoff can therefore stay as
simple as copying `.env` into `TRANSFER_STAGE_DIR/.env`.

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