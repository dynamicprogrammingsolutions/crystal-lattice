# Single-session exchange and synchronization

Move individual sessions and their assets between a local application and an
existing running cloud workspace without retransferring the repository.

Parent Task: `tasks/20260806-cloud-workspace-runtime-model/000-main.md`
Depends On: `tasks/20260806-cloud-workspace-runtime-model/030-application-workspace-creation-and-complete-transfer.md`

Specification:
`plugins/cloud-agent-app/docs/development/specifications/cloud-workspaces/index.md`

Requirements: `CWS-021`, `CWS-022`, `CWS-023`, `CWS-031`.

## Requirements checklist

- [ ] A local session and its assets can be added to a selected running cloud workspace.
- [ ] A cloud-created session and its assets can be imported into the local application.
- [ ] Explicit sync-up and sync-down actions replace the destination copy in the selected direction.
- [ ] Session IDs are preserved across transfer.
- [ ] Existing destination sessions are not overwritten without explicit confirmation.
- [ ] Successful exchange refreshes affected session lists and session state.
- [ ] Sessions added to cloud are registered to the selected workspace route.
- [ ] Repository transfer is not repeated for session-only operations.

## Supporting details

The initial target requires the runtime to be running. It reuses the existing
cloud session export contract and adds a runtime import contract that saves
through `AgentApplication` rather than manipulating files externally.

Conflict-free merge, automatic bidirectional sync, and offline import into a
stopped workspace are deferred.

## Execution plan
Status: Draft

### Stage 1 — Session transport primitives

Define portable session-plus-assets payloads, add runtime import through public
cloud control/proxy flow, reuse export, and verify round trips with preserved
IDs and asset references. Register imported cloud routes before reporting
success.

Stage completion is testable through direct plugin/runtime APIs.

### Stage 2 — Add and import actions

Expose local-to-cloud add and cloud-to-local import actions, workspace
selection from the plugin registry, destination existence checks, confirmation
requirements, and UI refresh effects.

Stage completion provides safe one-way exchange in both directions.

### Stage 3 — Directional sync convenience

Add explicit sync-up and sync-down actions over the same primitives, record
last exchange metadata where useful, and surface clear results and failures.

### Implementation decisions and open questions

- Preserve session IDs and require explicit overwrite.
- Prefer destination-side safety snapshots if the existing session APIs can
  provide them without inventing a separate backup format.
- Define asset collision handling by content identity/path during detailed
  planning.

### Documentation

- Document add, import, sync-up, and sync-down semantics.
- Document overwrite confirmation, asset inclusion, runtime-running
  prerequisite, and absence of merge behavior.

### Task checklist

- [ ] Finalize payload and overwrite contracts.
- [ ] Implement and verify Stage 1.
- [ ] Report API round-trip procedure.
- [ ] Implement and verify Stage 2.
- [ ] Report add/import user workflow.
- [ ] Implement and verify Stage 3.
- [ ] Report directional sync workflow.
- [ ] Update specification requirements and current documentation with evidence.

### Requirement verification

Required automated coverage:

- Add plugin/runtime unit tests for portable session-plus-assets payloads,
  import/export, route registration, overwrite rejection/confirmation,
  idempotency, asset failure rollback, and runtime-stopped errors.
- Add real `AgentApplication`/FastAPI integration for session import/export
  through production session stores and asset stores.
- Extend frontend SDK action/controller tests for mutations, reload effects,
  errors, and workspace selection.
- Extend local Docker `integration:cloud` to add an asset-bearing local session,
  use it in cloud, create/import a cloud session, run both directional syncs,
  and prove repository transfer hooks were not invoked.
- Use the public connection proxy and production frontend adapter throughout;
  direct runtime calls alone do not satisfy acceptance.

Detailed planning may add an external/AWS scenario if session exchange changes
deployment-specific transfer behavior. Local Docker public-flow coverage is
required in all cases.

### Additional implementation verification

- Failed asset transfer does not leave a saved session with broken asset
  references.
- Runtime-stopped errors remain clear and leave both copies unchanged.
- Repeated import/add requests with idempotency keys do not create accidental
  duplicate sessions.
- Existing two-session connection routing end-to-end remains green.
