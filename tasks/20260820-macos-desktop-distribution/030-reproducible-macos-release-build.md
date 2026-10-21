# Establish A Reproducible macOS Release Build

Create a pinned, automated local build path that verifies the desktop package
and produces an unsigned or ad-hoc universal Release archive before signing is
introduced.

## Requirements checklist

- [x] Node, Ruby, Bundler, CocoaPods, and relevant build-tool versions are pinned or otherwise reproducible.
- [x] A clean checkout can install dependencies and build the shared macOS scheme in Release configuration.
- [x] The Release app bundles production JavaScript and does not depend on Metro.
- [x] The resulting app contains both `arm64` and `x86_64` slices for required native executables.
- [x] TypeScript, Jest, selected integration/native checks, archive inspection, and failure diagnostics are part of the verification path.
- [x] Generated archives, DerivedData, Pods, logs, and release outputs are ignored appropriately.

Parent Task: tasks/20260820-macos-desktop-distribution/000-main.md
COMPLETED VIA: tasks/20260928-universal-macos-desktop-fastlane-release.md

## Reconciled status

Progress: done. Delivery date: September 29, 2026. The historical identity
predecessor 020 was superseded; it is not an active dependency for this
completed outcome. The original starting state and Draft approach below are
retained, while execution evidence comes from the approved replacement plan.

## Known starting state

- The desktop package has a Gemfile but no tracked Gemfile lock was observed.
- The current Gemfile constraints differ from the mobile fastlane environment and need reassessment against the installed React Native macOS/CocoaPods versions.
- `xcodebuild -showBuildSettings` reports `arm64 x86_64` for Release.
- The previous archive attempt failed before compilation because `macos/Pods` support files were absent.

## Execution plan
Status: Draft

Define package-local setup and verification commands, pin compatible tool
versions, install workspace dependencies and Pods, and produce a Release
archive from a clean state. Add small scripts or fastlane verification lanes
when they remove ambiguity or duplicate shell logic. Inspect the archive for
architectures, bundle metadata, privacy resources, embedded JavaScript, native
dependencies, and absence of development-only assumptions.

### Implementation decisions and open questions

- Prefer package-owned scripts and lockfiles that work locally and in GitHub Actions.
- Use the existing shared scheme and workspace; do not introduce a parallel Xcode project.
- Select the smallest meaningful native UI smoke slice for routine release builds and leave the broad UI suite for acceptance where runtime cost is high.

### Documentation

- Keep the desktop README’s first build concise.
- Add detailed Release setup, archive, inspection, and troubleshooting guidance to desktop development documentation and link it from the development index.

### Task checklist

- [x] Pin and lock compatible Ruby/build dependencies.
- [x] Define clean Node and CocoaPods installation commands.
- [x] Add Release verification/build commands.
- [x] Build a clean Release archive without production credentials.
- [x] Inspect architectures, JavaScript bundle, metadata, privacy manifest, resources, and dependencies.
- [x] Run desktop unit/component and selected native tests.
- [x] Verify ignored/generated output policy.

### Requirement verification

- Rebuild from a clean dependency state and record the successful command.
- Verify the app launches without Metro and reports the approved identity.
- Verify required Mach-O files contain both target architectures or document an approved exception.
- Verify failed prerequisites produce actionable diagnostics.

### Additional implementation verification

- Run `lipo -archs` or `file` across the main executable and bundled native libraries.
- Run `otool -L` checks for unexpected absolute non-system dependency paths.

## Completion Notes

Recorded during the approved October 7, 2026 reconciliation; delivery occurred
through `tasks/20260928-universal-macos-desktop-fastlane-release.md`.

- The replacement established locked Ruby/Fastlane/CocoaPods dependencies,
  clean Node/Pod setup, credential-free verification/build lanes and ignored
  build outputs.
- Its September 29 record includes TypeScript/Jest verification and seven
  selected native tests. Archive/bundle inspection covers JavaScript,
  metadata, privacy resources, native dependency paths and both architectures.
- Clean-source GitHub Actions run `36633536807` succeeded on
  `1a04b8689eab0821727be2c3efc9213e57ebafe7` on September 29, 2026. The
  resulting `0.9.0 (4)` archive/DMG is the decisive clean-checkout evidence.
- This credits the delivered baseline. It does not certify later source
  changes or close human installation acceptance.