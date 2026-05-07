# Reuse, Multi-Session Transfer, And Sync Polish
Expand the cloud workflow beyond one-session startup: reuse existing cloud instances, transfer multiple sessions, improve sync-down, and make closing/return flows reliable.

## Requirements checklist

- [ ] Add clean-instance vs reuse-existing-instance choices.
- [ ] Transfer multiple selected sessions to an existing or new cloud runtime.
- [ ] Add cloud instance listing/action conventions such as `cloud.list_instances` and `cloud.transfer_sessions`.
- [ ] Add project/workspace identity so instances can be grouped and reused.
- [ ] Improve sync-down hooks for files and session history.
- [ ] Support patch/archive return as a baseline and optional git push when configured.
- [ ] Make close-remote-session behavior explicit and idempotent.

Parent Task: `tasks/20260429-cloud-agent-orchestrator/000-main.md`
Depends On: `tasks/20260429-cloud-agent-orchestrator/010-remote-docker-orchestrator-mvp.md`

## Scope

This subtask should make daily use practical:

- Start clean when isolation matters.
- Reuse an existing cloud instance when continuing work.
- Transfer more sessions into an already-running workspace.
- Pull changes back without destroying the instance.
- Close the cloud session and update the original local session when finished.

## High-Level Behaviors To Test Before Acceptance

- User can start a fresh cloud instance for a session.
- User can reuse an existing instance and transfer another session into it.
- Multiple sessions import correctly and remain distinguishable.
- Sync-down can be run repeatedly without corrupting local files.
- Closing a remote session updates the local session exactly once even if retried.
- Patch/archive and optional git-push modes report success/failure clearly.