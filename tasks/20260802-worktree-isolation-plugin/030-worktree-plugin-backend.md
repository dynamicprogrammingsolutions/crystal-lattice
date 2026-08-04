# Worktree Application Plugin Backend

Implement the first-party application plugin's Git lifecycle, persistent session state, workspace-setting transitions, setup operation, recovery, and safety behavior independently of presentation details.

Parent Task: tasks/20260802-worktree-isolation-plugin/000-main.md

Depends On: tasks/20260802-worktree-isolation-plugin/010-shared-workspace-setup-contract.md

Depends On: tasks/20260802-worktree-isolation-plugin/020-effective-workspace-consistency.md

## Requirements checklist

- [ ] Backend actions can create/open, inspect, close, reopen, and explicitly clean up a linked Git worktree for a session.
- [ ] A new worktree uses a dedicated validated branch created from committed `HEAD`; an existing owned branch can be reopened safely.
- [ ] The plugin stores enough session metadata to reconcile active, setting-up, ready, setup-failed, closed, retained-dirty, removed, missing, and recoverable states after restart.
- [ ] Opening snapshots and atomically replaces the session's prior `working_directory` and `allowed_paths`; closing restores exact prior presence and values.
- [ ] Setup runs through the shared contract with observable asynchronous status, bounded diagnostics, and safe recovery after failure or interruption.
- [ ] Close removes a worktree only when Git permits safe non-forced removal and otherwise retains it without losing user data.
- [ ] No normal action force-removes a worktree, deletes a branch, stashes changes, creates hidden commits, or modifies the original checkout's dirty state.
- [ ] Branch/path conflicts, repeated actions, concurrent requests, externally changed worktrees, and missing repositories produce recoverable results.

## Supporting details

- Resolve the source repository from the session's effective workspace using Git, not from process cwd.
- Store worktrees outside the source checkout under a configurable allowlisted base. All deletion/removal validation must prove the target belongs to that base and to the expected Git common directory.
- Git worktrees share repository metadata and refs. This feature is not equivalent to a clone or container sandbox.
- Session deletion and application shutdown must not implicitly destroy retained user work.

## Execution plan

Status: Draft

Create a new plugin project under `plugins/` with package-local tests and metadata. Model worktree state as a versioned session metadata record containing source repository identity, original effective settings snapshot, branch, path, operation state, timestamps, setup result, and close/removal status.

Use non-shell subprocess argument arrays for all Git commands. Reserve an operation in session metadata under lock, run filesystem/setup work outside long-held persistence locks through the application's background runtime, then reconcile under lock before applying effective settings. Make retries and restart reconciliation idempotent. Separate "close session workspace" from destructive cleanup so dirty retention cannot block return to the original checkout.

### Implementation decisions and open questions

- Default base path recommendation: `<repo-parent>/.crystal-worktrees/<repo-name>/<session-token>`, configurable and validated after resolution.
- Generate branch names from a configurable prefix plus a stable session-safe token. Reject unsafe user-supplied refs through `git check-ref-format --branch`.
- "Owned branch" means metadata identifies the branch and repository and Git confirms the expected linked-worktree relationship; metadata alone is insufficient for deletion.
- Store prior override presence separately from values so close can distinguish absent keys from explicit values.
- Explicit cleanup of a dirty worktree, if ever offered, must be a separate destructive action and requirement; it is not authorized in this subtask.
- On setup failure, safely remove a newly created clean worktree only when no user changes appeared; otherwise retain and report it.

### Documentation

- Add plugin README/API documentation for configuration, metadata schema, actions, Git requirements, branch naming, storage base, setup operation, close/reopen, and recovery.
- Include a state-transition description concise enough for maintainers to audit destructive boundaries.

### Task checklist

- [ ] Scaffold the first-party plugin package.
- [ ] Implement repository/ref/path validation and command runner.
- [ ] Implement versioned worktree metadata and reconciliation.
- [ ] Implement create/open and setup operation.
- [ ] Implement status, close, reopen, and safe cleanup.
- [ ] Implement exact session setting transition/restoration.
- [ ] Add deterministic unit and application integration tests.
- [ ] Document backend contract and recovery.

### Requirement verification

- Through application actions, create a worktree from a temporary repository, observe setup completion, verify session-effective settings, commit changes, close, restore settings, remove the clean worktree, and reopen the retained branch.
- Make the worktree dirty and prove close returns the session to its original workspace while preserving the worktree, branch, and file contents.
- Reconstruct the application from persisted sessions during creating/setting-up/ready/closed states and assert truthful reconciliation.

### Additional implementation verification

- Test non-Git cwd, bare repository, detached HEAD, invalid branch, existing branch, branch checked out elsewhere, nested cwd, symlink base, path traversal, paths with spaces, source dirty warning, setup failure, process interruption, duplicate action, and concurrent close/open.
- Assert no test path uses force removal, automatic branch deletion, stash, reset, clean, or hidden source commits.