Parent Task: tasks/20260128-sandboxing-prereqs/000-main.md

# Standardize Workspace Path Semantics (`working_directory`, `allowed_paths`)

Define and implement consistent semantics for resolving workspace-related paths across tools/features so that switching a session’s workspace to a sandbox directory is reliable and safe.

## Problem

Today, plugins interpret `allowed_paths` differently:

- Codex tools (`shell`, `apply_patch`) treat each `allowed_paths` entry as a filesystem path resolved via `os.path.abspath(p)` relative to the server process current working directory.
  - `plugins/codex-tools/src/codex_tools/shell_tool.py:156`
  - `plugins/codex-tools/src/codex_tools/apply_patch_tool.py:636`

- `feature-file-context` treats relative `allowed_paths` as relative to `working_directory`.
  - `plugins/feature-file-context/src/feature_file_context/file_context_feature.py:125`

This inconsistency makes “switch workspace by updating `working_directory`” brittle. A sandbox plugin would have to update both `working_directory` and `allowed_paths` with absolute paths every time (and do so in a plugin-specific way).

## Desired Semantics (proposal)

Choose one rule and apply it across filesystem-touching plugins:

- **`working_directory`**: absolute or relative base directory for resolving relative file paths and workdirs.
- **`allowed_paths`**:
  - if entry is absolute: use as-is
  - if entry is relative: interpret relative to `working_directory`

Rationale: switching `working_directory` to a sandbox should naturally scope tool access without requiring rewriting multiple config keys.

## Implementation scope

- Update codex tools:
  - `plugins/codex-tools/src/codex_tools/shell_tool.py`
  - `plugins/codex-tools/src/codex_tools/apply_patch_tool.py`
  - Ensure their allowlist checks interpret relative allowed roots relative to the configured `working_directory`.

- Verify/align other filesystem-aware plugins:
  - `plugins/feature-file-context/src/feature_file_context/file_context_feature.py` already follows the proposed semantics.

## Tests

- Add/adjust unit tests in `plugins/codex-tools/tests/`:
  - Demonstrate that setting `working_directory=/tmp/sandbox` and `allowed_paths=["."]` permits access under `/tmp/sandbox`.
  - Demonstrate that `allowed_paths` still blocks paths outside the sandbox.
  - Include at least one test for `apply_patch` and one for `shell`.

## Open questions

- Should `allowed_paths` default be `["."]` (relative to `working_directory`) or `[working_directory]` (materialized absolute)?
- Should tools accept `allowed_paths=None` meaning “use working_directory only”? (Currently varies.)
