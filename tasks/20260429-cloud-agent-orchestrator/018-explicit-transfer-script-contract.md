# Transfer And Orchestration Contract Cleanup
Clean up cloud-agent transfer/orchestration handling so workspace sync, setup, export, close, and deploy verification match the intended MVP contract from `010` and the real `AgentApplication` runtime from `015`.

## Requirements checklist

- [x] Remove or disable implicit workspace copy defaults for sync-up; starting a cloud agent should require a user/project-defined transfer script for workspace contents.
- [x] Remove `upload_script` and `download_script` from the user-facing cloud-agent contract unless a separate transfer-adapter feature is deliberately designed later.
- [x] Implement the intended four-script model:
  - Sync-up local transfer script: packages selected local workspace contents into `TRANSFER_DIR`.
  - Sync-up cloud setup script: runs in the cloud after files are materialized into `CLOUD_WORKSPACE_DIR`; may be empty, commonly installs dependencies.
  - Sync-down cloud export script: packages selected cloud changes into `TRANSFER_DIR`.
  - Sync-down local apply script: applies downloaded changes into `LOCAL_WORKSPACE_DIR`.
- [x] Keep the actual byte transfer between scripts owned by the software/orchestrator/runner, not by project scripts.
- [x] Make transfer slots truly opaque at the orchestrator API boundary; remove or supersede public assumptions such as `bundle.tar.gz`, tar/gzip-only upload/download endpoints, or fixed archive names.
- [x] Implement the managed SSH transfer-slot backend described in `010`:
  - start a restricted short-lived transfer service/container when the selected transfer method requires it
  - restrict it to the transfer slot directory
  - deny shell, TTY, agent forwarding, port forwarding, and arbitrary filesystem access
  - expose endpoint metadata without leaking host filesystem paths
- [x] Keep HTTP bundle upload/download only as an explicit local/dev transfer adapter if retained; do not present it as the core script contract.
- [x] Make cloud setup and cloud export scripts first-class configuration/contract concepts, not hardcoded incidental file names.
- [x] Reduce public instance-start payloads to the intended minimal shape where possible, centered on `transfer_ref`; remove now-redundant `cloud_workspace_dir` from runner/runtime control flow.
- [x] Define and implement close-time behavior: either `cloud.close_session` performs final cloud export + local apply before stopping, or docs/API explicitly separate "sync then close" as required user flow.
- [x] Revalidate remote Docker and AWS EC2/CloudFront deployment after the `015` runtime image build-context change.
- [x] Update docs to recommend script templates/patterns rather than unsafe defaults.
- [x] Update E2E tests to use explicit scripts. For the test transfer script, prefer git-based packaging that behaves like a checkout while including staged and unstaged modifications and excluding git-ignored files.
- [x] Preserve portable config/session/env/config-asset transfer behavior from `tasks/20260429-cloud-agent-orchestrator/015-agentapplication-cloud-runtime.md`.
- [x] Keep scoped stateless instance tokens with expiration as-is for now; revocation/token-store work is out of scope for this cleanup.

Parent Task: tasks/20260429-cloud-agent-orchestrator/000-main.md

Depends On:

- tasks/20260429-cloud-agent-orchestrator/010-remote-docker-orchestrator-mvp.md
- tasks/20260429-cloud-agent-orchestrator/015-agentapplication-cloud-runtime.md

## Background

The intended script contract was already written in `tasks/20260429-cloud-agent-orchestrator/010-remote-docker-orchestrator-mvp.md` under `### Transfer and script contract`:

```md
Keep transfers as opaque slots. The orchestrator must not assume tar/gzip, archive names, one file vs many files, rsync vs SFTP, git metadata, or a workspace layout.

Use these script env vars:

- `LOCAL_WORKSPACE_DIR`
- `CLOUD_WORKSPACE_DIR`
- `TRANSFER_DIR`

Start/upload flow:

- Local transfer script receives `LOCAL_WORKSPACE_DIR`, `CLOUD_WORKSPACE_DIR`, and `TRANSFER_DIR`.
- Cloud setup script receives `CLOUD_WORKSPACE_DIR` and `TRANSFER_DIR`.

Return/sync-down flow:

- Cloud export script receives `CLOUD_WORKSPACE_DIR` and `TRANSFER_DIR`.
- Local apply script receives `LOCAL_WORKSPACE_DIR`, `CLOUD_WORKSPACE_DIR`, and `TRANSFER_DIR`.
```

The current implementation partially violates or muddies this contract. A later review of `010` against the `015` implementation found additional drift beyond the script names.

Current mismatches to clean up:

- `core/python/plugins/cloud_agent_app_plugin.py` still defaults to copying the whole workspace into the transfer payload when `transfer_script` is not set. This is risky for real projects because it may copy ignored/generated/private files.
- The same plugin exposes `upload_script` and `download_script`. These are confusing because the intended contract is that scripts prepare/apply contents, while the software transfers bytes between endpoints.
- Sync-down currently defaults to copying downloaded transfer contents directly into the local workspace when `apply_script` is absent.
- The Docker runner export path currently tars the cloud workspace directly, instead of invoking a cloud export script that decides what should be transferred back.
- The runtime has a `setup-cloud` hook shape, but the user-facing config/docs need to define this clearly as the cloud setup script in the four-script model.
- `cloud-orchestrator/lib/cloud_orchestrator/transfer_registry.ex` still assumes `bundle.tar.gz` for upload/download. That contradicts the "opaque transfer slot" wording from `010`.
- The orchestrator currently returns a `managed_ssh` endpoint shape, but there is no actual restricted managed SSH/SFTP transfer service/container implementing the documented security model.
- `cloud.start_session_agent` still sends `cloud_workspace_dir` in the instance-start payload. After `015`, the runner/runtime use canonical `/cloud-agent/instance/...` paths, so this value should be script-contract/user-facing only if retained at all.
- `cloud.close_session` currently retrieves final session state but does not perform final workspace export/apply. If the intended UX is "close brings everything home", close should run the same explicit export/apply flow or be documented as requiring a prior `cloud.sync_down`.
- `015` changed the runtime image build context to the repository root so it can include `core/python`, `application/python`, and repo-root plugins. Local Docker E2E passed, but remote Docker and AWS EC2/CloudFront paths should be revalidated after this deployment-sensitive change.

Token note:

- `010` said tokens should preferably be short-lived or revocable. Current tokens are stateless, scoped by instance/session claims, and expire. That is acceptable for now. Do not add token revocation or a token store in this task unless the scope is explicitly reopened.

## Desired Model

There should be no broad default workspace copy for real cloud sessions. For now, workspace transfer should be explicit and user/project-owned.

Sync-up:

1. Local transfer script runs with:
   - `LOCAL_WORKSPACE_DIR`
   - `CLOUD_WORKSPACE_DIR`
   - `TRANSFER_DIR`
2. Software transfers the contents of `TRANSFER_DIR` to the cloud side.
3. Runner/runtime materializes the transferred files into `CLOUD_WORKSPACE_DIR`.
4. Cloud setup script runs with:
   - `CLOUD_WORKSPACE_DIR`
   - `TRANSFER_DIR`

Sync-down:

1. Cloud export script runs with:
   - `CLOUD_WORKSPACE_DIR`
   - `TRANSFER_DIR`
2. Software transfers the contents of `TRANSFER_DIR` to the local side.
3. Local apply script runs with:
   - `LOCAL_WORKSPACE_DIR`
   - `CLOUD_WORKSPACE_DIR`
   - `TRANSFER_DIR`

Transfer adapters:

- Project scripts do not upload/download directly.
- A transfer adapter owned by the local app/orchestrator/runner moves bytes between transfer slots.
- The orchestrator API should speak in terms of transfer slots and transfer refs, not a specific archive filename.
- A retained HTTP adapter may use tar/gzip internally, but that detail should stay behind the adapter boundary.
- The remote Docker path should implement the managed SSH/SFTP slot described in `010`, or clearly mark it as deferred and keep docs honest.

Instance startup:

- Public `POST /instances` payloads should be centered on:

```json
{
  "transfer_ref": {
    "transfer_id": "tr_123"
  }
}
```

- `session_id` may remain if needed for token/link/session targeting, but runner/runtime filesystem paths should be canonical and runner-owned.
- `cloud_workspace_dir` should not steer Docker mount paths or cloud runtime env. The cloud runtime uses `/cloud-agent/instance/workspace`.

Close/sync:

- Decide and document whether `cloud.close_session` means:
  - "final sync then close", in which case it must run cloud export + local apply before stopping, or
  - "session-only close", in which case UI/docs must require `cloud.sync_down` before close when workspace changes matter.
- Prefer "final sync then close" if it can be implemented without surprising overwrites.

## Test Direction

Update the cloud orchestrator E2E to define explicit test scripts.

Suggested sync-up test script behavior:

- Use git to create a checkout-like transfer.
- Exclude git-ignored files.
- Include tracked files, staged changes, and unstaged modifications.
- The exact implementation can be a small shell script checked into the test fixture or generated by the E2E test.

Suggested sync-down test script behavior:

- Cloud export script uses git-aware logic to package only the intended changes into `TRANSFER_DIR`.
- Local apply script applies those changes to the local workspace.

The E2E should assert at least:

- A git-ignored local file is not transferred.
- A tracked modified file is transferred.
- A staged new file is transferred.
- An unstaged new file, if intentionally supported by the script, is transferred.
- Cloud-created changes sync back only through the cloud export/local apply script path.
- `cloud.close_session` behavior matches the documented choice: either it performs final sync or tests assert sync is explicitly required before close.
- The instance-start payload used by the local action no longer includes redundant runtime path controls.
- Transfer API tests do not require callers to know `bundle.tar.gz`.
- Managed SSH/SFTP transfer-slot tests cover restricted endpoint metadata and lifecycle, if implemented in this cleanup.

Deployment revalidation:

- Run local Docker E2E after the contract cleanup.
- Run or document the result of generic remote Docker deploy/E2E after the runtime build-context change from `015`.
- Run or document the result of AWS EC2/CloudFront E2E after the runtime build-context change from `015`.

## Current References

- Intended contract: `tasks/20260429-cloud-agent-orchestrator/010-remote-docker-orchestrator-mvp.md`, section `### Transfer and script contract`.
- Current sync-up default copy and `transfer_script` hook: `core/python/plugins/cloud_agent_app_plugin.py`.
- Current extra `upload_script`/`download_script` hooks: `core/python/plugins/cloud_agent_app_plugin.py`.
- Current sync-down default apply behavior: `core/python/plugins/cloud_agent_app_plugin.py`.
- Current docs mentioning `transfer_script`, `upload_script`, `download_script`, and `apply_script`: `application/python/README.md`.
- Current transfer contract docs: `cloud-orchestrator/README.md`.
- Current tar/gzip transfer-slot assumption: `cloud-orchestrator/lib/cloud_orchestrator/transfer_registry.ex`.
- Current token implementation, intentionally out of scope except for preserving scoped expiration: `cloud-orchestrator/lib/cloud_orchestrator/token.ex`.
- Current runtime build-context changes from `015`: `cloud-orchestrator/runtime/python/Dockerfile`, `cloud-orchestrator/deploy/remote-docker/deploy.sh`, `cloud-orchestrator/deploy/aws-ec2/builder.yaml`, and `packages/frontend-sdk/src/integration/harness.ts`.

## Execution plan

Added during completion after user approval.

1. Move the cloud application plugin out of `core/python/plugins` into repo-root `plugins/`, and update configs/tests to load it via a `path:` plugin reference.
   - Preserve portable config/session/env/config-asset transfer behavior from `015`.
   - Keep the implementation importable in tests and runtime packaging after the move.

2. Split project content scripts from platform byte-transfer scripts.
   - Project/user scripts remain file-local:
     - `local_transfer_script`: prepares selected local workspace contents into `TRANSFER_DIR`.
     - `cloud_setup_script`: runs in the cloud after materialization into `CLOUD_WORKSPACE_DIR`.
     - `cloud_export_script`: prepares selected cloud workspace changes into `TRANSFER_DIR`.
     - `local_apply_script`: applies downloaded changes from `TRANSFER_DIR` into `LOCAL_WORKSPACE_DIR`.
   - Remove `upload_script` and `download_script` as project-facing hooks.
   - Do not restore broad default workspace copy/apply fallbacks.

3. Implement managed SSH as the platform transfer method.
   - The orchestrator creates restricted, short-lived SSH transfer slots.
   - The local plugin uses a platform-owned bash adapter script to run `rsync` over the managed SSH endpoint.
   - The rsync adapter has a built-in default script, with a config override under managed-SSH adapter settings.
   - Project content scripts do not receive SSH endpoint details unless a user deliberately overrides the platform adapter.

4. Retire HTTP archive transfer.
   - Remove public upload/download bundle routes and registry helpers.
   - Remove `bundle.tar.gz` assumptions and tar/gzip-only transfer-slot behavior.
   - Keep transfer slots opaque at the public API boundary.

5. Make cloud setup/export scripts first-class runtime concepts.
   - Package configured cloud setup/export scripts into the reserved `.cloud-agent` runtime sidecar.
   - Runtime startup materializes only user workspace transfer contents into `CLOUD_WORKSPACE_DIR`, then runs the packaged cloud setup script.
   - Runtime export runs the packaged cloud export script into a runtime-owned export directory; runner copies that directory into the requested transfer slot.

6. Reduce instance startup payloads and keep runner-owned canonical paths.
   - Start instances from `session_id` plus `transfer_ref`.
   - Remove `cloud_workspace_dir` from local action start payloads and runtime control flow.

7. Define close behavior as final sync then close.
   - `cloud.close_session` should run final cloud export, managed-SSH rsync download, and local apply before stopping.
   - If final sync fails, leave the instance running and surface the failure.
   - After successful sync, close the instance and import/save final remote session state.

8. Update tests and docs.
   - Unit tests should cover required/explicit script behavior, adapter env, no `cloud_workspace_dir` start payload, no HTTP bundle routes, and opaque transfer slots.
   - Runtime/runner tests should cover cloud setup/export scripts and export through runtime rather than host workspace tar.
   - E2E tests should use explicit scripts, with a git-aware local transfer script that excludes ignored files and includes intended local changes.
   - Docs should describe script templates/patterns and managed-SSH rsync transfer rather than unsafe defaults.

9. Verify locally and document deployment revalidation.
   - Run focused Python, Elixir, and frontend SDK tests.
   - Run local Docker E2E when feasible.
   - Run or document remote Docker and AWS EC2/CloudFront validation status.

## Completion Notes

Added during completion.

- Moved the cloud application plugin out of `core/python/plugins` into `plugins/cloud-agent-app`, with `agent_plugin.json`, package metadata, and default loading through `path:${env:BUILTIN_PLUGINS}/cloud-agent-app`.
- Replaced `transfer_script` / `apply_script` fallbacks and `upload_script` / `download_script` hooks with the explicit content-script contract: `local_transfer_script`, `cloud_setup_script`, `cloud_export_script`, and `local_apply_script`.
- Added a platform-owned managed-SSH rsync adapter script with a config override at `application.cloud_agent.managed_ssh.adapter_script`.
- Retired HTTP bundle upload/download routes and removed `bundle.tar.gz` assumptions from the transfer flow.
- Added a restricted managed SSH transfer container image and orchestrator lifecycle support for short-lived transfer slot services. Upload services are stopped when the transfer is marked ready; download services are deleted after local apply.
- Changed runtime startup to materialize transfer slot contents directly into the cloud workspace while keeping `.cloud-agent` as a reserved sidecar, and added a runtime export endpoint that runs the configured cloud export script.
- Changed Docker runner export to call the runtime export endpoint and copy the resulting export directory into the requested transfer slot instead of tarring the host workspace.
- Changed `cloud.close_session` to perform final sync-down before closing, leaving the instance running if sync fails.
- Updated local Docker E2E scripts to use git-aware local packaging that excludes ignored files and includes tracked/staged/unstaged intended changes.
- Updated docs, default configs, local/remote Docker build flow, and AWS EC2 image build/deploy metadata for the new plugin path and managed-SSH transfer image.

Verification completed:

- `PYTHONPATH=plugins/cloud-agent-app/src:core/python pytest plugins/cloud-agent-app/tests/test_cloud_agent_app_plugin.py -q`
- `PYTHONPATH=core/python:application/python pytest application/python/tests/test_cloud_agent_runtime.py -q`
- `mix test` in `cloud-orchestrator`
- `mix format --check-formatted` in `cloud-orchestrator`
- `npm test --prefix packages/frontend-sdk -- cloud-orchestrator.e2e.integration.test.ts`
- `RUN_CLOUD_ORCHESTRATOR_E2E=1 npm test --prefix packages/frontend-sdk -- cloud-orchestrator.e2e.integration.test.ts`

Deployment revalidation status:

- Local Docker E2E passed with the real managed-SSH rsync transfer path.
- Remote Docker deployment scripts were updated to build `cloud-agent-transfer-ssh:latest`; a live remote host run was not performed in this environment.
- AWS EC2/CloudFront build/deploy templates were updated to build, push, pull, and tag a transfer SSH image; a live AWS deployment was not performed in this environment.