# Complete Final macOS Distribution Acceptance

Perform the final release matrix after workspace onboarding is present in both
distribution paths and confirm that DMG and PKG remain independently usable,
secure, documented, and publicly downloadable.

## Requirements checklist

- [ ] The final app-only DMG passes clean Apple Silicon and Intel installation, Gatekeeper, launch, connection, workspace-onboarding, and relaunch checks.
- [ ] The final Apple Silicon and Intel PKGs pass matching-architecture clean installation, Gatekeeper, app launch, CLI command, independent CLI process, workspace-onboarding, and relaunch checks.
- [ ] PKG upgrade behavior and coexistence with a standalone user-scoped CLI are verified without losing user state.
- [ ] Production landing-page choices download the correct final DMG and architecture-specific PKGs with matching checksums and version information.
- [ ] GitHub Actions release runs, notarization records, published assets, download-domain assets, and release manifests all refer to the same approved source/version.
- [ ] Current desktop, CLI, landing, privacy, support, installation, troubleshooting, and maintainer release documentation matches the accepted behavior.
- [ ] Human acceptance is recorded for both distribution choices; unresolved blockers leave the parent task incomplete.

Parent Task: tasks/20260820-macos-desktop-distribution/000-main.md
Depends On:
tasks/20260820-macos-desktop-distribution/100-automated-combined-installer-release.md
tasks/20260820-macos-desktop-distribution/110-desktop-landing-distribution-options.md
tasks/20260820-macos-desktop-distribution/120-workspace-onboarding.md

## Reconciliation — October 7, 2026

Progress: pending. This task joins final installer automation, onboarding and
public presentation. The first app-only DMG's Intel hardware waiver does not
establish the matching-architecture CLI/PKG or final acceptance evidence here.


## Manual verification boundary

This is the final human acceptance gate. Automated workflow and integration
tests are prerequisites, not substitutes for installing the public downloads,
observing macOS security/UI behavior, and using the application on clean
Apple Silicon and Intel systems.

## Execution plan
Status: Draft

Create a final release candidate containing all three outputs: universal
app-only DMG, ARM64 combined PKG, and Intel combined PKG. Download through the
production landing page, verify integrity and security metadata, and execute
the complete matrix. For the DMG path, install or expose a compatible CLI
separately before workspace onboarding. For the PKG path, use only the command
installed by the PKG. Exercise upgrades, coexistence, documentation, and
failure messaging, then record human acceptance.

### Implementation decisions and open questions

- Acceptance applies to published production-equivalent downloads, not only local files or workflow artifacts.
- Do not treat Rosetta execution as proof of native Intel acceptance without explicit approval.
- If a release candidate changes after any accepted test, rerun affected checks and update evidence rather than mixing versions.

### Documentation

- Correct user and maintainer documentation for any accepted final behavior discovered during verification.
- Store detailed evidence and human confirmations in this task only; public docs describe the product without acceptance-process language.

### Task checklist

- [ ] Record source commit, versions, workflow runs, release, URLs, and checksums.
- [ ] Verify DMG security metadata and install on Apple Silicon and Intel.
- [ ] Verify DMG workspace onboarding with a separately installed CLI.
- [ ] Verify ARM64 PKG install, CLI independence, workspace onboarding, and upgrade.
- [ ] Verify Intel PKG install, CLI independence, workspace onboarding, and upgrade.
- [ ] Verify standalone CLI coexistence and PATH diagnostics.
- [ ] Verify landing options, downloads, privacy, support, installation, and troubleshooting.
- [ ] Verify user state survives app/PKG upgrade and removal instructions avoid user data.
- [ ] Record human acceptance or blocking defects for every matrix row.
- [ ] Update the parent and subtask checklists only when evidence supports completion.

### Requirement verification

- Map each requirement to exact system/version, command evidence, workflow/release reference, production URL, and human observation.
- Verify the DMG remains app-only while providing the same workspace UI.
- Verify both PKGs install the correct CLI architecture and the GUI remains universal.
- Verify no desktop process owns the user-started CLI process.
- Verify all public download labels and checksums correspond to the tested files.

### Additional implementation verification

- Exercise offline launch after stapling and a fresh reboot.
- Test invalid/stale workspace status and missing-command messaging in both distribution paths.
- Verify release rollback/republication procedures without creating mixed-version public assets.