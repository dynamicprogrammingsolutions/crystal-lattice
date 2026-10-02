# Add User-Selectable iOS Workspaces

Extend the embedded iOS agent's working-directory control so a session can use
an isolated app sandbox, an app-owned directory shared with other sessions, or
a user-selected folder from iOS Files with persistent permission.

## Requirements checklist

- [x] The existing app-owned workspace root and existing contained-directory
  selections remain available.
- [x] A user can create and select a new app-private sandbox for one session;
  it is not offered as a shared directory to other sessions.
- [x] A user can create and select an app-owned shared directory that can be
  selected by other sessions.
- [ ] A user can select a directory from iOS Files, including available file
  providers such as On My iPhone or iCloud Drive, and grant the app the
  permission needed to use it as a working directory.
- [ ] An authorized external directory remains usable after an app/runtime
  relaunch while the underlying iOS permission remains valid.
- [x] A session records an opaque workspace selection rather than accepting an
  arbitrary external filesystem path from the UI or session override API.
- [x] Claude-like and Codex-like file tools treat the effective selected
  directory as their filesystem boundary and cannot traverse to its parent or
  unrelated authorized directories.
- [x] Selecting or creating a workspace does not import, copy, or duplicate
  the directory's contents.
- [ ] Missing, moved, stale, or revoked external-folder access is shown as an
  unavailable workspace and does not silently fall back to a different
  directory.
- [ ] The complete internal and external folder-selection flow is verified in
  the iOS Release simulator through the production session-settings and
  embedded-runtime path.

Parent Task: tasks/20260910-ios-embedded-runtime-poc/000-main.md

Depends On:
tasks/20260910-ios-embedded-runtime-poc/019-session-working-directory-selector.md
tasks/20260910-ios-embedded-runtime-poc/022-plugin-driven-session-settings-actions.md

## Scope

This subtask owns working-directory selection and directory creation for the
embedded iOS runtime:

- create a private app-owned session sandbox;
- create or reuse an app-owned shared workspace;
- select and retain access to an existing external directory through iOS
  Files; and
- use the selected directory directly as the session's tool boundary.

It does not add file import/copy, a workspace file browser, file
synchronization, automatic cleanup or deletion, Android/macOS external-folder
support, or arbitrary absolute-path input.

## Approved target UX

The existing **Session settings → Working directory** row remains the single
entry point. Its compact value shows a source-qualified, human-readable name,
never an app-container path:

- `Private · This session`
- `Shared · Workspace root`
- `Shared · <folder name>`
- `Files · <folder name>`
- `Unavailable · <folder name>` when a retained external grant cannot be
  restored

Tapping the row opens a grouped chooser containing known workspaces:

1. **Private to this session**
   - Existing private workspaces for the current session appear here.
   - Private directories are omitted from other sessions' choices.

2. **Shared app workspaces**
   - **Workspace root** preserves the current shared-root behavior.
   - Existing app-owned shared directories are listed by relative name.

3. **Folders from Files**
   - Previously authorized external folders are listed by display name and
     availability.
   - Selecting a previously authorized entry reuses its retained permission
     rather than opening the picker again.

The workspace plugin contributes settings-placed actions immediately under the
working-directory field:

- **Use a new private workspace**
- **New shared workspace…**
- **Choose folder from Files…**
- **Restore access…**, shown only for an unavailable external selection

The custom workspace element selects and displays known workspace IDs; it
does not hardcode creation or authorization operations. Those operations use
the generic plugin-driven settings-action contract from subtask `022`.
Selection saves immediately. Successful creation or authorization actions
also select the new workspace and refresh the chooser. Canceling the native
picker leaves the current directory unchanged.

The first increment does not delete workspace contents automatically. Session
deletion therefore cannot erase a private or external directory. Cleanup and
permission-removal UX require a later explicit decision.

## Feasibility and supporting facts

- The mobile app already depends on `@react-native-documents/picker` 12.0.1
  for attachment selection.
- That package exposes `pickDirectory({requestLongTermAccess: true})` on iOS,
  starts security-scoped access for the selected URL, and returns a bookmark
  payload for long-term access.
- The attachment helper uses import mode and `keepLocalCopy`, which is correct
  for message attachments but conflicts with this task's no-copy workspace
  requirement. Reuse should therefore be limited to the picker dependency,
  error conventions, presentation patterns, and test mocks.
- The package does not expose a general API that restores a saved bookmark and
  reacquires filesystem access for an embedded interpreter. A small native
  iOS workspace-access component is needed to resolve saved bookmarks,
  detect stale grants, call `startAccessingSecurityScopedResource`, and keep
  access active while the embedded runtime uses the directory.
- The existing Python application validation permits only descendants of one
  fixed `workspace_root`. Supporting external folders safely requires an
  authorized-workspace registry or resolver; merely adding external paths to
  `allowed_paths` or accepting absolute session overrides would weaken the
  current boundary.
- The current `directory` session-setting renderer established the immediate
  save and contained-selection behavior. The expanded contract should use a
  distinct `workspace` config type whose value is an opaque ID and whose
  renderer groups known sources and availability. Creation and picker buttons
  remain separate plugin actions.

## Proposed design

Represent each selectable workspace as a stable opaque record:

```text
workspace_id
kind: private | shared | external
display_name
availability
```

For app-owned records, the application maps the ID to a canonical directory
under its private workspace. For external records, the native iOS host stores
the bookmark locally and maps the ID to the security-scoped URL only after
successfully restoring access. Session overrides persist `workspace_id`;
ordinary clients do not set the resolved external path.

The native host owns acquisition and lifetime of iOS permissions. The
embedded application receives a host-authorized registry of active workspace
IDs and resolved roots, validates the session selection against it, and
derives the effective `working_directory` and tool boundary from the selected
record. A request that names an unknown or unavailable ID is rejected.

The workspace package exposes a feature plugin for the config/effective
workspace boundary and an application plugin for the registry and actions.
Private and shared directory creation goes through application actions rather
than direct React Native filesystem writes. External selection uses the
generic directory client input, while the native host owns the bookmark and
the application action receives only a grant ID.

## Execution plan

Status: Approved

First, extend the workspace-settings feature from a flat path option into a
`workspace` config element with opaque choices carrying source, label, and
availability. Preserve compatibility by migrating the current workspace root
and existing app-owned descendants into shared workspace records and by
resolving existing path-based session overrides when they still identify
contained directories.

Add an application plugin in the workspace package. It owns the workspace
registry and contributes settings-placed actions for creating a private
session workspace, creating a named shared workspace, registering a Files
grant, and restoring stale access. Private records are associated with their
owning session and excluded from other sessions' lists. Shared records remain
under the current application workspace and are listed to all embedded
sessions.

Add a mobile `workspace` chooser behind the existing **Working directory**
row. It renders the three source groups and saves known choices immediately.
Creation and external selection are rendered by the generic anchored settings
actions from subtask `022`.

Add a narrow native iOS workspace-access component around security-scoped
bookmarks. It persists bookmark records outside session/config JSON, restores
them on launch, reports stale or unavailable access, and keeps each selected
URL's security scope active while the embedded runtime may use it. The
component exposes only opaque IDs and resolved authorized roots to the
embedded host boundary.

Teach the embedded runtime and `AgentApplication` workspace validation to
resolve a selected workspace ID from the host-authorized registry. Keep each
tool invocation rooted at the selected directory and reject parent traversal,
symlink escape, unknown IDs, stale grants, and direct attempts to override
authorization fields.

Verify the implementation in stages: internal creation and session isolation;
native picker and permission-state component tests; persistence across an
embedded-runtime restart; and a Release-simulator flow that selects a Files
directory and uses real embedded file tools without copying data.

### Implementation decisions and open questions

- **Approved:** preserve existing sessions and their current selections.
- **Implemented for compatibility:** newly created sessions continue using the
  shared workspace root by default. Creating a private workspace remains an
  explicit plugin action; changing the default can be reviewed separately.
- **Approved:** expose the three source labels as **Private**, **Shared**, and
  **Files**.
- **Implemented:** an external folder grant belongs to the app and appears as
  a reusable **Files** choice, but every session must select it explicitly.
- **Approved:** never delete workspace data automatically in this subtask,
  including when its owning session is deleted.
- **Approved:** store security-scoped bookmarks in protected native
  application state and store only opaque workspace IDs in session metadata.
- **Approved:** the workspace element only selects known choices. Private and
  shared creation, Files selection, and access restoration are plugin actions
  placed under the field through subtask `022`.
- **Open technical validation:** confirm that the Release simulator's Files
  provider returns a bookmark that can be restored after terminating and
  relaunching the app. If the simulator provider cannot exercise durable
  bookmark restoration, keep deterministic component coverage and record the
  exact manual device check rather than weakening the production design.

### Documentation

- Update the embedded iOS configuration guide with the workspace record,
  permission, and Python/native ownership boundaries.
- Update the mobile embedded-runtime guide with the Private, Shared, and Files
  choices, immediate-save behavior, persistence expectations, and unavailable
  folder recovery.
- Document that selecting an external folder grants direct read/write access
  to that folder and that the app does not copy its contents.

### Task checklist

- [x] Approve the workspace chooser and plugin/action ownership.
- [x] Preserve the shared-root default and make external grants reusable only
  through explicit per-session selection.
- [x] Add workspace record and creation operations while preserving existing
  internal workspace selections.
- [x] Add the workspace-specific mobile chooser and reuse the installed
  document-picker dependency for Files selection.
- [x] Add native bookmark persistence, restoration, access lifetime, and
  unavailable-permission handling.
- [x] Connect host-authorized workspace IDs to embedded application and tool
  boundary validation.
- [ ] Add focused source, component, native, bundle, and Release-simulator
  verification.
- [x] Update user and developer documentation.

### Requirement verification

- Through the production session-settings backend, create a private workspace
  for one session and prove it is neither listed nor selectable by another
  session.
- Create a shared app workspace, select it from two sessions, and prove both
  resolve relative file operations to the same directory.
- Through the native Files picker, select a simulator-visible directory, write
  and read a marker with the embedded Claude-like or Codex-like file tools,
  and prove the original directory is used without a local copy.
- Terminate and relaunch the Release app/runtime, reopen the session, and
  prove the selected external workspace and marker remain usable.
- Revoke, move, or invalidate a test external selection and prove the session
  reports it as unavailable without changing to another directory.
- Attempt direct raw-path, parent traversal, sibling access, symlink escape,
  unknown workspace ID, and cross-private-workspace access through the public
  settings/backend boundaries; prove each unauthorized case is rejected.

### Additional implementation verification

- Run the existing attachment-picker tests to prove the workspace picker does
  not alter import/copy semantics for message attachments.
- Verify the immutable iOS bundle includes any new Python workspace logic
  without adding development dependencies.
- Run focused Python/plugin tests, mobile Jest, TypeScript, Swift/native
  tests, documentation preparation, `git diff --check`, and a Release
  simulator build.

## Implementation Notes

- 2026-09-30: The workspace package now exposes both a feature plugin and an
  application plugin. The feature owns the workspace config/tool boundary;
  the application plugin owns Private/Shared/Files choices and creation or
  authorization actions.
- 2026-09-30: `workspace_id` is the persisted selection. `AgentApplication`
  resolves it to a canonical effective `working_directory` and rejects
  unknown IDs, another session's private workspace, traversal, and unavailable
  grants.
- 2026-09-30: Shared descendants remain selectable, private directories live
  under a hidden session-owned area, and external grants are app-level choices
  represented by opaque IDs.
- 2026-09-30: The native runtime stores security-scoped bookmarks in protected
  Application Support state, restores access for runtime configuration, and
  exposes only active grant metadata and resolved roots to Python.
- 2026-09-30: Mobile settings render source-qualified workspace choices and
  plugin-contributed actions for private creation, shared creation, Files
  selection, and stale-access restoration.
- 2026-09-30: Automated evidence passed for internal creation/isolation,
  external grant selection through the embedded application, no-copy
  behavior, tool boundaries, client-input cancellation, opaque action
  payloads, immutable ZIP import, and the Release simulator build.
- 2026-09-30: The remaining acceptance boundary is an interactive Release
  simulator run through the native Files picker followed by app termination
  and relaunch. Source tests use a host-authorized temporary external folder;
  they do not claim to exercise the system Files UI or actual bookmark
  restoration.
- 2026-09-30: The Release build completed successfully. A follow-up run of the
  existing embedded-runtime Detox smoke launched the app and began the test
  but did not return a pass/fail result before the five-minute command timeout;
  the orphaned simulator app was terminated. This run is recorded as
  incomplete, not as acceptance evidence.