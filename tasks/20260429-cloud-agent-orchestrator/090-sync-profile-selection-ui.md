# Sync Profile Selection UI
Add user-facing selection for compatible sync-down profiles when syncing cloud changes back.

## Requirements checklist

- [ ] Add action UI metadata/dialog so `Sync cloud changes` can select a sync-down profile.
- [ ] Show only sync-down profiles compatible with the transfer-up profile used to start the cloud agent.
- [ ] Pass the selected sync-down profile and profile inputs to the plugin action.
- [ ] Store selected profile ids in `session.metadata.cloud_agent`.
- [ ] Keep single-default-profile behavior working when only one compatible profile exists.
- [ ] Add unit tests for profile filtering, action input mapping, and plugin validation.
- [ ] Add integration/e2e coverage for the stable start/sync flow.

Parent Task: `tasks/20260429-cloud-agent-orchestrator/000-main.md`

Depends On: `tasks/20260429-cloud-agent-orchestrator/080-default-cloud-profile-scripts.md`

## Behavior

This is the first task in the sequence that should visibly change user behavior.

When the user runs `Sync cloud changes`, the UI should allow selecting among compatible sync-down profiles, for example:

- apply patch to current worktree
- import as branch
- plain directory download/overlay, if compatible

The action should not offer incompatible profiles.

## Metadata

Record selected profile ids on the local session:

```json
{
  "cloud_agent": {
    "transfer_up_profile": "working-tree-current-state",
    "install_profile": "repo-install",
    "sync_down_profile": "working-tree-patch",
    "container_profile": "default-runtime"
  }
}
```

The sync UI should use the recorded `transfer_up_profile` from the session that started the cloud agent.

## Tests

Cover:

- UI schema/dialog generation for multiple profiles
- no dialog or simple default behavior with one compatible sync profile
- frontend action runner passing selected profile values
- plugin rejecting incompatible sync profile selections
- runtime/export/local-apply using the selected profile
