# Cloud workspace requirements

These requirements track live implementation, verification, documentation, and
evidence relative to the cloud workspace target.

| ID | Requirement | Implementation | Verification | Documentation | Evidence |
|---|---|---|---|---|---|
| CWS-001 | Connection, route, workspace-instance, and runtime records survive orchestrator restart in the configured durable data directory. | Not started | Unverified | Pending | `tasks/20260806-cloud-workspace-runtime-model/010-durable-orchestrator-state-and-stable-connections.md` |
| CWS-002 | New connection-scoped credentials remain valid until explicit rotation, revocation, or connection deletion rather than expiring solely with time. | Not started | Unverified | Pending | `tasks/20260806-cloud-workspace-runtime-model/010-durable-orchestrator-state-and-stable-connections.md` |
| CWS-003 | Orchestrator restart rediscovers labeled managed Docker containers and restores proxy/readiness behavior. | Not started | Unverified | Pending | `tasks/20260806-cloud-workspace-runtime-model/010-durable-orchestrator-state-and-stable-connections.md` |
| CWS-004 | Missing, corrupt, unsupported, and orphaned durable/runtime state is reported safely without silent destructive cleanup. | Not started | Unverified | Pending | `tasks/20260806-cloud-workspace-runtime-model/010-durable-orchestrator-state-and-stable-connections.md` |
| CWS-005 | Durable workspace state and runtime process state are represented separately under the existing instance identity. | Not started | Unverified | Pending | `tasks/20260806-cloud-workspace-runtime-model/020-workspace-runtime-lifecycle-and-control.md` |
| CWS-006 | Runtime start, stop, retry, status, desired state, and observed state are idempotent durable orchestrator operations. | Not started | Unverified | Pending | `tasks/20260806-cloud-workspace-runtime-model/020-workspace-runtime-lifecycle-and-control.md` |
| CWS-007 | Connection health, cloud runtime settings/actions, status, and notifications remain available while the runtime is stopped. | Not started | Unverified | Pending | `tasks/20260806-cloud-workspace-runtime-model/020-workspace-runtime-lifecycle-and-control.md` |
| CWS-008 | Runtime-dependent APIs report stopped/starting/failed state without invalidating or deleting the saved app connection. | Not started | Unverified | Pending | `tasks/20260806-cloud-workspace-runtime-model/020-workspace-runtime-lifecycle-and-control.md` |
| CWS-009 | Mobile and desktop can start/stop through connection settings/actions and refresh runtime-backed state after readiness. | Not started | Unverified | Pending | `tasks/20260806-cloud-workspace-runtime-model/020-workspace-runtime-lifecycle-and-control.md` |
| CWS-010 | Users can create a cloud workspace through an application-level action without selecting a session. | Not started | Unverified | Pending | `tasks/20260806-cloud-workspace-runtime-model/030-application-workspace-creation-and-complete-transfer.md` |
| CWS-011 | Workspace creation transfers all configured agents and the referenced provider/plugin configuration needed to use them. | Not started | Unverified | Pending | `tasks/20260806-cloud-workspace-runtime-model/030-application-workspace-creation-and-complete-transfer.md` |
| CWS-012 | Workspace creation transfers every live session with its ID and session-owned assets while excluding snapshot and transient event history. | Not started | Unverified | Pending | `tasks/20260806-cloud-workspace-runtime-model/030-application-workspace-creation-and-complete-transfer.md` |
| CWS-013 | Workspace creation reports background progress, completion, retry, and failure through application operations and durable application notifications. | Not started | Unverified | Pending | `tasks/20260806-cloud-workspace-runtime-model/030-application-workspace-creation-and-complete-transfer.md` |
| CWS-014 | The source application durably records created workspace/connection identity and lifecycle metadata in plugin-owned runtime state. | Not started | Unverified | Pending | `tasks/20260806-cloud-workspace-runtime-model/030-application-workspace-creation-and-complete-transfer.md` |
| CWS-015 | `cloud.start_session_agent` remains a compatibility wrapper over complete workspace creation. | Not started | Unverified | Pending | `tasks/20260806-cloud-workspace-runtime-model/030-application-workspace-creation-and-complete-transfer.md` |
| CWS-016 | Existing transfer/setup/install/export/apply/validation script phases and project profile overrides remain supported. | Implemented | Automated | Documented | `plugins/cloud-agent-app/tests`; `plugins/cloud-agent-app/README.md`; `plugins/cloud-agent-app/docs/cloud-script-authoring.md`; target preservation in tasks 030 and 040 |
| CWS-017 | The new default transfer profile materializes complete supported reachable Git history, branches, tags, metadata, and current worktree state. | Not started | Unverified | Pending | `tasks/20260806-cloud-workspace-runtime-model/040-full-git-clone-and-remote-sync.md` |
| CWS-018 | Cloud setup restores the original upstream as `origin` without embedding credentials in repository transfer material. | Not started | Unverified | Pending | `tasks/20260806-cloud-workspace-runtime-model/040-full-git-clone-and-remote-sync.md` |
| CWS-019 | Sync-down creates or updates a stable local cloud remote and fetches cloud refs without mutating checked-out local branches or worktree state. | Not started | Unverified | Pending | `tasks/20260806-cloud-workspace-runtime-model/040-full-git-clone-and-remote-sync.md` |
| CWS-020 | Existing patch and branch-import profiles remain selectable and compatible after the new default is introduced. | Not started | Unverified | Pending | `tasks/20260806-cloud-workspace-runtime-model/040-full-git-clone-and-remote-sync.md`; existing profile tests/docs are baseline evidence only |
| CWS-021 | A local session and its assets can be added to a selected running cloud workspace without repository transfer. | Not started | Unverified | Pending | `tasks/20260806-cloud-workspace-runtime-model/050-single-session-exchange.md` |
| CWS-022 | A cloud session and its assets can be imported locally without repository transfer. | Not started | Unverified | Pending | `tasks/20260806-cloud-workspace-runtime-model/050-single-session-exchange.md` |
| CWS-023 | Directional session sync preserves IDs, requires explicit overwrite, and refreshes affected UI state. | Not started | Unverified | Pending | `tasks/20260806-cloud-workspace-runtime-model/050-single-session-exchange.md` |
| CWS-024 | Workspace Git access uses a newly generated per-workspace keypair and never transfers an existing local user private key. | Not started | Unverified | Pending | `tasks/20260806-cloud-workspace-runtime-model/060-github-workspace-credential-lifecycle.md` |
| CWS-025 | GitHub workspace creation can register a writable deploy key through the logged-in source `gh` session and use it for fetch/push. | Not started | Unverified | Pending | `tasks/20260806-cloud-workspace-runtime-model/060-github-workspace-credential-lifecycle.md` |
| CWS-026 | GitLab workspace creation can register a writable expiring deploy key through the logged-in source `glab` session and use it for fetch/push. | Not started | Unverified | Pending | `tasks/20260806-cloud-workspace-runtime-model/070-gitlab-workspace-credential-support.md` |
| CWS-027 | Provider private keys remain only in protected cloud workspace state and are excluded from bundles, sync, config assets, links, notifications, action results, control records, and logs. | Not started | Unverified | Pending | `tasks/20260806-cloud-workspace-runtime-model/060-github-workspace-credential-lifecycle.md`; `tasks/20260806-cloud-workspace-runtime-model/070-gitlab-workspace-credential-support.md` |
| CWS-028 | Supported workspace removal stops runtime, revokes or confirms absence/expiry of provider access when applicable, deletes workspace/control state, and revokes the cloud connection in order. | Not started | Unverified | Pending | `tasks/20260806-cloud-workspace-runtime-model/060-github-workspace-credential-lifecycle.md`; GitLab extension in `tasks/20260806-cloud-workspace-runtime-model/070-gitlab-workspace-credential-support.md` |
| CWS-029 | Provider revocation failure preserves a stopped, retryable deletion state and is not reported as successful removal. | Not started | Unverified | Pending | `tasks/20260806-cloud-workspace-runtime-model/060-github-workspace-credential-lifecycle.md`; `tasks/20260806-cloud-workspace-runtime-model/070-gitlab-workspace-credential-support.md` |
| CWS-030 | Runtime control remains available without the source server, while guaranteed provider credential deletion requires source credential-manager participation in the first target. | Not started | Unverified | Pending | `tasks/20260806-cloud-workspace-runtime-model/020-workspace-runtime-lifecycle-and-control.md`; tasks 060 and 070 |
| CWS-031 | Every transferred, cloud-created, or later-added cloud session is registered to its workspace route and remains visible through the connection-level session API. | Not started | Unverified | Pending | `tasks/20260806-cloud-workspace-runtime-model/030-application-workspace-creation-and-complete-transfer.md`; `tasks/20260806-cloud-workspace-runtime-model/050-single-session-exchange.md` |
| CWS-032 | Active and terminal connection-control notification state survives orchestrator restart and remains available independently of runtime state. | Not started | Unverified | Pending | `tasks/20260806-cloud-workspace-runtime-model/020-workspace-runtime-lifecycle-and-control.md` |

## Primary work evidence

- `tasks/20260806-cloud-workspace-runtime-model/000-main.md`
- `tasks/20260806-cloud-workspace-runtime-model/010-durable-orchestrator-state-and-stable-connections.md`
- `tasks/20260806-cloud-workspace-runtime-model/020-workspace-runtime-lifecycle-and-control.md`
- `tasks/20260806-cloud-workspace-runtime-model/030-application-workspace-creation-and-complete-transfer.md`
- `tasks/20260806-cloud-workspace-runtime-model/040-full-git-clone-and-remote-sync.md`
- `tasks/20260806-cloud-workspace-runtime-model/050-single-session-exchange.md`
- `tasks/20260806-cloud-workspace-runtime-model/060-github-workspace-credential-lifecycle.md`
- `tasks/20260806-cloud-workspace-runtime-model/070-gitlab-workspace-credential-support.md`

Implementation tasks must replace task-only evidence with concrete code, test,
documentation, review, and delivery references as each requirement progresses.
