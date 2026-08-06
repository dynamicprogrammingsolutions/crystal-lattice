# Workspace/runtime lifecycle and always-on control

Separate durable workspace state from runtime process state and keep the cloud
connection control surface available while the runtime is stopped.

Parent Task: `tasks/20260806-cloud-workspace-runtime-model/000-main.md`
Depends On: `tasks/20260806-cloud-workspace-runtime-model/010-durable-orchestrator-state-and-stable-connections.md`

Specification:
`plugins/cloud-agent-app/docs/development/specifications/cloud-workspaces/index.md`

Requirements: `CWS-005`, `CWS-006`, `CWS-007`, `CWS-008`, `CWS-009`,
`CWS-030`, `CWS-032`.

## Requirements checklist

- [ ] Stopping a runtime preserves the workspace record, storage, connection, sessions, config, and repository files.
- [ ] Starting a runtime creates a new runner process against the existing workspace and restores session access after readiness.
- [ ] Desired runtime state and observed runtime state are persisted separately.
- [ ] Connection settings, cloud control actions, status, health, and notifications remain usable while the runtime is stopped.
- [ ] Connection-control notification state and history survive orchestrator restart.
- [ ] Users can start, stop, and retry the runtime through both a connection setting and connection-level actions.
- [ ] Runtime-dependent APIs communicate stopped/unavailable state without invalidating the saved cloud connection.
- [ ] Mobile and desktop keep the connection usable and refresh runtime-backed data after startup completes.

## Supporting details

The current `instance_id` remains the workspace handle. The setting
`cloud_runtime_enabled` expresses desired state. Start/stop actions and setting
mutations invoke the same idempotent lifecycle operations.

The orchestrator terminates a narrow always-on control API and proxies runtime
data APIs only while the runtime is ready. Runtime-owned settings/actions are
merged when running and omitted or reported unavailable while stopped.

## Execution plan
Status: Draft

### Stage 1 — Runner lifecycle

Extend runner and registry contracts with start, stop, retry, and status.
Persist desired/observed runtime states and recreate Docker containers using
the existing workspace directory and stored container profile. Keep legacy
close behavior compatible until destructive workspace deletion is introduced.

Stage completion is testable through orchestrator APIs and Docker inspection.

### Stage 2 — Always-on connection control

Serve connection health, runtime setting/schema, cloud control actions/schema,
status, and durable notifications at the orchestrator. Persist notification
state/history across orchestrator restart, route control-owned mutations
locally, and merge or proxy runtime-owned values while running. Define
structured stopped-runtime responses for sessions, agents, messages, and events.

Stage completion allows control through the existing REST backend even with no
runtime container.

### Stage 3 — Frontend stopped-runtime experience

Update shared SDK, mobile, and desktop behavior so runtime unavailability does
not delete or reject the cloud connection. Expose the runtime checkbox and
actions, retain cached session context, show transition notifications, and
reload runtime-backed state after readiness.

Stage completion is directly testable in mobile and desktop.

### Implementation decisions and open questions

- Desired `true` may restart a missing runtime during orchestrator recovery;
  the UI description must make this cost behavior explicit.
- Use plugin/owner identity `cloud_control` for orchestrator-owned actions and
  settings to avoid collisions.
- Decide during detailed planning whether `GET /sessions` returns a structured
  503 or an extended successful envelope while stopped. It must not falsely
  represent the durable session store as empty.

### Documentation

- Document runtime state transitions and setting semantics.
- Document which routes remain available while stopped.
- Document frontend stopped/starting/failed presentation and operator recovery.

### Task checklist

- [ ] Finalize runtime state machine and route ownership contract.
- [ ] Implement and verify Stage 1.
- [ ] Report direct API and Docker start/stop procedure.
- [ ] Implement and verify Stage 2.
- [ ] Report always-on control behavior with the runtime stopped.
- [ ] Implement and verify Stage 3.
- [ ] Report mobile/desktop user workflow and any required human presentation checks.
- [ ] Update specification requirements and current documentation with evidence.

### Requirement verification

Required automated coverage:

- Extend orchestrator runner, registry, router, and notification tests for the
  runtime state machine, idempotent/conflicting operations, control/runtime
  route ownership, desired-state replay, and durable notifications.
- Extend frontend SDK server-settings, application-action, notification, and
  cloud transport tests for stopped/starting/running/failed responses and
  post-readiness invalidation.
- Add mobile and desktop component/integration tests that keep the connection
  visible, expose runtime controls, retain cached session context, and refresh
  after readiness. Run package-local Jest/integration suites and shared
  frontend package tests.
- Extend local Docker `integration:cloud` to stop the runtime through both the
  setting and action, use control endpoints while stopped, restart it, and use
  the same session through the same connection.
- Add orchestrator process/container restart cases for desired state true and
  false, including notification history recovery.
- Extend `integration:cloud:aws:fresh` with at least one stopped-control and
  restart scenario against the persisted AWS data volume.

Detailed planning may decide whether native UI automation is needed after
component/integration coverage. Human presentation verification is required
only if a material visual behavior cannot be asserted by those suites.

### Additional implementation verification

- Concurrent start/stop requests are idempotent or rejected with an explicit
  conflict.
- Runtime startup failure leaves the workspace and control connection usable.
- Runtime-owned settings/actions retain current behavior while running.
- Existing backend server-settings and notification HTTP integration tests
  remain green after cloud control interception is added.
