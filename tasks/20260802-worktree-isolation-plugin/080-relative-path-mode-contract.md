# Opt-In Relative-Path Mode Contract

Define the common configuration, input, output, system-message, safety, compatibility, and conformance-test contract for a path-minimizing mode before changing the four default tool families.

Parent Task: tasks/20260802-worktree-isolation-plugin/000-main.md

Depends On: tasks/20260802-worktree-isolation-plugin/050-baseline-real-model-workflow.md

## Requirements checklist

- [ ] A documented opt-in setting selects relative-path-oriented behavior while leaving existing defaults unchanged when disabled.
- [ ] The contract specifies how dedicated tools accept workspace-relative paths, handle or reject absolute paths, and authorize paths outside the workspace.
- [ ] Workspace-contained paths in model-visible tool schemas, results, errors, and default system messages have a consistent relative representation.
- [ ] The contract tells the model to verify cwd through shell before depending on it instead of embedding the absolute cwd in opted-in default system messages.
- [ ] Shell limitations are explicit: the mode reduces accidental stale-path reuse and disclosure but does not hide paths from commands or provide security containment.
- [ ] Symlinks, traversal, workdir arguments, temp/output paths, images/media, background processes, and provider-native tool displays have defined behavior.
- [ ] A shared conformance suite can be applied to Codex, Claude, Kimi, and Gemini implementations.
- [ ] Incompatible combinations with explicit absolute workspace context are validated rather than resolved silently.

## Supporting details

- Existing tool families intentionally mirror upstream vendor schemas and differ in whether they require absolute paths, expose workdir parameters, persist cwd, or report resolved paths.
- The proof of concept must be explicit and reversible. It must not permanently deviate default schemas from their vendor-compatible shapes.
- Relative presentation must not weaken root validation. Resolve and validate canonical absolute paths internally, then render only the approved relative representation.
- Legitimate user-supplied files outside the workspace need an explicit policy rather than accidental breakage.

## Execution plan

Status: Draft

Use baseline model evidence and a path-surface inventory to write one normative mode contract. Define settings names and precedence, internal canonicalization, workspace-relative display rules, outside-root authorization, schema wording, shell guidance, and system-message output. Build shared conformance fixtures that assert enabled and disabled behavior without importing one tool family's implementation into another.

Do not modify all tool packages in this subtask beyond shared primitives and test infrastructure. Present the resolved contract for approval before family implementations if the choice between guidance-only and runtime rejection materially changes user behavior.

### Implementation decisions and open questions

- Material decision: whether dedicated tools reject absolute paths in relative mode or accept them but normalize displays. Recommendation: require relative paths for ordinary workspace operations, while providing an explicit opt-in outside-workspace capability rather than a silent absolute-path fallback.
- Shell commands can always call `pwd` and emit absolute paths. Shell schemas should prefer `.`/relative workdirs, but enforcement must not pretend to sanitize command output.
- Paths outside workspace recommendation: remain available only through existing explicit allowlists and retain an absolute representation where no safe workspace-relative form exists.
- Temp and background output paths may need opaque handles or workspace-relative locations; do not redact paths needed by a follow-up tool unless a resolvable handle exists.
- Explicit absolute system context and relative-path mode should be mutually exclusive; reminders may compose if their wording follows the selected path mode.

### Documentation

- Add a normative relative-path mode specification with examples and a complete model-visible path-surface table.
- Document compatibility, privacy limits, outside-workspace behavior, migration, and setting conflicts.
- Record decisions with baseline evidence and tradeoffs.

### Task checklist

- [ ] Inventory model-visible path surfaces.
- [ ] Define setting and precedence.
- [ ] Decide input enforcement and outside-root policy.
- [ ] Define result/error/system-message representation.
- [ ] Implement shared canonicalization/display primitives where appropriate.
- [ ] Build cross-family conformance suite.
- [ ] Document and approve contract before family changes.

### Requirement verification

- Apply the conformance suite to representative fake tools/adapters and prove it detects absolute workspace paths in schemas, results, errors, and system messages when enabled.
- Prove canonical absolute validation still blocks traversal and disallowed roots even though model-visible paths are relative.
- Assert disabled-mode fixtures retain existing schemas and representative output.

### Additional implementation verification

- Cover symlink escapes, `..`, paths with spaces, nested workdirs, deleted cwd, external allowlisted files, temp files, background output, images, patches, and native display metadata.