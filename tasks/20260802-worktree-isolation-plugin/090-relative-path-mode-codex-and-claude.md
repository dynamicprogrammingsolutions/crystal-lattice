# Relative-Path Mode for Codex and Claude

Implement the approved opt-in relative-path contract for default Codex and Claude tools and system messages while preserving their existing vendor-compatible behavior when disabled.

Parent Task: tasks/20260802-worktree-isolation-plugin/000-main.md

Depends On: tasks/20260802-worktree-isolation-plugin/080-relative-path-mode-contract.md

## Requirements checklist

- [ ] Codex and Claude dedicated file, edit, search, patch, image/media, and relevant shell schemas follow the approved relative-path contract when enabled.
- [ ] Workspace-contained paths in model-visible results, errors, previews, displays, and system messages are relative when enabled.
- [ ] Codex shell/apply-patch workdir behavior and Claude Bash cwd persistence remain correct across worktree open and close.
- [ ] Internal path resolution and allow-root enforcement remain canonical and do not weaken because model-visible paths are relative.
- [ ] Existing default schemas and representative outputs remain compatible when the mode is disabled.
- [ ] Shared conformance tests and family-specific unit/integration tests pass.
- [ ] A real GPT/Codex-tools and Claude/Claude-tools transition workflow exercises the mode.

## Supporting details

- Codex shell currently encourages an explicit `workdir`, and apply-patch schemas can embed a configured working directory.
- Claude Read requires absolute paths in its default schema, while Bash persists cwd through tool-result metadata.
- Claude's relative persisted cwd inside the configured root is already helpful for workspace transitions; absolute stored cwd outside the root remains a special case.
- Tool changes must remain opt-in to protect upstream compatibility and existing model behavior.

## Execution plan

Status: Draft

Thread the approved mode through Codex and Claude tool initialization and schema generation. Canonicalize paths internally against effective workspace, enforce the contract at input boundaries, and use shared display helpers for workspace-relative output. Adjust opted-in default system-message sections to omit absolute cwd and instruct shell verification.

Exercise normal and transition behavior with production tool wrappers, provider-native displays, and real models. Keep disabled-mode golden/schema tests to prevent accidental default drift.

### Implementation decisions and open questions

- Preserve tool names and parameter names unless the approved contract explicitly requires a mode-specific schema variant.
- For Claude Read/Edit/Write absolute defaults, mode-specific descriptions and validation may change, but disabled behavior must remain untouched.
- Claude Bash should reset an invalid/stale absolute persisted cwd to effective workspace and render any diagnostic according to selected path mode.
- Codex shell must not claim containment; relative `workdir` guidance should prefer `.` while canonical execution still uses the configured workspace.

### Documentation

- Update Codex and Claude tool READMEs with enabled/disabled examples, setting propagation, outside-root behavior, and cwd persistence.
- Document any provider/model compatibility findings from real runs.

### Task checklist

- [ ] Implement Codex mode behavior.
- [ ] Implement Claude mode behavior.
- [ ] Update opted-in system messages.
- [ ] Apply shared conformance suite.
- [ ] Add disabled compatibility tests.
- [ ] Run GPT and Claude real transition cases.
- [ ] Update family documentation.

### Requirement verification

- Run the conformance suite and representative application flows for both families with mode off and on.
- In enabled mode, inspect complete model-visible requests/tool results for workspace absolute-path leakage, then verify canonical filesystem effects and root blocking.
- Complete real worktree open/edit/commit/close/merge/follow-up cases for GPT and Claude.

### Additional implementation verification

- Cover apply-patch freeform/function variants, shell array/string variants, Claude Bash stored cwd, background output paths, MCP result paths, file-not-found errors, image paths, and native display metadata.