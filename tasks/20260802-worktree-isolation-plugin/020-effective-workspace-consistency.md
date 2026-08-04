# Effective Workspace Consistency

Correct the minimum default system-message and tool configuration behavior needed for one session to switch workspaces reliably across Codex, Claude, Kimi, and Gemini while preserving current default tool shapes.

Parent Task: tasks/20260802-worktree-isolation-plugin/000-main.md

Depends On: tasks/20260802-worktree-isolation-plugin/010-shared-workspace-setup-contract.md

## Requirements checklist

- [ ] Default Codex, Claude, Kimi, and Gemini system-message helpers derive their active cwd and project instructions from effective session `working_directory`.
- [ ] An absolute `working_directory` plus absolute `allowed_paths` value scopes dedicated file/edit/search tools to the selected worktree across all four tool families.
- [ ] A subsequent workspace switch reconstructs tool state and system context from the new effective configuration.
- [ ] Default tool schemas, absolute-path guidance, and result formatting remain unchanged unless a later opt-in relative-path mode is enabled.
- [ ] Regression coverage proves that process cwd may differ from the effective session workspace.

## Supporting details

- Codex and Claude use specialized runtime helpers that already resolve effective `working_directory`.
- Kimi and Gemini use a shared runtime helper that currently initializes cwd from `Path.cwd()`, causing system context and loaded project instructions to disagree with tool execution after a session override.
- Relative `allowed_paths` semantics are inconsistent, but the baseline plugin will set an absolute worktree root and restore the prior value exactly. General relative-path behavior is addressed only if required for correctness or by the optional mode.
- Shell tools are not claimed to be filesystem-contained.

## Execution plan

Status: Draft

Make the shared default system-message runtime resolve cwd with the same effective-config semantics used by Codex and Claude. Confirm all path-sensitive default system-message variables and project-instruction loaders consume that value. Add focused helper tests and an application-level test where process cwd, original checkout, and session worktree are distinct.

Audit initialization of baseline dedicated tools for the four families with absolute roots. Fix only defects that prevent the explicit absolute worktree configuration from working or restoring correctly. Preserve existing schemas and displays; record broader path minimization for optional subtasks.

### Implementation decisions and open questions

- Resolve relative configured cwd against process cwd for compatibility, then normalize to an absolute path.
- Do not globally remove absolute cwd from default prompts here; baseline needs truthful effective context and optional subtask `080` owns path-minimizing behavior.
- Do not claim `allowed_paths` confines shell commands. Tests should distinguish dedicated-tool root checks from shell cwd selection.
- If a tool caches config beyond a request despite normal plugin recreation, fix that lifecycle defect in this subtask.

### Documentation

- Document effective workspace semantics shared by default system-message helpers.
- Note that baseline worktree switching installs absolute session overrides to avoid family-specific relative-root ambiguity.
- Cross-reference the optional relative-path mode rather than describing unimplemented behavior.

### Task checklist

- [ ] Correct shared system-message cwd resolution.
- [ ] Verify project instruction loading follows effective cwd.
- [ ] Audit absolute workspace/root handling in four tool families.
- [ ] Add helper and application integration tests.
- [ ] Update effective-workspace documentation.

### Requirement verification

- Build sessions whose process cwd, base config cwd, and per-session cwd differ; assert each default family renders and uses the per-session directory.
- Switch the same session from original checkout to worktree and back, recreate request tool state, and assert dedicated operations touch only the selected fixture root.
- Verify schemas and representative default result text remain unchanged when no experimental setting exists.

### Additional implementation verification

- Cover relative configured cwd, missing cwd, symlinks, paths with spaces, and project instructions present only in one workspace.
- Run focused Codex, Claude, Kimi, Gemini, feature-system-message, and terminal default-config tests.