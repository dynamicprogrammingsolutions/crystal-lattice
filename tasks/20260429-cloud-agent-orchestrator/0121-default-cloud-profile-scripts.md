# Default Cloud Profile Scripts
 Refine the cloud profile model and ship explicit bundled profile script families for the main cloud workspace workflows, with comprehensive coverage for every shipped script.

## Requirements checklist

- [x] Extend the cloud profile model with a separate `cloud_setup_profiles` section so cloud workspace materialization is not overloaded into `install_profiles`.
- [x] Add optional `local_stage_script` support on transfer-up profiles so repo-local hooks can copy `.env` files or other explicitly selected local-only inputs into the transfer directory before upload.
- [x] Keep the current working-tree current-state patch round trip as the shipped default behavior unless the config default is explicitly changed.
- [x] Split the current bundled `repo-install` behavior into an explicit cloud setup profile plus a no-op/default install-hook profile.
- [x] Ship a safer branch-oriented default profile family for dirty-worktree cloud sessions that exports normal committed cloud branches plus safety snapshot refs instead of applying changes directly onto the local dirty worktree.
- [x] Ship a clean-head branch-oriented profile family for committed-only cloud sessions.
- [x] Ensure every bundled script receives explicit env vars for all relevant paths, profile ids, and branch/ref names where applicable.
- [x] Define repeat-sync acknowledgement behavior for every shipped sync-down profile, including branch-oriented profiles.
- [x] Add comprehensive unit tests for all default scripts using temporary workspaces/repos, including concurrent local/cloud safety cases.
- [x] Keep bundled default scripts under the default config asset tree so they are packaged via `${env:CONFIG_DIR}`.

Parent Task: `tasks/20260429-cloud-agent-orchestrator/000-main.md`

Depends On: `tasks/20260429-cloud-agent-orchestrator/0120-cloud-profile-config-no-behavior-change.md`

## Background

Task `0120` already moved the default cloud flow from ad hoc root `.cloud-agent` scripts to explicit bundled profile entries under `${env:CONFIG_DIR}`. This task now focuses on refining that model, separating responsibilities cleanly, adding more shipped profile families, and hardening the script contract.

The currently shipped default profile family implements:

- `transfer-up`: `git archive HEAD` plus a binary patch of staged/unstaged/untracked changes
- `cloud setup`: extract archive, initialize cloud git baseline, apply local working patch
- `export-cloud`: create a cloud patch against the imported baseline
- `apply-down`: apply cloud patch locally

That flow should remain as the initial default profile.

One important issue discovered during design review is that the current bundled `repo-install` script is still doing cloud workspace materialization. This task should split that into:

- `cloud_setup_profiles`: reconstruct the cloud workspace from the transferred payload
- `install_profiles`: optional dependency/bootstrap hooks only

The install hook should also remain reusable for future local sandbox workflows built on top of the same setup model.

## Proposed Scope

This task should now do four main things:

- extend the profile model with `cloud_setup_profiles`
- add optional local staging hooks before upload
- preserve the current patch-based flow as the unchanged default
- add safer branch-oriented default profiles that return clean branches plus safety snapshots

## Proposed Bundled Profile Families

The exact names can still be adjusted during implementation, but the shipped profile set should be organized around these families.

### Patch Round Trip Default

Purpose:

- Upload current committed, staged, unstaged, and untracked state.
- Cloud workspace starts as the same apparent current worktree.
- Sync-down applies cloud changes onto the local current worktree.

Likely profile ids:

```text
transfer_up: working-tree-current-state
cloud_setup: git-archive-patch-setup
sync_down: working-tree-patch
install: repo-install-hook
```

This remains closest to today's behavior and should stay the default.

### Dirty Snapshot With Branch Export

Purpose:

- Start the cloud session from the same apparent local dirty state.
- Let the cloud agent commit naturally from the real base commit as if the work never moved to cloud.
- Return committed cloud work as a separate local branch instead of patching the current dirty worktree.
- Preserve safety snapshots of delegated state, final cloud full state, and local import-time full state.

Likely profile ids:

```text
transfer_up: working-tree-current-state-branch
cloud_setup: git-dirty-head-setup
sync_down: branch-import-snapshot
install: repo-install-hook
```

The exported committed branch should be a normal branch from the real base commit, not a branch whose visible parent is a synthetic delegated snapshot commit.

### Git Clean Head With Branch Export

Purpose:

- Upload only committed `HEAD`, without local staged/unstaged/untracked changes.
- Useful for clean cloud exploration or reproductions.
- Sync-down should return a branch import rather than mutating the current worktree.

Likely profile ids:

```text
transfer_up: clean-head
cloud_setup: git-clean-head-setup
sync_down: branch-import
install: repo-install-hook
```

### Plain Directory Snapshot

Purpose:

- Support non-git workspaces.
- Transfer selected directory contents with common exclusions.
- Sync-down can export a directory snapshot or generated archive.

This is still useful, but it is lower priority than the git branch-oriented profiles in this task. If scope becomes tight, the branch-oriented git workflows should land first and plain-directory can remain a follow-up.

## Branch-Oriented Safety Model

For dirty-worktree branch export, the implementation should preserve three safety snapshots while keeping the normal merge path clean:

- delegated snapshot at cloud start
- cloud full-state snapshot at export time
- local full-state snapshot at import time

These safety snapshots should be imported as private refs by default, not automatically merged and not applied onto the current local worktree.

The normal user-facing merge path should be:

- local clean branch containing the local committed work, for example `A`
- imported cloud committed branch containing the cloud committed work, for example `B + C`

Those branches can later be merged normally to produce `A + B + C`, while the safety refs preserve states such as `A + B`, `A + B + C`, and current local import-time state.

### Why The Cloud Commit Must Look Normal

Purpose:

- The cloud should be able to commit selected changes exactly as if the work stayed local.
- The delegated dirty snapshot exists for safety and recovery, not as the visible parent of the committed cloud branch.

In the common reviewed scenario:

- local base is `X`
- local dirty state is `A + B`
- cloud commits `B + C`
- cloud leaves `A` uncommitted

The imported committed cloud branch should therefore look like `X -> Y` where `Y` contains `B + C`, while separate safety refs preserve the original delegated `A + B`, the cloud full state `A + B + C`, and the local full state seen at import time.

### Possible Mechanics

- full branch-history transfer
- archive plus explicit git metadata plus local/cloud snapshot refs
- `git bundle`, `fast-export`, or another script-friendly branch artifact format
- local apply creates or updates a branch such as `cloud/<session-id>/committed` plus private safety refs such as `refs/cloud-agent/<session-id>/...`

The exact transport format can be refined during implementation, but the branch-oriented flow must support:

- clean committed branch import
- local/cloud delegated safety snapshots
- repeat-sync acknowledgement semantics
- no automatic mutation of the current local worktree

## Local Stage Hook

Some repos need local-only files copied into the transfer payload before upload, for example:

```bash
cp .env "${TRANSFER_STAGE_DIR}/.env"
cp .tool-config.json "${TRANSFER_STAGE_DIR}/tool-config.json"
```

This should be handled by an optional `local_stage_script` on the transfer-up profile, not by hardcoding special file handling in the transfer script itself.

Default behavior:

- bundled default local stage wrapper does nothing if no repo hook is configured/present
- if a repo hook convention is adopted, pass explicit env vars and document it
- repos must explicitly opt in to staging sensitive files such as `.env`

## Install Profile

The install concept is for package/dependency installation after cloud setup, such as:

```bash
npm install
pip install -r requirements.txt
```

Default behavior:

- do nothing if no repo install hook is configured/present
- if a repo hook convention is adopted, pass explicit env vars and document it

## Script Environment

Every script should fail clearly if required env vars are missing. Expected env vars should include, as applicable:

```text
LOCAL_WORKSPACE_DIR
CLOUD_WORKSPACE_DIR
TRANSFER_DIR
TRANSFER_STAGE_DIR
CONFIG_DIR
WORKING_DIR
SESSION_ID
CLOUD_AGENT_PROFILE_ID
CLOUD_AGENT_TRANSFER_UP_PROFILE_ID
CLOUD_AGENT_CLOUD_SETUP_PROFILE_ID
CLOUD_AGENT_SYNC_DOWN_PROFILE_ID
CLOUD_AGENT_INSTALL_PROFILE_ID
```

For branch-oriented profiles, also pass explicit branch/ref naming env vars rather than having scripts invent names ad hoc.

Use exact names consistently with implementation.

## Testing Notes

Add comprehensive script tests:

- `bash -n` for shell scripts
- required env var failures
- successful stage/transfer/setup/install/export/apply/mark-synced behavior for each profile family
- committed/staged/unstaged/untracked handling for git profiles
- default patch round trip remains stable
- local stage hook wrapper no-op behavior and repo hook execution behavior
- clean-head excludes dirty local changes
- branch import creates/updates the expected committed branch without touching the current dirty worktree
- delegated snapshot, cloud full-state snapshot, and local import-time snapshot refs are created as expected
- concurrent local/cloud safety scenarios, such as local commit `A` and cloud commit `B + C`
- repeat-sync behavior for branch-oriented flows
- plain-directory behavior with ignored/excluded files if that profile family lands in this task
- binary file changes where relevant
- idempotency or clear failure behavior on repeated apply where relevant

## Proposed Plan

1. Extend the cloud profile resolver/model from `0120` with `cloud_setup_profiles` and optional `local_stage_script` support on transfer-up profiles.
2. Update `CloudAgentAppPlugin` and runtime wiring so the selected transfer-up profile resolves and runs, in order:
   - local stage script
   - local transfer script
   - cloud setup script
   - cloud install script
   - cloud export script
   - cloud mark-synced script
   - local apply script
3. Split the current bundled `repo-install` script into:
   - `git-archive-patch-setup` for cloud materialization
   - `repo-install-hook` for optional dependency/bootstrap work
4. Keep the current patch-based profile family as the default shipped flow so behavior remains stable unless config defaults are intentionally changed.
5. Add a branch-oriented dirty-worktree profile family that:
   - transfers enough git history for normal cloud commits from the real base commit
   - preserves delegated/local/cloud safety snapshots
   - imports a clean committed cloud branch plus private safety refs
   - does not rewrite the current local worktree automatically
6. Add a clean-head branch-oriented profile family for committed-only cloud sessions.
7. If scope permits, add a plain-directory profile family; otherwise leave it as a follow-up after the git profile families land.
8. Add focused unit coverage for every bundled script and integration-style profile tests for the default patch flow and the new branch-oriented flow.

## Execution plan

Added during completion on 2026-05-05 after user approval.

1. Update the cloud profile resolver and validation logic to support `cloud_setup_profiles`, optional `local_stage_script`, and separate effective script resolution for setup versus install.
2. Update cloud plugin script execution order and runtime script packaging so local stage, local transfer, cloud setup, cloud install, cloud export, cloud mark-synced, and local apply are distinct phases with explicit env vars.
3. Update the cloud runtime startup flow to run separate bundled `setup` and `install` scripts while preserving current default behavior.
4. Split the current bundled materialization logic into a dedicated setup profile and convert the default install profile into an optional repo install hook wrapper.
5. Keep the current patch-based profile family as the default shipped flow and verify existing behavior remains stable through the new contract.
6. Add a clean-head branch-oriented bundled profile family to establish the branch export/import contract with simpler committed-only semantics.
7. Add the dirty-worktree branch-oriented bundled profile family with delegated, cloud full-state, and local import-time safety refs, while avoiding automatic mutation of the current local worktree.
8. Add repeat-sync acknowledgement behavior for branch-oriented profiles so later syncs export only new cloud work.
9. Expand resolver, runtime, script-level, and profile-level tests in the same order to guard the default patch flow first and then cover the new branch-oriented flows.

## Completion Notes

Added during completion on 2026-05-05 after implementation and verification.

- Extended `cloud_agent_profiles.resolve_cloud_agent_profiles` with `cloud_setup_profiles`, optional `local_stage_script`, separate selected/effective setup profile resolution, and explicit `cloud_install_script` resolution.
- Updated `CloudAgentAppPlugin` to run local stage before local transfer, package separate runtime `setup` and `install` scripts, and pass expanded script env vars including session/profile ids plus branch/safety-ref names for branch-oriented profiles.
- Updated the cloud runtime startup flow to execute `setup` and then `install` as distinct phases with shared explicit env vars.
- Split the previous bundled materialization behavior into `git-archive-patch-setup/setup` and converted `repo-install/install` into a repo-hook wrapper that no-ops when no repo hook is present.
- Added the bundled `common/local-stage-hook` wrapper so repos can explicitly stage local-only files such as `.env` into `TRANSFER_STAGE_DIR`.
- Kept the current patch-based `working-tree-current-state -> working-tree-patch` flow as the default shipped behavior.
- Added bundled branch-oriented profile families for `clean-head` and `working-tree-current-state-branch`, plus a shared `branch-import` sync family that imports a committed branch and private safety refs without mutating the current local worktree.
- Added branch-oriented repeat-sync acknowledgement through `refs/cloud-agent/<session>/last-synced` and incremental bundle export logic.
- Updated the shipped default config and README example to the new `cloud_setup_profiles` plus `local_stage_script` model.
- Added/updated tests for resolver behavior, separate runtime install execution, local stage and install hook wrappers, stable default patch sync, clean-head branch import, dirty-worktree branch import with delegated/cloud/local safety refs, and incremental branch sync.

Verification:

```bash
PYTHONPATH=plugins/cloud-agent-app/src:core/python pytest plugins/cloud-agent-app/tests/test_cloud_agent_app_plugin.py -q
PYTHONPATH=core/python:application/python pytest application/python/tests/test_cloud_agent_runtime.py application/python/tests/test_runtime_layout.py application/python/tests/test_default_config_effective_agent_configs.py core/python/tests/test_default_system_instructions_docs.py -q
ruff check plugins/cloud-agent-app/src/cloud_agent_app plugins/cloud-agent-app/tests/test_cloud_agent_app_plugin.py application/python/tests/test_cloud_agent_runtime.py application/python/tests/test_runtime_layout.py application/python/tests/test_default_config_effective_agent_configs.py core/python/tests/test_default_system_instructions_docs.py
```
