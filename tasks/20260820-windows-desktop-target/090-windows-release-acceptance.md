# Complete Windows Desktop Release Acceptance

Validate the production Windows downloads, native behavior, packaging,
automation, and manual development workflow on ARM64 and native x64 systems.

## Requirements checklist

- [ ] A published x64 package downloads, verifies, installs, launches, upgrades, and uninstalls on a clean native x64 Windows system.
- [ ] A published ARM64 package, when included in the release, downloads, verifies, installs, launches, upgrades, and uninstalls on Windows 11 ARM.
- [ ] Core and native host behavior passes human acceptance, including menus, transient UI, secondary windows, text/scroll, file picker, persistence, accessibility, keyboard, DPI, high contrast, sleep/resume, and reconnect.
- [ ] Native automated suites pass against the same production package build.
- [ ] The Apple Silicon Mac workflow successfully supports Windows 11 ARM development/manual testing.
- [ ] Native x64 acceptance uses a physical or remote x64 Windows environment rather than ARM emulation alone.
- [ ] Published package/checksum/manifest/download metadata and GitHub workflow runs refer to the same source/version.
- [ ] Current Windows, shared, macOS, support, privacy, installation, testing, and release documentation matches accepted behavior.
- [ ] Existing macOS tests and a focused manual regression remain green.
- [ ] Human acceptance and any approved limitations are recorded; unresolved release blockers keep the parent task incomplete.

Parent Task: tasks/20260820-windows-desktop-target/000-main.md
Depends On: tasks/20260820-windows-desktop-target/080-windows-github-actions.md

## Manual test environments

Recommended ARM64 development environment on the current `arm64` Mac:

1. Parallels Desktop.
2. Windows 11 Pro ARM.
3. Windows Developer Mode and long paths.
4. Visual Studio 2022 ARM64 with Desktop development with C++, Windows application development, Windows SDK, MSVC x64/x86 and ARM64 toolsets, and Node tooling.
5. Repository cloned inside the VM filesystem.

Required native x64 acceptance environment:

- physical Intel/AMD Windows 11, or
- remote Azure/AWS/other Windows 11 x64 VM accessed through Remote Desktop.

GitHub Actions x64 proves automated build/test behavior but does not replace
human native x64 UI acceptance.

## Execution plan
Status: Draft

Select a release candidate from the protected workflow. Download it through
the intended public path on clean ARM64 and native x64 systems, verify checksum
and signature, install, and execute the full manual/automated matrix. Validate
the documented Parallels workflow from this Mac, use a remote/physical native
x64 environment for final UI behavior, and run a focused macOS regression.
Record exact systems, package versions, workflow runs, observations, defects,
reruns, and human acceptance.

### Implementation decisions and open questions

- Do not treat Windows x64 emulation on ARM as native x64 acceptance.
- Do not accept a workflow artifact alone when the intended release is a public signed download.
- If ARM64 is deferred, state that explicitly and leave ARM64 release requirements incomplete rather than labeling an x64 package universal.
- Any candidate change after acceptance evidence requires rerunning affected checks.

### Documentation

- Correct current user/maintainer documentation when acceptance exposes a real discrepancy.
- Keep detailed acceptance evidence, systems, workflow IDs, and human confirmations in this task rather than public user pages.

### Task checklist

- [ ] Record source commit, versions, workflow runs, release, URLs, checksums, and signatures.
- [ ] Validate the Parallels Windows 11 ARM setup from this Mac.
- [ ] Download/install/test ARM64 package if released.
- [ ] Download/install/test x64 package on native x64.
- [ ] Run native automated suites against production packages.
- [ ] Exercise core and native-host manual matrix.
- [ ] Exercise clean upgrade and uninstall while preserving approved user state.
- [ ] Verify download/support/privacy/install/test/release documentation.
- [ ] Run macOS automated and focused manual regression.
- [ ] Record human acceptance or blocking defects.
- [ ] Update parent/subtask checklists only when evidence supports completion.

### Requirement verification

- Map each requirement to exact environment/version, command output, workflow/release reference, automated result, and human observation.
- Verify native windows/transients/menus through production behavior, not test-only UI.
- Verify package labels and architecture match the installed binaries.
- Verify no Windows implementation regression changed the shared macOS user outcome.

### Additional implementation verification

- Test multiple monitors, DPI changes while running, high contrast, text scaling, keyboard-only use, clipboard, file picker, sleep/resume, offline/reconnect, and long streaming sessions.
- Verify no orphaned app, Metro, Appium, WinAppDriver, or backend processes remain after tests.