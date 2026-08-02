# Relative-Path Mode for Kimi and Gemini

Implement the approved opt-in relative-path contract for default Kimi and Gemini tools and system messages while preserving current behavior when disabled.

Parent Task: tasks/20260802-worktree-isolation-plugin/000-main.md

Depends On: tasks/20260802-worktree-isolation-plugin/080-relative-path-mode-contract.md

## Requirements checklist

- [ ] Kimi and Gemini dedicated file, edit, search, media, and shell schemas follow the approved relative-path contract when enabled.
- [ ] Workspace-contained paths in model-visible results, errors, displays, temp references, and system messages are relative when enabled.
- [ ] Kimi's configured-cwd shell and Gemini's `dir_path` behavior remain correct across worktree open and close.
- [ ] Shared path utilities canonicalize and validate against the effective workspace without resolving relative allow roots against process cwd.
- [ ] Existing default schemas and representative outputs remain compatible when the mode is disabled.
- [ ] Shared conformance tests and family-specific unit/integration tests pass.
- [ ] Real Kimi/Kimi-tools and Gemini/Gemini-tools transition workflows exercise the mode.

## Supporting details

- Kimi and Gemini currently share path utilities but initialize several allowed-root lists with `Path(...).resolve()` relative to process cwd.
- Gemini exposes resolved paths in multiple success and error messages and allows an explicit shell `dir_path`.
- Kimi's shell has no workdir argument and relies on configured cwd, while dedicated tools have varying absolute/relative guidance.
- Shared utilities are an opportunity for consistency, but family-specific vendor schemas and formatting must remain distinct where required.

## Execution plan

Status: Draft

Correct shared workspace-relative canonicalization and thread the approved mode through Kimi and Gemini tool initialization, schema generation, result formatting, and opted-in system-message rendering. Apply the common conformance suite, then add family-specific coverage for shell, temp/media paths, ignore files, and provider-native displays.

Run realistic worktree transitions with the production OpenRouter or family-appropriate provider configurations. Preserve disabled-mode snapshots and existing default-agent behavior.

### Implementation decisions and open questions

- Shared helpers should accept an explicit base path; no relative path may resolve implicitly against process cwd.
- Gemini `dir_path` in relative mode should follow the contract's workspace-relative rule and reject or explicitly authorize outside-root values.
- Temp/output files should live under a workspace-relative project temp directory where possible; otherwise expose an opaque or approved external reference.
- `.geminiignore` and analogous root-relative behavior must continue using the effective workspace.

### Documentation

- Update Kimi and Gemini tool READMEs with mode behavior, shell differences, outside-root handling, ignore files, temp paths, and compatibility.
- Record provider/model observations from real transition runs.

### Task checklist

- [ ] Correct shared base-relative path primitives.
- [ ] Implement Kimi mode behavior.
- [ ] Implement Gemini mode behavior.
- [ ] Update opted-in system messages.
- [ ] Apply conformance and disabled compatibility suites.
- [ ] Run Kimi and Gemini real transition cases.
- [ ] Update family documentation.

### Requirement verification

- Run conformance and application flows for both families with the mode disabled and enabled.
- Inspect model-visible requests/results for workspace absolute paths while verifying canonical effects and allow-root enforcement.
- Complete real worktree open/edit/commit/close/merge/follow-up cases for Kimi and Gemini.

### Additional implementation verification

- Cover reads/writes/replacements, glob/grep/list, media files, shell `dir_path`, project temp paths, ignored files, missing files, paths with spaces, symlinks, and native display payloads.