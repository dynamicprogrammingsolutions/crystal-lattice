# 040 — Shell tooling: Round 3 (Codex-style sandboxing + permission hooks)

## Problem

Codex CLI includes richer “sandbox” semantics than our current `allowed_paths` check:

- separate notions of *default sandbox permissions* vs *escalated* permissions
- ability to request additional filesystem permissions (feature-gated)
- approval flows and prefix rules for future approvals

This subtask adds *hooks and structure* so the **Codex-accurate shell tools** can integrate with command sandboxing work without rewriting everything later.

## References

- Current `shell` allowed_paths logic: `plugins/codex-tools/src/codex_tools/shell_tool.py`
- Codex CLI permission-y schemas:
  - `docs/codex-tools/exec_command/schema.with_request_permissions.json`
  - `docs/codex-tools/shell_command/schema.with_request_permissions.json`

## Plan

### A) Normalize working-directory + allowed_paths semantics

Right now, `allowed_paths` are resolved using `os.path.abspath(p)` which depends on process CWD.

1) Standardize path resolution to be relative to the tool’s configured `working_directory` (or to an explicit workspace root) to match the rest of the repo tooling.
2) Add tests proving that relative `allowed_paths` are interpreted consistently.

### B) Add sandbox permission fields (schema + runtime behavior)

Implement fields similar to Codex CLI (no alias names):

- `sandbox_permissions: string | null`
- `additional_permissions: object | null`
- `justification: string | null`
- `prefix_rule: string | null`

Initial runtime behavior (v1):

- If `sandbox_permissions` asks for escalation and policy disallows it, return a clear error.
- If `additional_permissions` is present but feature is disabled, return a clear error (prefer failing rather than silently ignoring to avoid drift).

### C) Pluggable approval policy

Add a simple approval hook in config:

- `approval_mode`: `"auto" | "prompt" | "deny"` (defaults to auto)

Implementation detail: in this repo we can implement `prompt` as “fail with a message telling the user approval is required”, until the UI-level approval pipeline is wired.

### D) Add a stub “sandbox executor” interface

Refactor the execution path so that later we can swap `subprocess` for a sandbox runner.

Example:

- `CommandExecutor` protocol with `run(...)` and `stream(...)`
- default implementation: local subprocess (today)
- future: sandboxed runner (bubblewrap, container, etc.)

### E) Tests

- Tests for denial when escalation requested.
- Tests for path normalization + denial outside allowed paths.

## Acceptance criteria

- `shell` tool schema supports sandbox-related fields.
- There is a clear policy decision and error messaging when escalation/extra perms are requested.
- Path semantics are consistent and documented.

## Open questions / follow-ups

- How will UI approvals be represented in this platform (tool-partials, app actions, or session overrides)? Keep design flexible.
- Whether web/network access should be controlled here or via a separate network proxy/sandbox layer.
