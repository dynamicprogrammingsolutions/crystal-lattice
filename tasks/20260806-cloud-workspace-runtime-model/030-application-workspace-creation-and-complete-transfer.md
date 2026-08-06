# Application-level workspace creation and complete transfer

Create a cloud workspace independently of a selected session and transfer the
complete configured application, all live sessions, and session-owned assets.

Parent Task: `tasks/20260806-cloud-workspace-runtime-model/000-main.md`
Depends On: `tasks/20260806-cloud-workspace-runtime-model/020-workspace-runtime-lifecycle-and-control.md`

Specification:
`plugins/cloud-agent-app/docs/development/specifications/cloud-workspaces/index.md`

Requirements: `CWS-010`, `CWS-011`, `CWS-012`, `CWS-013`, `CWS-014`,
`CWS-015`, `CWS-016`, `CWS-031`.

## Requirements checklist

- [ ] Users can create a cloud workspace from an application-level action without selecting a session.
- [ ] Workspace creation transfers all configured agents and their referenced providers/plugins.
- [ ] Workspace creation transfers every live session with its existing ID.
- [ ] Session-owned assets are available in the cloud runtime.
- [ ] Every transferred session is routed to the created workspace so it is visible through the connection-level session API.
- [ ] Snapshot history and transient events are explicitly excluded from the initial transfer contract.
- [ ] Creation progress, completion, retry, and failure are presented through application operations and durable application notifications.
- [ ] The local source server maintains a durable plugin-owned registry of created workspaces.
- [ ] The legacy session-start action remains available as a compatibility wrapper over the new creation flow.
- [ ] Existing project profile and script overrides continue to work.

## Supporting details

The portable config builder should stop optimizing workspace creation to one
selected agent. The runtime bootstrap should materialize complete session and
asset stores before constructing `AgentApplication`.

The plugin registry belongs under `app.get_runtime_state_root()` and records
connection/workspace identity, lifecycle status, source directory, and
credential-management metadata without becoming the orchestrator source of
truth.

## Execution plan
Status: Draft

### Stage 1 — Complete portable application bundle

Package all agents, required provider/plugin definitions, config assets, and
runtime environment references. Preserve current cloud-control stripping and
portable path rewriting.

Stage completion is testable by starting through the legacy flow and selecting
multiple transferred agents.

### Stage 2 — Complete session and asset bundle

Enumerate all live sessions through application APIs, export each with its
original ID, copy session assets, and materialize both stores in the runtime.
Register every transferred session route to the created workspace and define
deterministic behavior for sessions changing during bundle creation.

Stage completion is testable by comparing local and cloud session/asset sets.

### Stage 3 — Application-level creation workflow

Add `cloud.create_workspace`, application UI schema, managed background
operation, durable application notification progress, workspace registry, and
stable connection result. Reimplement `cloud.start_session_agent` as a
compatibility wrapper that may still attach metadata to its initiating session.

Stage completion is testable without opening or selecting a session.

### Implementation decisions and open questions

- Session transfer is a point-in-time snapshot; detailed planning must choose
  locking or per-session consistency behavior without blocking unrelated work
  longer than necessary.
- Session assets are included; snapshots and event history are not.
- The workspace registry may store connection secrets only with restrictive
  permissions and must not duplicate provider private keys.

### Documentation

- Update cloud-agent user workflow from session-owned startup to workspace
  creation while documenting the compatibility action.
- Document complete-agent/session transfer boundaries and excluded history.
- Document workspace registry location, purpose, and recovery behavior.

### Task checklist

- [ ] Finalize portable bundle and consistency contracts.
- [ ] Implement and verify Stage 1.
- [ ] Report multi-agent cloud behavior.
- [ ] Implement and verify Stage 2.
- [ ] Report complete session/asset comparison procedure.
- [ ] Implement and verify Stage 3.
- [ ] Report application-level creation and legacy compatibility workflow.
- [ ] Update specification requirements and current documentation with evidence.

### Requirement verification

Required automated coverage:

- Extend cloud-agent plugin tests for complete portable config selection,
  all-session export, session assets, route registration, workspace registry,
  operation admission, notifications, retry, and legacy wrapper behavior.
- Add/extend real `AgentApplication` and FastAPI integration tests for the
  application-level action, application notification lifecycle, and
  connection-level session visibility.
- Extend local Docker `integration:cloud` with a multi-agent, multi-session,
  asset-bearing fixture that creates a workspace without a selected session,
  reconnects through `CloudTransport`, lists all sessions, uses multiple
  agents, and creates a new routed cloud session.
- Extend installed/default runtime bundle tests where complete plugin/config
  packaging changes their boundary.
- Run `integration:cloud:profiles` to prove project override and hook
  compatibility.
- Add an AWS fresh-build scenario for application-level creation and complete
  session visibility through the public CloudFront connection.
- Explicitly consider `integration:cloud:codex` or the relevant hosted-provider
  slice when default-config/runtime-bundle changes affect real provider
  loading; if not run, record why provider behavior is unchanged.

Detailed planning chooses fixtures and provider combinations. The complete
agent/session/asset behavior must be asserted automatically through the public
cloud flow.

### Additional implementation verification

- A failed background stage leaves a retryable notification and does not
  publish a false workspace record.
- Secrets excluded by current config/runtime policies remain excluded.
- Large multi-session bundles report meaningful progress rather than appearing
  stalled.
- Existing plugin unit tests and local cloud session-start e2e remain green to
  prove legacy compatibility.
