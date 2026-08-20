# Add Workspace Onboarding Without Owning The CLI Process

Add an `Add Workspace` desktop flow that selects a local directory, discovers
workspace/runtime information, creates a connection, and gives the user the
exact Terminal command while leaving CLI startup and lifetime entirely under
the user’s control.

## Requirements checklist

- [ ] `Add Workspace` is available in the desktop application shipped through both DMG and PKG release paths.
- [ ] The existing `New connection` workflow remains unchanged and available.
- [ ] The user selects a workspace directory through an appropriate native macOS picker and the association survives relaunch when permitted.
- [ ] The app discovers assigned port/profile information from the approved workspace/user profile contract and handles missing, invalid, conflicting, or stale data clearly.
- [ ] The app reliably distinguishes a matching running Crystal Lattice server from a stale status file or unrelated process.
- [ ] The app creates or updates a normal local connection and stores workspace-only metadata separately from shared connection semantics.
- [ ] The app presents an exact, safely quoted, copyable Terminal command for starting the CLI in the selected directory.
- [ ] The desktop app never starts, stops, restarts, owns, or supervises the CLI process.
- [ ] DMG users receive clear guidance that the required CLI command must already be installed; PKG users can use the bundled terminal command.
- [ ] Unit, shared-component, native bridge, CLI contract, HTTP identity, persistence, and realistic integration tests cover the flow.

Parent Task: tasks/20260820-macos-desktop-distribution/000-main.md
Depends On: tasks/20260820-macos-desktop-distribution/110-desktop-landing-distribution-options.md

## Known starting state

- CLI profiles resolve from `<workspace>/.crystal/profile.json`, then `~/.crystal/projects.json`, with CLI flags taking precedence.
- The CLI has no general workspace runtime-status file.
- The bridge PID lock exists only for bridge-enabled processes and is not a general runtime signal.
- `/api/hello` is generic and cannot prove that a server is the expected workspace process.
- Desktop connections currently support manual, discovery, bridge, and cloud records; manual records already carry host and port.
- The desktop package has native window/attachment picker patterns that can inform a workspace directory picker.

## Execution plan
Status: Draft

Plan the detailed UX and cross-package contract before implementation. Add the
minimum CLI runtime-status and HTTP identity support needed for reliable
detection, then add a native directory picker, persisted workspace association,
profile/port resolution, command generation, running-state probe, connection
creation, and user feedback. Keep workspace metadata desktop-owned and create a
normal manual connection for existing backend behavior.

### Implementation decisions and open questions

- Recommended runtime contract: atomically maintain `<workspace>/.crystal/runtime.json` with schema version, PID, process-instance ID, host, port, start time, and CLI version; remove it on clean shutdown and treat it as advisory.
- Recommended identity contract: add a small HTTP runtime endpoint that returns product/version/process-instance identity without exposing the absolute workspace path.
- Recommended running check: read status, validate schema, probe the HTTP endpoint, and compare process-instance identity; do not trust PID/file existence alone.
- Recommended no-port behavior: choose and store a desktop workspace port and include an explicit `--port` in the shown command; do not silently modify workspace profile files without a deliberate UX decision.
- Recommended local command defaults: bind to loopback for desktop-only use; provide an explicit option/instruction when Bonjour or LAN access is desired.
- If App Sandbox is enabled, use user-selected directory access and security-scoped bookmarks; decide how global `~/.crystal/projects.json` access is handled without broad home-directory entitlement.
- These are implementation decisions, not new required outcomes. Reassess them during detailed planning and request approval for any user-visible behavior change.

### Documentation

- Add workspace onboarding and CLI prerequisite instructions to desktop user documentation.
- Document the runtime status/identity contract in the owning CLI and desktop development documentation, with one authoritative schema location.
- Update landing `/desktop` copy only if the delivered onboarding prerequisites differ from the already published distinction.

### Task checklist

- [ ] Write and approve the detailed UX/contract plan.
- [ ] Add and test CLI runtime status lifecycle.
- [ ] Add and test the non-sensitive runtime identity endpoint.
- [ ] Add native directory selection and persistent access as required.
- [ ] Implement profile/port resolution and safe command generation.
- [ ] Implement running/stale/unrelated-server detection.
- [ ] Persist workspace association separately and create the manual connection.
- [ ] Preserve the existing connection editor.
- [ ] Add unit, native, CLI, backend, and desktop integration coverage.
- [ ] Rebuild both DMG and PKG application outputs with the feature.

### Requirement verification

- From both an app-only DMG installation and a combined PKG installation, select a workspace, copy/run the displayed command manually in Terminal, and confirm the app detects and connects to that independently running server.
- Verify stale files, occupied ports, invalid JSON, missing CLI, wrong server identity, moved directories, relaunch, duplicate workspace, and existing connection cases.
- Confirm process inspection shows no desktop-owned CLI child process.

### Additional implementation verification

- Test paths containing spaces, quotes, Unicode, symlinks, and removable volumes.
- Verify runtime files contain no secrets and HTTP identity does not disclose the workspace path.
- Verify sandbox/bookmark behavior across application relaunch if sandboxing is retained.