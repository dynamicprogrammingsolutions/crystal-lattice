# Add A Safe Per-Session Working Directory Selector

Let each embedded-agent session select a working directory within the
application-owned workspace through a dedicated directory control, while
keeping the workspace root as the non-overridable filesystem boundary.

## Requirements checklist

- [x] The application-owned embedded workspace root remains fixed and cannot
  be expanded by session settings.
- [x] A session can select the workspace root or an existing subdirectory as
  its own working directory through a dedicated directory input.
- [x] The selected directory is persisted as a per-session override and does
  not change other sessions.
- [x] Backend/tool validation rejects traversal, symlink escape, and any
  working directory outside the configured workspace, including values sent
  by non-UI clients.
- [x] Both Claude-like and Codex-like embedded file tools resolve relative
  paths against the selected working directory while retaining the workspace
  boundary.
- [x] The mobile directory control displays workspace-relative names rather
  than exposing implementation-specific application-container paths.
- [x] The production Release-simulator app proves two sessions can use
  different working directories and read/write only within their effective
  directory and workspace boundary.
- [x] Arbitrary iOS Files/iCloud directory access, security-scoped bookmarks,
  and external-directory persistence are excluded from this first version.

Parent Task: tasks/20260910-ios-embedded-runtime-poc/000-main.md

Depends On:
tasks/20260910-ios-embedded-runtime-poc/018-embedded-json-config-plugin-parity-and-product-review.md

## Settled direction

- Treat the app workspace as the security boundary and the session working
  directory as a selectable descendant.
- Use a plugin-owned config/UI contribution with a dedicated `directory`
  control rather than exposing `working_directory` as unrestricted text.
- Persist the canonical selected directory through the existing session
  override API.
- Validate the boundary in the backend/tool path as well as the UI. UI options
  are convenience, not authorization.
- List the workspace root and existing subdirectories. Directory creation and
  arbitrary Files/iCloud access are not required in this increment.

## Supporting facts

- Embedded Claude-like and Codex-like tools share
  `embedded_tools_shared.workspace.resolve_workspace_root`.
- The current resolver creates and trusts the configured `working_directory`
  without checking `allowed_paths`, so exposing the setting directly would
  allow a non-UI client to choose an unintended path.
- Session settings already persist arbitrary JSON overrides and the React
  settings host supports application-supplied renderers keyed by control type.
- The mobile settings modal currently falls back to a text field for unknown
  control types. A `directory` renderer can reuse the existing options modal
  while preserving immediate per-session persistence.

## Execution plan

Status: Approved

Add a small embedded workspace-settings feature plugin. Its schema owns the
`working_directory` setting and its UI contribution uses a dedicated
`directory` type with workspace-relative labels and canonical values. It will
enumerate only real directories contained by the first configured allowed
workspace root, apply deterministic ordering and bounded enumeration, and
always include the workspace root.

Harden the shared embedded workspace resolver before exposing the setting.
Resolve configured allowed roots and the selected working directory without
following the selected path outside those roots, reject traversal and symlink
escape, and create a missing working directory only after validation. Keep the
existing relative tool-path checks beneath the selected working directory.

Add a mobile `directory` renderer that opens the existing options modal,
persists selection immediately through the normal session-settings controller,
shows a workspace-relative value, and retains the standard revert-to-default
operation. The renderer will not accept arbitrary typed absolute paths.

Register and package the feature in the Python-owned embedded JSON and iOS
archive. Verify the feature and resolver in source tests, inspect the immutable
ZIP, and exercise selection and session isolation through the production
Release-simulator app.

### Implementation decisions and open questions

- **Approved:** selection is limited to the app-owned workspace; arbitrary
  Files/iCloud folders are deferred.
- **Approved:** the first version selects existing directories and does not
  need a create-directory workflow.
- **Approved:** session overrides may store canonical paths, but all visible
  labels are workspace-relative.
- **Open:** whether a later version should let users import/copy external files
  into the workspace or retain security-scoped access to external folders.

### Documentation

- Document the distinction between workspace root and per-session working
  directory.
- Document the containment, symlink, and non-UI validation boundary.
- Add the directory control and its first-version limitations to the embedded
  mobile runtime guide.

### Task checklist

- [x] Add resolver regression tests for allowed descendants and rejected
  traversal, sibling, and symlink paths.
- [x] Add and package the embedded workspace-settings feature plugin.
- [x] Add the mobile `directory` session-setting renderer.
- [x] Add source and real-backend component coverage for directory options,
  persistence, revert, and session isolation.
- [x] Add a focused Release-simulator scenario using two working directories.
- [x] Update documentation and completion evidence.

### Requirement verification

- Run shared-tool tests proving both tool families accept workspace
  descendants and reject paths outside the fixed allowed root, including a
  symlink escape.
- Query the production embedded session config/UI schema and prove the
  directory options contain only the root and contained directories with
  relative labels.
- Through the production backend and mobile settings modal, assign different
  directories to two sessions, relaunch, and prove each session retains its
  own override.
- Through a Release-simulator model/tool scenario, write and read a relative
  file in the selected directory and prove an outside selection is rejected
  through the HTTP override boundary or tool initialization.

### Additional implementation verification

- Verify the immutable iOS ZIP imports the workspace-settings feature and
  shared resolver from the bundle rather than the repository.
- Run focused Ruff, plugin tests, mobile Jest, TypeScript, Swift parsing,
  `git diff --check`, and the Release-simulator build.

## Implementation Notes

- 2026-09-30: Added the `embedded-workspace-settings` feature package. Its
  `directory` UI contribution lists the fixed workspace root and existing
  non-hidden descendant directories with workspace-relative labels.
- 2026-09-30: Added generic `AgentApplication` validation for sessions with a
  configured `workspace_root`. Such sessions cannot override
  `workspace_root` or `allowed_paths`; selected working directories are
  canonicalized, required to exist, and required to remain under the root.
- 2026-09-30: Hardened `embedded-tools-shared` so both embedded tool families
  independently reject a selected working directory outside the configured
  boundary, including traversal and symlink escapes.
- 2026-09-30: The embedded in-process `/sessions/{id}/overrides` adapter now
  delegates to `AgentApplication.patch_session_settings` and
  `delete_session_setting` instead of writing session metadata directly.
- 2026-09-30: Added a mobile `directory` renderer backed by the existing
  options modal. It displays only relative labels, patches the canonical
  option value immediately, and supports reverting to the agent default.
- 2026-09-30: The real provider simulator diagnostics now create
  `matrix-alpha` through a real file-tool call, select it for one session,
  retain another session at the root, reject an outside override, and verify
  the same state after process relaunch.

## Completion Notes

Completed on 2026-09-30.

- The fixed application workspace and session-specific working directory are
  separate enforced concepts across configuration, session persistence,
  mobile UI, the in-process transport, and both embedded tool families.
- Source evidence passed: 31 focused application/runtime tests, 42 shared
  workspace and tool-family tests, the full 54-suite/279-test mobile Jest run,
  focused settings tests, TypeScript, Ruff, documentation preparation, and
  `git diff --check`.
- The Release iPhone 17 Pro simulator build passed. The real OpenAI Responses
  matrix completed an `apply_patch` request, reported the selected
  `matrix-alpha` directory, rejected the outside path, proved the second
  session remained independent, and retained those facts after relaunch.
- The immutable archive imported `embedded_workspace_settings` and
  `embedded_tools_shared` from `crystal_lattice_app.zip`; provider bundle tests
  passed and the archive remained unchanged with SHA-256
  `6894aef3350afd6b1a40aef7c71941b91d4465a23104c499b50e3d9bd8966f2c`.
- Arbitrary Files/iCloud access, directory creation from the picker, and
  security-scoped bookmarks remain deferred exactly as planned.