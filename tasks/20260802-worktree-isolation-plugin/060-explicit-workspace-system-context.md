# Opt-In Explicit Workspace System Context

Add an optional strategy that places authoritative original and current workspace information directly into supported default system messages so its effect can be evaluated against the production baseline.

Parent Task: tasks/20260802-worktree-isolation-plugin/000-main.md

Depends On: tasks/20260802-worktree-isolation-plugin/050-baseline-real-model-workflow.md

## Requirements checklist

- [ ] An explicit opt-in session setting adds original and current workspace context to Codex, Claude, Kimi, and Gemini default system messages.
- [ ] The setting is disabled by default and does not change baseline system messages when absent or false.
- [ ] Context truthfully represents inactive, creating, active, setup-failed, closed, retained-dirty, missing, and reopened worktree states.
- [ ] The model can identify the authoritative active directory and whether an earlier worktree path is no longer active without needing to infer state from old tool calls.
- [ ] The setting is visible and editable through generic session settings UI.
- [ ] Custom system-message configurations are not silently rewritten; integration requires an explicit supported variable/hook contract.
- [ ] Provider-native and rendered-system-message tests cover all four default families.

## Supporting details

- This is an optional product enhancement, not a prerequisite for baseline completion.
- The workflow SHOULD avoid requiring understanding of Git worktree mechanics, but this explicit experiment may name original/current workspaces and can mention worktree state when useful.
- The context must come from reconciled plugin metadata and effective settings, not merely from a directory recorded during creation.
- This strategy may compose with transition reminders. It conflicts conceptually with a later path-minimizing mode and needs explicit precedence.

## Execution plan

Status: Draft

Define a session setting and a neutral runtime context contract through which the application plugin's reconciled state can be rendered by default system-message helpers. Add concise family-appropriate sections that identify original workspace, active workspace, branch, and transition status without copying setup diagnostics or unrelated metadata into the prompt.

Keep the integration conditional and prove that disabled output matches the baseline. Expose the setting through existing config UI, document custom-template integration, and add an experiment row or focused prompts that measure whether explicit context prevents stale-path reuse.

### Implementation decisions and open questions

- Recommendation: use an enum such as `workspace_system_context = "default" | "explicit"` rather than a loosely typed boolean so future strategies have a stable extension point.
- Render absolute paths in this explicit strategy by design.
- When inactive after close, identify the original workspace as active and the last worktree as inactive only if that history is relevant and still available.
- If path-minimizing mode is also selected, reject the incompatible combination with a clear settings error rather than silently leaking paths or discarding explicit context.

### Documentation

- Document setting scope, defaults, rendered fields, custom-template integration, token/privacy implications, and incompatibility with path-minimizing mode.
- Add examples for active, closed, and retained-dirty states.

### Task checklist

- [ ] Define setting and runtime context contract.
- [ ] Implement state-to-context projection.
- [ ] Integrate four default system-message families.
- [ ] Add settings UI and validation.
- [ ] Add disabled/enabled provider-native tests.
- [ ] Document behavior and experiment usage.

### Requirement verification

- For each default family, render the system message with the setting disabled and enabled across representative worktree states; assert baseline preservation and authoritative paths/state.
- Run a same-session open/close request flow and confirm the model-visible system context switches to the correct active workspace.

### Additional implementation verification

- Cover malformed/stale metadata, externally removed worktrees, session reopen, branch reuse, custom templates without the hook, and incompatible settings.