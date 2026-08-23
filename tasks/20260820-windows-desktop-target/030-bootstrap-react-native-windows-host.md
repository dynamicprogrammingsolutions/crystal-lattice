# Bootstrap The Supported React Native Windows Host

Create the production Windows native host, consume the extracted desktop
application, and deliver a working single-window connection to a real Crystal
Lattice backend.

## Requirements checklist

- [ ] `desktop/crystal-lattice-control-windows-rn` or the approved equivalent is generated from the supported RNW C++ template.
- [ ] The Windows host uses the approved RN/RNW versions, Hermes/New Architecture settings, Windows SDK, application identity, and architecture configurations.
- [ ] Monorepo workspace packages and the shared desktop application resolve in Metro, TypeScript, Jest, Codegen, autolinking, Debug, and ReleaseBundle builds.
- [ ] The main Windows window displays the real desktop shell and can save/open a manual connection to a real backend.
- [ ] ReleaseBundle operation does not depend on Metro.
- [ ] Windows product naming, icons, package identity, network capability, version metadata, and error diagnostics are established.
- [ ] The macOS host remains green.

Parent Task: tasks/20260820-windows-desktop-target/000-main.md
Depends On: tasks/20260820-windows-desktop-target/020-extract-shared-desktop-application.md

## Scope boundary

This subtask establishes one main window and the transport/application shell.
Secondary native windows, native popovers, application menus, attachment
picker parity, custom text/scroll behavior, packaging/signing, and full native
UI testing belong to later subtasks.

## Execution plan
Status: Draft

Generate the Windows host on Windows, apply monorepo Metro/workspace setup,
register the shared main React root, configure product identity and network
access, and implement the smallest platform adapters needed to render. Add
scripts for dependency checking, Debug execution, ReleaseBundle build, and a
backend integration smoke test.

### Implementation decisions and open questions

- Use the C++ app template because current RNW New Architecture native modules are C++/WinRT.
- Start with x64 and ARM64 build configurations, but require x64 as the first production target.
- Use Windows-appropriate fallback surfaces for unimplemented native capabilities; show explicit unsupported diagnostics rather than silent no-ops.

### Documentation

- Create a concise Windows host README with prerequisites, install, first run, Debug/Release build, and links.
- Create Windows development documentation for Visual Studio/SDK configuration, monorepo resolution, Codegen, and troubleshooting.

### Task checklist

- [ ] Generate and normalize the Windows solution/projects.
- [ ] Configure identity, icons, capabilities, versions, and architectures.
- [ ] Configure monorepo Metro, TypeScript, Jest, Codegen, and autolinking.
- [ ] Register the main shared React root.
- [ ] Add minimal platform adapters and visible unsupported diagnostics.
- [ ] Run Debug x64/ARM64 as available.
- [ ] Build ReleaseBundle without Metro.
- [ ] Connect to and exercise a real backend.
- [ ] Re-run the macOS consumer verification.

### Requirement verification

- Launch the Windows application and complete a manual connection/session list request against a real backend.
- Launch the ReleaseBundle with Metro stopped.
- Verify product identity and native package metadata.
- Verify the macOS host still builds/tests against the shared package.

### Additional implementation verification

- Test first-run failure messages for missing runtime/dependencies.
- Verify long-path, workspace path with spaces, and clean-clone setup.