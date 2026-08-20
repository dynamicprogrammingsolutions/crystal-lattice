# Extract The Shared Desktop Application And Platform Contracts

Separate reusable desktop React/state/backend behavior from the macOS native
host so macOS and Windows can consume the same application without sharing an
incompatible React Native installation.

## Requirements checklist

- [ ] A clearly owned shared desktop package contains reusable screens, state, connection/session/chat logic, persistence coordination, action handling, and platform-neutral UI.
- [ ] React and React Native are peer/runtime boundaries rather than a shared package-owned native version.
- [ ] Significant host behavior is expressed through small typed platform contracts with `.macos` and `.windows` implementations.
- [ ] Direct imports of macOS-only modules are removed from shared application code.
- [ ] The current macOS host consumes the extracted package and preserves existing production behavior, native windows/popovers, tests, and Metro resolution.
- [ ] Shared tests run once at the owning package and at least one real macOS consumer verifies integration.
- [ ] The extraction leaves an intentional path for a future Linux host without defining Linux behavior prematurely.

Parent Task: tasks/20260820-windows-desktop-target/000-main.md
Depends On: tasks/20260820-windows-desktop-target/010-windows-compatibility-architecture-spike.md

## Recommended contracts

```text
DesktopWindowHost
DesktopTransientHost
DesktopMenuHost
DesktopFilePicker
DesktopTextView
DesktopScrollMetrics
DesktopThemeHost
DesktopTestHost
```

Use fewer contracts if the audit proves they can remain cohesive, but do not
replace one macOS-shaped global manager with scattered platform checks.

## Execution plan
Status: Draft

Inventory import and ownership boundaries, create the shared package, and move
code incrementally. Introduce platform-neutral types/adapters before moving
consumers. Wrap the current macOS native modules and custom text-view package
behind macOS implementations. Keep the macOS application buildable and tested
after every slice. Configure both Metro and TypeScript to resolve workspace
symlinks and platform extensions.

### Implementation decisions and open questions

- Avoid a big-bang directory move; extract by coherent dependency slices.
- Keep desktop-specific shared behavior separate from the already shared mobile-compatible RN components unless the abstraction is genuinely common.
- Prefer capability interfaces over platform-name checks.
- Preserve AppRegistry root names and public behavior unless a cross-host registration contract requires an approved change.

### Documentation

- Add the shared package purpose, ownership, development setup, platform-extension rules, and test commands to its README/development docs.
- Update macOS README/development routing for the new shared ownership without documenting unimplemented Windows behavior as current.

### Task checklist

- [ ] Map shared versus macOS-only imports and dependencies.
- [ ] Create the shared package and peer-dependency boundary.
- [ ] Add typed platform contracts.
- [ ] Wrap macOS window/transient/menu/theme/picker/text/scroll behavior.
- [ ] Move shared application code in reviewable slices.
- [ ] Update Metro, TypeScript, Jest, and workspace manifests.
- [ ] Run shared tests and the real macOS consumer tests/build.
- [ ] Confirm no shared code imports the macOS-only text-view package or native modules.

### Requirement verification

- Build and run the macOS host through the extracted package.
- Verify shared tests and existing macOS native/UI tests pass.
- Verify dependency inspection shows React/React Native supplied by the host.
- Verify platform-specific files are selected without widespread `Platform.OS` branching.

### Additional implementation verification

- Run cycle detection or inspect package dependency direction.
- Verify source maps, Fast Refresh, test mocks, and production bundling still resolve moved code correctly.