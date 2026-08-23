# Produce A Signed And Notarized App-Only DMG

Create the maintained app-only desktop release output: a polished DMG
containing only Crystal Lattice Control and the Applications installation
target.

## Requirements checklist

- [ ] A Developer ID Application-signed Release app is produced from the reproducible build.
- [ ] The app passes strict code-signature and Gatekeeper assessment with Hardened Runtime enabled.
- [ ] A user-friendly DMG contains the app and an Applications shortcut without a CLI payload.
- [ ] The DMG is submitted to Apple notarization, accepted, stapled, and validated.
- [ ] The output has deterministic naming, version/build metadata, checksum, and inspection evidence.
- [ ] Installation and launch succeed locally without Metro or development dependencies.

Parent Task: tasks/20260820-macos-desktop-distribution/000-main.md
Depends On: tasks/20260820-macos-desktop-distribution/040-developer-id-signing-bootstrap.md

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

- [ ] Add local signing/notarization configuration and lanes/scripts.
- [ ] Produce and inspect the Developer ID-signed app.
- [ ] Create the app-only DMG layout.
- [ ] Submit and wait for notarization.
- [ ] Inspect the notarization log and resolve actionable findings.
- [ ] Staple and validate the DMG.
- [ ] Generate checksum and release metadata.
- [ ] Install and launch locally from the DMG.

### Requirement verification

- Run `codesign --verify --deep --strict`, `spctl`, `stapler validate`, and metadata inspection on final outputs.
- Mount the DMG, copy the app to Applications, launch it, and exercise a basic local connection.
- Verify the DMG contains no CLI runtime and does not install terminal commands.

### Additional implementation verification

- Inspect every nested Mach-O signature and architecture.
- Confirm notarization succeeds from a clean output rather than a previously stapled local copy.