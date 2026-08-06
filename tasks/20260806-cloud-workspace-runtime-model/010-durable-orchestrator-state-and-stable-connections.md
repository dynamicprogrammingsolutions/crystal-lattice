# Durable orchestrator state and stable connections

Make existing cloud connections and Docker-backed instances recoverable across
orchestrator restart while replacing expiring connection access with durable,
explicitly revocable authorization.

Parent Task: `tasks/20260806-cloud-workspace-runtime-model/000-main.md`

Specification:
`plugins/cloud-agent-app/docs/development/specifications/cloud-workspaces/index.md`

Requirements: `CWS-001`, `CWS-002`, `CWS-003`, `CWS-004`.

## Requirements checklist

- [ ] Connection, instance, route, and connection-key state survives orchestrator restart.
- [ ] Saved connection-scoped cloud credentials remain valid until explicit revocation or rotation.
- [ ] Legacy instance-scoped token behavior remains compatible during migration.
- [ ] Running managed Docker containers are rediscovered and become proxyable after orchestrator restart.
- [ ] Missing or orphaned managed containers are reported through explicit recoverable state instead of being silently ignored or deleted.
- [ ] Existing cloud creation, proxy, export, sync, and close flows continue to work.

## Supporting details

Use atomic file-backed manifests under the existing orchestrator data
directory. GenServers remain serialized caches over durable state. Managed
containers receive labels containing the connection and instance identifiers.
Docker inspection reconstructs runtime-only values such as container ID,
published port, and proxy URL.

The first implementation remains single-node. It does not need a general SQL
database or distributed lock service.

## Execution plan
Status: Draft

### Stage 1 — Durable manifests and authorization

Define versioned connection and instance manifest shapes. Persist all registry
mutations atomically, rebuild indexes at startup, and validate new
connection-scoped credentials against the durable active connection and
credential version. Preserve current public response shapes where possible and
define migration behavior for existing links.

Stage completion exposes the current cloud flow with durable records and
stable saved connections under the in-memory runner and controlled restart
tests.

### Stage 2 — Docker labels and reconciliation

Label every managed runtime container, inspect labeled containers on startup,
restore proxy/readiness metadata, resume readiness monitoring, and distinguish
running, stopped, missing, failed, and orphaned states. Exercise an actual
orchestrator restart while leaving the runtime container and host storage in
place.

Stage completion lets a user restart the orchestrator and reconnect to the
same running cloud runtime through the saved app connection.

### Implementation decisions and open questions

- Persist runtime observations but reconcile them against Docker at startup.
- Treat manifests as authoritative for workspace/connection existence and
  Docker as authoritative for current process existence.
- Do not automatically delete orphaned containers.
- Resolve the exact token claim/version shape during detailed planning while
  preserving explicit revocation.

### Documentation

- Document manifest locations, schema versioning, recovery behavior, token
  lifecycle, labels, and operator-visible orphan states.
- Keep deployment instructions explicit that the orchestrator data directory
  must be backed by durable host storage.

### Task checklist

- [ ] Specify manifest and credential compatibility contracts.
- [ ] Implement and verify Stage 1.
- [ ] Report Stage 1 behavior and restart test procedure.
- [ ] Implement and verify Stage 2.
- [ ] Report Stage 2 Docker recovery behavior and user test procedure.
- [ ] Update specification requirements and current documentation with evidence.

### Requirement verification

Required automated coverage:

- Extend orchestrator token, registry, and router tests for manifest reload,
  credential age/rotation/revocation, corrupt versions, and route recovery;
  run `(cd cloud-orchestrator && mix test)`.
- Add process-restart integration that starts a real orchestrator process,
  persists records, restarts it, and verifies the same public connection,
  routes, and instance state. Reconstructing registry state directly is not
  sufficient.
- Extend `cloud-orchestrator.e2e.integration.test.ts` in local Docker mode to
  leave the runtime running, restart the orchestrator container, reconnect
  through the previously saved `CloudTransport`, and use a routed session.
- Use controlled time in token tests to cross the former 24-hour boundary and
  prove durable connection validity plus explicit rotation/revocation.
- Add a gated remote Docker or AWS fresh-build scenario that restarts the
  deployed orchestrator while preserving its host/EBS data volume, then
  reconnects through the public URL. AWS coverage is required for the durable
  volume recovery contract, not a manual substitute.

Detailed planning must select the exact restart hooks and test names in the
existing harness. The behaviors above are mandatory even if organized into
fewer scenarios.

### Additional implementation verification

- Corrupted or unsupported manifest versions fail safely and preserve bytes
  for operator recovery.
- Concurrent registry mutations cannot leave partially written JSON.
- Unknown labeled containers are visible as orphans and are not adopted
  without matching durable identity.
- Existing cloud plugin, frontend SDK, and local cloud end-to-end suites remain
  green to prove compatibility with current creation/export/sync/close flows.
