# Add A Safe Per-Session Working Directory Selector

Let each embedded-agent session select a working directory within the
application-owned workspace through a dedicated directory control, while
keeping the workspace root as the non-overridable filesystem boundary.

## Requirements checklist

- [ ] The application-owned embedded workspace root remains fixed and cannot
  be expanded by session settings.
- [ ] A session can select the workspace root or an existing subdirectory as
  its own working directory through a dedicated directory input.
- [ ] The selected directory is persisted as a per-session override and does
  not change other sessions.
- [ ] Backend/tool validation rejects traversal, symlink escape, and any
  working directory outside the configured workspace, including values sent
  by non-UI clients.
- [ ] Both Claude-like and Codex-like embedded file tools resolve relative
  paths against the selected working directory while retaining the workspace
  boundary.
- [ ] The mobile directory control displays workspace-relative names rather
  than exposing implementation-specific application-container paths.
- [ ] The production Release-simulator app proves two sessions can use
  different working directories and read/write only within their effective
  directory and workspace boundary.
- [ ] Arbitrary iOS Files/iCloud directory access, security-scoped bookmarks,
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

- [ ] Add resolver regression tests for allowed descendants and rejected
  traversal, sibling, and symlink paths.
- [ ] Add and package the embedded workspace-settings feature plugin.
- [ ] Add the mobile `directory` session-setting renderer.
- [ ] Add source and real-backend component coverage for directory options,
  persistence, revert, and session isolation.
- [ ] Add a focused Release-simulator scenario using two working directories.
- [ ] Update documentation and completion evidence.

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