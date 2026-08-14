# Cloud workspaces technical specification

## Architectural boundary

The Cloud Agent App plugin owns:

- workspace creation workflow and background operation;
- portable application/session/asset bundle construction;
- repository transfer and sync profile selection;
- project script execution;
- local workspace registry;
- single-session exchange semantics;
- provider credential issuance and revocation workflow;
- user-facing action and notification content.

The cloud orchestrator owns:

- durable connection, route, workspace-instance, and runtime records;
- connection authorization and explicit revocation;
- transfer slots and build contexts;
- runner start/stop/status/reconciliation;
- always-on connection control routes;
- proxy routing to a ready runtime.

The runner owns backend-specific process and mount behavior. The runtime owns
materialization, application boot, session import/export, and project script
execution inside the workspace.

## Compatibility model

The first target retains:

- `connection_id` as the logical cloud connection identifier;
- `instance_id` as the durable workspace handle;
- existing `/connections` and `/instances` API families;
- current managed-SSH transfer slots;
- transfer-up, sync-down, and container profile contracts;
- standard `.cloud-agent/local-stage`, `.cloud-agent/install-cloud`, and
  `.cloud-agent/validate-cloud` hooks;
- existing patch and branch-import profiles;
- `cloud.start_session_agent` as a compatibility action.

No parallel public `/workspaces` resource is required initially. Public and
internal responses add workspace/runtime fields without changing existing
identifiers.

## Durable state

The configured orchestrator data directory is the single-node persistence
root. It contains versioned atomic manifests alongside existing data:

```text
data_dir/
  connections/<connection_id>/connection.json
  instances/<instance_id>/instance.json
  instances/<instance_id>/workspace/
  instances/<instance_id>/sessions/
  instances/<instance_id>/config/
  instances/<instance_id>/env/
  instances/<instance_id>/state/
  instances/<instance_id>/logs/
  build-contexts/
  transfers/
  runtime-cache/
```

GenServers cache and serialize durable state; they are not the source of truth.
Manifest replacement uses temporary-file write, flush/close, and atomic rename.
Every manifest has a schema version. Unsupported or corrupt manifests remain
on disk and produce an explicit recovery error.

Connection manifests contain at least:

- identity and stable connection key;
- active/deleting/deleted state;
- credential version;
- default and member instance IDs;
- session routes;
- timestamps.

Instance manifests contain at least:

- instance/workspace and connection identity;
- workspace lifecycle state;
- desired runtime state;
- observed runtime state and diagnostics;
- container profile/build identity needed to restart;
- transfer/materialization completion state;
- timestamps.

Runtime-only observations such as container ID, published port, and proxy URL
may be persisted but are reconciled against the runner.

## Stable connection authorization

New connection-scoped credentials do not expire solely because time passes.
They are valid only when:

- the signature is valid;
- the durable connection exists and is active;
- the credential version in the token matches the connection record.

Rotation increments the durable credential version and invalidates previous
tokens. Deletion revokes the connection. Legacy instance-scoped tokens retain
their existing age behavior during migration.

The frontend continues to persist the cloud connection record. A saved
connection must distinguish unavailable orchestrator, revoked connection,
stopped runtime, starting runtime, failed runtime, and deleted workspace.

Per-device credentials and one-time claim links are deferred.

## Docker reconciliation

Managed containers carry labels for:

- managed marker;
- instance/workspace ID;
- connection ID.

At startup the orchestrator loads manifests, lists labeled containers, and
reconciles:

- expected running container present: inspect, restore proxy metadata, probe
  readiness;
- expected starting container present: resume readiness monitoring;
- manifest says running but container absent: preserve workspace and mark
  stopped or failed with recovery detail;
- desired stopped and container absent: normal stopped state;
- desired stopped and container present: stop it;
- labeled container with matching manifest: adopt it;
- labeled container without matching identity: report orphan, do not silently
  delete.

## Workspace and runtime lifecycle

Workspace state and runtime state are separate.

Workspace states include:

- `active`;
- `deleting`;
- `credential_revocation_failed`;
- `deleted`.

Desired runtime state is `running` or `stopped`. Observed runtime states
include:

- `starting`;
- `running`;
- `stopping`;
- `stopped`;
- `failed`.

Runner operations are idempotent:

- ensure runtime running;
- ensure runtime stopped;
- retry failed runtime;
- inspect/reconcile runtime.

Stopping removes the Docker container but preserves workspace storage and the
connection. Starting creates a new container with the stored container profile
and existing mounts. Runtime bootstrap detects prior materialization and
reloads existing config/session/workspace state.

## Always-on connection control

The cloud connection has an orchestrator-served control surface independent of
runtime state. The connection proxy intercepts or dispatches:

- connection health;
- server settings values and schema;
- cloud control application actions and UI schema;
- connection-level notifications and dismissal;
- runtime status.

Connection-control notifications use the portable application-notification
record and revision semantics where applicable. Their active and terminal
state is durable across orchestrator restart and remains separate from
runtime-owned application notifications.

The setting:

```json
{
  "ui_type": "config",
  "scope": "server",
  "key": "cloud_runtime_enabled",
  "type": "checkbox"
}
```

expresses desired runtime state. `cloud_control` start, stop, and retry actions
invoke the same lifecycle operations.

When running, orchestrator-owned and runtime-owned settings/actions/schema are
merged by ownership. The orchestrator handles the runtime setting and
`cloud_control` actions; other keys/actions proxy to the runtime. While stopped,
only control-owned values are available.

Runtime-dependent APIs return a structured unavailable result that preserves
connection identity and runtime state. Frontends keep the saved connection and
cached session context. Readiness completion triggers invalidation of sessions,
application actions, and server settings/schema.

The exact stopped `GET /sessions` envelope may be selected during detailed
planning, but it must not falsely represent durable sessions as absent.

## Workspace creation

`cloud.create_workspace` is an application-level action and does not require a
session ID. It:

1. registers an application operation;
2. creates a durable application notification;
3. resolves source workspace and profiles;
4. packages the complete portable application;
5. exports all live sessions and session assets;
6. runs local stage and transfer scripts;
7. uploads build context and workspace payload;
8. creates the durable cloud instance/workspace and connection;
9. starts and waits for runtime readiness;
10. records the workspace in the local plugin registry;
11. completes the notification with connection follow-up actions.

Notification phases include preparation, agent/config export, session export,
repository transfer, upload, provisioning, runtime startup, readiness,
completion, and failure/retry.

The local registry lives below `app.get_runtime_state_root()` and stores
workspace/connection identity, source directory, status, timestamps, and
credential management metadata. Secret fields require restrictive file
permissions and must not duplicate provider private keys.

The portable bundle includes all agents and referenced provider/plugin
configuration. It retains existing cloud-control stripping, portable path
rewriting, config-asset policy, and runtime-env policy.

All live sessions are exported with existing IDs. Session-owned assets are
included. Snapshot selection/history and transient event history are excluded.
Detailed implementation must provide point-in-time per-session consistency and
must not publish a successful workspace record for a partial bundle.

Every transferred session ID is registered to the created connection/workspace
route before creation is reported complete. Sessions later created in cloud or
added through session exchange are registered to the same workspace route.
Connection-level session listing must not hide transferred sessions merely
because no individual session initiated workspace creation.

`cloud.start_session_agent` invokes the same creation implementation and may
retain initiating-session attachment metadata for compatibility.

## Repository transfer and synchronization

The new default transfer-up profile uses a Git bundle and metadata:

- all supported reachable branches and tags;
- source HEAD and current branch;
- original upstream URL;
- Git identity metadata;
- staged, unstaged, binary, and non-ignored untracked worktree state.

Cloud setup clones from the bundle, restores the original upstream as `origin`,
and applies the worktree state. Credential data is not embedded.

The matching sync-down profile exports cloud refs to a bundle. Local apply:

- atomically stores the latest usable bundle below local Git state;
- creates or updates a stable workspace-specific remote;
- fetches supported refs into that remote-tracking namespace;
- does not checkout, merge, rebase, reset, or delete local branches.

Current patch and branch-import profiles remain available. Project overrides
retain the existing local-stage, transfer, cloud-setup, install, export,
mark-synced, apply, and validation script phases.

Linked worktrees, ignored build outputs, unreachable objects, private
submodules, and additional repositories are excluded initially.

## Single-session exchange

Session-only operations use portable session-plus-assets payloads and do not
invoke repository transfer.

Supported actions:

- add local session to cloud;
- import cloud session locally;
- sync local copy up;
- sync cloud copy down.

The runtime must be running in the first target. Import saves through
`AgentApplication`; export uses the runtime session export contract. IDs are
preserved. A session added to cloud is registered to the selected workspace
route before success is returned. Destination existence requires explicit
overwrite confirmation. Destination-side snapshots are preferred when
supported. No session merge is defined.

## Provider-issued Git credentials

Credential transfer is explicit and opt-in. The plugin generates a new
workspace-specific Ed25519 keypair and never reads or transfers an existing
user private key.

Provider-neutral metadata records:

- provider and host;
- primary repository identity;
- provider credential/deploy-key ID;
- title and public-key fingerprint;
- creation and optional expiration;
- active/revoking/revocation-failed/revoked state.

The private key exists only under protected cloud workspace state and is
referenced by instance-local SSH configuration. It is excluded from
repository/workspace sync payloads, config assets, connection links,
notifications, action results, logs, and control manifests.

GitHub issuance uses the source server's logged-in `gh` session to register a
writable deploy key for the primary repository. GitLab issuance uses `glab`,
registers a writable deploy key, and applies a configurable expiration.

Protected branches and repository policy remain effective. Private submodules
and additional repositories require future credentials.

## Destructive workspace removal

Supported removal is ordered:

1. mark workspace deleting;
2. stop runtime;
3. revoke or confirm absence/expiry of provider credential;
4. delete provider private key and workspace storage;
5. remove durable instance/route/connection records;
6. revoke the cloud connection;
7. update local registry and notification.

For a workspace without a provider credential, step 3 is explicitly not
applicable and the remaining ordered deletion still applies.

If provider revocation fails, the workspace remains in
`credential_revocation_failed`, retains enough metadata to retry, keeps the
runtime stopped, and is not reported deleted.

Guaranteed provider revocation requires source-server participation in the
first target. Remote clients may stop/start runtimes but cannot finalize
destructive deletion alone.

## Security and privacy

- Durable connection credentials are explicitly revocable.
- Provider private keys are workspace-specific and protected at rest.
- Existing user Git private keys are never transferred.
- Control manifests never contain provider private keys.
- Logs and bounded errors redact tokens, keys, and authorization headers.
- Transfer and sync exclusion tests cover provider private keys.
- Self-managed GitLab host routing never sends credentials to another host.
- Connection and workspace deletion is auditable through durable state and
  notification outcomes.

## Failure behavior

- Manifest write failure does not report mutation success.
- Corrupt manifests remain available for operator recovery.
- Runtime failure preserves workspace and control connection.
- Creation failure leaves a retryable application notification and no false
  completed registry entry.
- Session asset failure does not save a session with broken references.
- Git sync failure preserves the previous usable local bundle/remote state.
- Provider API failure preserves revocation metadata and blocks final deletion.

## Migration

- Existing default and project profiles continue to resolve.
- New default config selects full-clone/remote-sync profiles; explicitly
  configured old profiles are unchanged.
- Existing session-start action remains available.
- Existing identifiers and connection links remain parseable.
- Legacy expiring tokens remain valid under their original contract until
  expiry; newly issued connection credentials use the durable contract.
- Existing running instances without manifests require an explicit
  compatibility discovery/adoption policy during task 010 planning and are
  never silently deleted.

## Verification strategy

Automated verification is required at the lowest useful level and at the
public boundaries crossed by each behavior.

### Package and protocol coverage

- `plugins/cloud-agent-app/tests` covers plugin actions, profile/config
  resolution, transfer construction, portable config/session/asset packaging,
  provider adapters, secret exclusion, and error behavior.
- `cloud-orchestrator/test` covers token, durable manifest, registry, router,
  runner, runtime state machine, reconciliation, and control/runtime dispatch
  contracts.
- focused `application/python/tests` covers real `AgentApplication`, FastAPI,
  runtime bootstrap/import/export, notifications, settings/actions, installed
  bundles, and local Docker validation.
- frontend SDK and React/RN package tests cover transport dispatch,
  controllers, invalidation, cached state, and stopped-runtime presentation
  contracts.
- mobile and desktop component/integration/native suites cover their production
  settings, action, notification, and connection surfaces when changed.

### Local Docker end-to-end

The existing frontend SDK cloud harness is the primary acceptance boundary:

```text
frontend SDK
  → local FastAPI application and cloud plugin action
  → managed transfer
  → real cloud orchestrator
  → real Docker runtime
  → connection-scoped CloudTransport
  → export/sync back
```

`integration:cloud` is extended for restart/reconnect, runtime stop/start,
complete application/session transfer, session exchange, and credential-aware
flows. `integration:cloud:profiles` is extended for full-clone/remote-sync and
legacy profile compatibility. Tests must use public HTTP, production
transports, shipped scripts, and normal runtime images.

### Remote and AWS deployment coverage

Persistence, reconciliation, runtime lifecycle, default runtime/config
packaging, and managed-SSH storage behavior require gated deployed coverage:

- remote Docker external-mode smoke where appropriate;
- AWS EC2 + CloudFront fresh-image e2e using the persistent data volume.

Required scenarios restart the deployed orchestrator while preserving storage,
reconnect with the saved connection, control a stopped runtime, and exercise
the task-specific public workflow. Gating or cost does not make these manual;
if credentials or infrastructure are unavailable, they remain explicitly not
run.

### Provider credential coverage

GitHub and GitLab support requires:

- controlled adapter/unit tests;
- local Docker tests with a disposable SSH Git server;
- gated real provider repository/project tests that create, query, use, revoke,
  and verify cleanup of deploy keys through `gh` or `glab` authenticated APIs.

Provider web-page inspection is not required when API assertions can prove the
state.

### Manual verification

Manual verification is limited to material native presentation or external
observations that the existing automated suites cannot assert. It supplements
rather than replaces automated acceptance evidence.

Detailed subtask planning chooses exact test case names, fixtures, and focused
commands. It may combine scenarios for efficiency but may not remove the
required behavior boundaries. Stage reports link concrete executed evidence in
[requirements.md](requirements.md), and skipped gated suites are recorded as
not run.
