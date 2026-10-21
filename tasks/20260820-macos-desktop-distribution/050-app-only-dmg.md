# Produce A Signed And Notarized App-Only DMG

Create the maintained app-only desktop release output: a polished DMG
containing only Crystal Lattice Desktop and the Applications installation
target.

## Requirements checklist

- [x] A Developer ID Application-signed Release app is produced from the reproducible build.
- [x] The app passes strict code-signature and Gatekeeper assessment with Hardened Runtime enabled.
- [x] A user-friendly DMG contains the app and an Applications shortcut without a CLI payload.
- [x] The DMG is submitted to Apple notarization, accepted, stapled, and validated.
- [x] The output has deterministic naming, version/build metadata, checksum, and inspection evidence.
- [x] Installation and launch succeed locally without Metro or development dependencies.

Parent Task: tasks/20260820-macos-desktop-distribution/000-main.md
Depends On: tasks/20260820-macos-desktop-distribution/030-reproducible-macos-release-build.md

COMPLETED VIA: tasks/20260928-universal-macos-desktop-fastlane-release.md

## Reconciled status

Progress: done. Delivery date: September 29, 2026. Application signing was
completed through the replacement task. The remaining Installer work in 040
is a PKG prerequisite, not a dependency of the completed DMG.

The original Draft approach below is retained as history; the approved
replacement plan supplied the execution evidence.

## Execution plan
Status: Draft

Add or extend fastlane/package-local release automation to fetch Developer ID
Application signing read-only, archive/export the app, verify all nested code,
create the app-only DMG, submit it with `notarytool`, staple the accepted
ticket, and generate checksums. Keep upload/publication outside this subtask.

### Implementation decisions and open questions

- The DMG remains app-only permanently; do not add the CLI to it in subtask 080 or later.
- Prefer native Apple tooling plus a pinned, maintained DMG creation tool only when it materially improves the install presentation.
- Notarize the outer DMG after all nested code is signed.
- Treat any broad entitlement added solely to make notarization pass as a design finding, not an automatic workaround.

### Documentation

- Document local DMG build, notarization, validation, outputs, and troubleshooting in desktop release development documentation.
- Add concise app-only installation instructions to desktop user documentation only after the DMG behavior is verified.

### Task checklist

- [x] Add local signing/notarization configuration and lanes/scripts.
- [x] Produce and inspect the Developer ID-signed app.
- [x] Create the app-only DMG layout.
- [x] Submit and wait for notarization.
- [x] Inspect the notarization log and resolve actionable findings.
- [x] Staple and validate the DMG.
- [x] Generate checksum and release metadata.
- [x] Install and launch locally from the DMG.

### Requirement verification

- Run `codesign --verify --deep --strict`, `spctl`, `stapler validate`, and metadata inspection on final outputs.
- Mount the DMG, copy the app to Applications, launch it, and exercise a basic local connection.
- Verify the DMG contains no CLI runtime and does not install terminal commands.

### Additional implementation verification

- Inspect every nested Mach-O signature and architecture.
- Confirm notarization succeeds from a clean output rather than a previously stapled local copy.

## Completion Notes

Recorded during the approved October 7, 2026 reconciliation; delivery occurred
through `tasks/20260928-universal-macos-desktop-fastlane-release.md`.

- Candidate run `36633536807` produced `Crystal Lattice Desktop 0.9.0 (4)`
  on September 29, 2026, with accepted notarization, valid stapling,
  Developer ID signatures, Hardened Runtime and universal native code.
- The retained candidate inspection verifies the app-plus-Applications-link
  layout, metadata and checksum. Local installation/launch and the later
  fresh public-download launch smoke passed without Metro.
- Publication run `36685765746` subsequently published that exact candidate
  on September 30. SHA-256:
  `8bbd119552de60eee53dd4d45fb8cd360faa1a7a788b780114e274ee46959bb5`.
- The DMG includes no CLI payload. Human clean-machine/architecture acceptance
  remains governed by the replacement release task and future PKG acceptance.