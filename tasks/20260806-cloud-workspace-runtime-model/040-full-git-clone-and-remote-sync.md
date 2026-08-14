# Full Git clone and remote-style synchronization

Provide a complete Git clone in the cloud workspace and synchronize cloud refs
back to a stable local remote without automatic branch mutation.

Parent Task: `tasks/20260806-cloud-workspace-runtime-model/000-main.md`
Depends On: `tasks/20260806-cloud-workspace-runtime-model/030-application-workspace-creation-and-complete-transfer.md`

Specification:
`plugins/cloud-agent-app/docs/development/specifications/cloud-workspaces/index.md`

Requirements: `CWS-016`, `CWS-017`, `CWS-018`, `CWS-019`, `CWS-020`.

## Requirements checklist

- [ ] The new default transfer profile materializes complete reachable Git history, branches, and tags in cloud.
- [ ] Current staged, unstaged, and non-ignored untracked worktree state is represented in cloud.
- [ ] The cloud clone retains the original upstream as `origin` without embedding credentials.
- [ ] Sync-down creates or updates a stable local cloud remote and fetches cloud refs into its remote-tracking namespace.
- [ ] Sync-down does not automatically checkout, merge, rebase, reset, or delete local branches.
- [ ] Existing patch and branch-import profiles remain selectable and compatible.
- [ ] Existing project scripts and profile overrides continue using the current phase contract.

## Supporting details

Use Git bundles and explicit metadata instead of copying raw `.git` internals.
The latest returned bundle may live below
`.git/cloud-agent/<workspace-id>/`, with a stable remote such as
`cloud-<workspace-id>`.

External linked worktrees, ignored build outputs, private submodules, and
multi-repository credentials are excluded from this task.

## Execution plan
Status: Draft

### Stage 1 — Full clone transfer

Add a bundled transfer-up profile that exports reachable refs and metadata,
captures current worktree state, clones from the bundle in cloud, restores the
upstream URL, and applies the worktree state. Keep the existing repository hook
phases intact.

Stage completion is testable by inspecting cloud history, branches, tags, and
working state.

### Stage 2 — Remote-style return sync

Add a matching export/apply profile that creates a cloud bundle, stores it
under local Git state, creates or updates a stable remote, and fetches all
supported refs without modifying checked-out branches.

Stage completion is testable by creating a cloud branch and observing it under
the generated local remote.

### Stage 3 — Default and compatibility migration

Make the full-clone pair the default for new/default configuration while
retaining and validating all current profiles and project overrides. Simplify
authoring documentation around the default and custom hooks.

### Implementation decisions and open questions

- Define the exact refspec and remote naming normalization during detailed
  planning.
- Transfer only reachable Git objects in the initial target.
- Preserve original upstream URL and Git identity metadata, but no credential
  material in this task.

### Documentation

- Update bundled profile reference and script-authoring examples.
- Document cloud remote naming, ref layout, repeat sync behavior, and manual
  merge/cherry-pick workflows.
- Clearly document exclusions such as linked worktrees and ignored files.

### Task checklist

- [ ] Finalize bundle metadata, refspec, and remote naming contract.
- [ ] Implement and verify Stage 1.
- [ ] Report cloud clone inspection procedure.
- [ ] Implement and verify Stage 2.
- [ ] Report local remote synchronization procedure.
- [ ] Implement and verify Stage 3.
- [ ] Report custom-profile compatibility procedure.
- [ ] Update specification requirements and current documentation with evidence.

### Requirement verification

Required automated coverage:

- Add script-focused tests for bundle metadata, refs, staged/unstaged/binary/
  untracked state, origin restoration, remote naming, refspecs, repeat sync,
  interrupted replacement, and credential exclusion.
- Extend cloud-agent profile/config tests for new defaults and compatibility.
- Extend `cloud-orchestrator.profiles.e2e.integration.test.ts` so the shipped
  full-clone and remote-sync scripts run through the real local Docker
  orchestrator/runtime transfer path.
- Extend local Docker `integration:cloud` to create/update cloud branches over
  repeated syncs and assert the stable remote-tracking refs while the local
  checked-out branch and worktree remain unchanged.
- Keep explicit end-to-end scenarios for existing patch and branch-import
  profiles.
- Add an AWS fresh-build profile/sync scenario so full-clone transfer and
  return sync are exercised over managed SSH and the deployed persistent
  volume.

Detailed planning selects fixture repository shape and exact ref namespace.
Inspection commands in stage reports are supplementary; repository state must
be asserted by tests.

### Additional implementation verification

- Repository paths with spaces and non-ASCII names round-trip correctly.
- Failed or interrupted sync does not replace a previously usable local bundle
  or remote state.
- Git credentials do not appear in bundles, metadata, or logs.
- Cloud validation Docker tests continue to exercise the shipped script
  contract and installed runtime bundle.
