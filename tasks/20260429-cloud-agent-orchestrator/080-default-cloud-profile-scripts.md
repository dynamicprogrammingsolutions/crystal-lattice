# Default Cloud Profile Scripts
Add explicit default cloud profile scripts for common transfer and sync methods, with comprehensive unit coverage for every shipped script.

## Requirements checklist

- [ ] Add default profile scripts under the default config asset tree so they are packaged via `${env:CONFIG_DIR}`.
- [ ] Include the current working-tree current-state patch round trip as a default profile.
- [ ] Add additional default transfer/sync methods such as clean-head, branch-oriented, and plain-directory flows.
- [ ] Add a no-op/default install script profile that can call a repo install hook when configured or present.
- [ ] Ensure every script receives explicit env vars for all relevant paths.
- [ ] Add comprehensive unit tests for all default scripts using temporary workspaces/repos.
- [ ] Keep the current default behavior stable unless the config default is explicitly changed.

Parent Task: `tasks/20260429-cloud-agent-orchestrator/000-main.md`

Depends On: `tasks/20260429-cloud-agent-orchestrator/070-cloud-profile-config-no-behavior-change.md`

## Background

After profile config exists, this task should move from ad hoc root `.cloud-agent` scripts to explicit packaged defaults. The scripts should live with default config assets, not as hidden plugin fallbacks.

The current root/test scripts implement:

- `transfer-up`: `git archive HEAD` plus a binary patch of staged/unstaged/untracked changes
- `setup-cloud`: extract archive, initialize cloud git baseline, apply local working patch
- `export-cloud`: create a cloud patch against the imported baseline
- `apply-down`: apply cloud patch locally

That flow should remain as the initial default profile.

## Candidate Default Profiles

The exact names/scripts can be refined during implementation, but include ideas and tests for multiple useful methods.

### Working Tree Current State

Purpose:

- Upload current committed, staged, unstaged, and untracked state.
- Cloud workspace starts as the same apparent current worktree.
- Sync-down applies cloud changes onto the local current worktree.

Likely profile ids:

```text
transfer_up: working-tree-current-state
sync_down: working-tree-patch
install: repo-install
```

This is closest to today's behavior.

### Git Clean Head

Purpose:

- Upload only committed `HEAD`, without local staged/unstaged/untracked changes.
- Useful for clean cloud exploration or reproductions.
- Sync-down should not blindly mutate the local dirty worktree unless explicitly selected.

Possible sync pairings:

- branch import
- patch import onto current branch if explicitly compatible

### Branch-Oriented Round Trip

Purpose:

- Preserve enough git history or branch metadata for cloud changes to come back as a separate branch.
- Avoid applying cloud changes directly onto the user's current worktree.

Possible mechanics:

- git bundle
- archive plus branch patch metadata
- cloud export creates a branch patch/bundle
- local apply creates or updates a branch such as `cloud/<session-id>` or a configured prefix

### Plain Directory Snapshot

Purpose:

- Support non-git workspaces.
- Transfer selected directory contents with common exclusions.
- Sync-down can export a directory snapshot or generated patch-like archive.

This should be designed carefully because conflict behavior is harder without git. Unit tests should make the default safety behavior explicit.

## Install Profile

The install/setup concept is for package/dependency installation, such as:

```bash
npm install
pip install -r requirements.txt
```

It is not the place to describe git workspace materialization. Transfer/install compatibility exists only because some transfer profiles might transfer install artifacts, but the common case can use one shared install profile.

Default behavior:

- do nothing if no repo install hook is configured/present
- if a repo hook convention is adopted, pass explicit env vars and document it

## Script Environment

Every script should fail clearly if required env vars are missing. Expected env vars should include, as applicable:

```text
LOCAL_WORKSPACE_DIR
CLOUD_WORKSPACE_DIR
TRANSFER_DIR
CONFIG_DIR
WORKING_DIR
SESSION_ID
CLOUD_AGENT_PROFILE_ID
CLOUD_AGENT_TRANSFER_UP_PROFILE_ID
CLOUD_AGENT_SYNC_DOWN_PROFILE_ID
CLOUD_AGENT_INSTALL_PROFILE_ID
```

Use exact names consistently with implementation.

## Testing Notes

Add comprehensive script tests:

- `bash -n` for shell scripts
- required env var failures
- successful transfer/setup/export/apply for each profile
- committed/staged/unstaged/untracked handling for git profiles
- clean-head excludes dirty local changes
- branch import creates/updates the expected branch without touching current dirty worktree
- plain-directory behavior with ignored/excluded files
- binary file changes where relevant
- idempotency or clear failure behavior on repeated apply where relevant
