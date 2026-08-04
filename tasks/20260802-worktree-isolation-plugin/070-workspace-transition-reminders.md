# Opt-In Workspace Transition Reminders

Add a provider-neutral, model-visible reminder strategy for workspace transitions, including explicit open/close controls and a standalone reorientation action.

Parent Task: tasks/20260802-worktree-isolation-plugin/000-main.md

Depends On: tasks/20260802-worktree-isolation-plugin/050-baseline-real-model-workflow.md

## Requirements checklist

- [ ] Explicit opt-in settings independently control reminders on worktree open and close; both are disabled by default.
- [ ] A separate session action can remind the model of the authoritative current workspace at any time.
- [ ] A reminder uses a provider-neutral model-visible representation and is preserved correctly across Codex, Claude, Kimi, and Gemini provider-native history.
- [ ] Reminder wording identifies the current workspace and warns that earlier absolute paths may be stale without requiring the model to understand Git worktrees.
- [ ] Reminder generation is idempotent for one transition and does not create duplicate messages during action retry or restart reconciliation.
- [ ] Reminder records are auditable to the user and distinguishable from user-authored messages through metadata.
- [ ] Existing sessions and workflows are unchanged when the settings are disabled.

## Supporting details

- Recommended reminder shape:

  ```text
  <system_reminder>
  The active working directory has changed to /authoritative/path.
  Treat this directory as the project root. Absolute paths from earlier tool
  calls may refer to the previous workspace and must not be reused without
  checking them.
  </system_reminder>
  ```

- Persisted model-visible user messages are the preferred initial mechanism because they are provider-neutral and auditable. A hidden/request-only injection would require a broader generic message-visibility contract.
- Consecutive user messages and provider-native retained history must be tested rather than assumed safe.
- This strategy can compose with explicit workspace system context.

## Execution plan

Status: Draft

Add session settings and action-dialog controls for open/close reminders, plus a standalone application action. Append reminders through the normal core/session message path so native history stays valid, using stable transition identifiers in metadata for idempotency. Render generated messages as ordinary auditable system-reminder content unless a generic existing presentation contract can distinguish them without frontend hardcoding.

Test each provider family with retained native history, action retries, restart reconciliation, and a subsequent real request. Add focused comparative evidence without changing the default workflow.

### Implementation decisions and open questions

- Persisted user-role reminder is recommended. If provider evidence shows a material incompatibility, return to Draft and compare a bundled feature-based request-only injection before changing the requirement.
- Metadata should identify generator, transition id, old/new workspace, and timestamp, but model-visible content should remain concise.
- The standalone action should avoid appending an exact duplicate when the latest unconsumed reminder already names the same workspace.
- Frontends may visually label generated reminders through generic metadata, but a new hidden-message feature is out of scope.

### Documentation

- Document settings, action behavior, message shape, audit visibility, idempotency, native-history implications, and how reminders compose with explicit system context.
- Add manual steps for open, close, and standalone reminder variants.

### Task checklist

- [ ] Define reminder settings and metadata contract.
- [ ] Implement transition and standalone actions.
- [ ] Integrate open/close dialog controls.
- [ ] Add provider-native history and retry tests.
- [ ] Add focused real-model evidence.
- [ ] Document behavior and limitations.

### Requirement verification

- Open and close a worktree with each reminder setting disabled and enabled; inspect persisted core/native history and make a subsequent request for all four provider families.
- Retry the same action and restart between reservation/completion; assert one reminder per transition.
- Invoke the standalone action after close and assert it names only the authoritative current workspace.

### Additional implementation verification

- Cover agent switching, session fork, message export, compaction/native-history rebuild, and multiple open/close cycles.