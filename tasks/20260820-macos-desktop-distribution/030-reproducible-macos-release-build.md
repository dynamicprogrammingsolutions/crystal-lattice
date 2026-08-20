# Establish A Reproducible macOS Release Build

Create a pinned, automated local build path that verifies the desktop package
and produces an unsigned or ad-hoc universal Release archive before signing is
introduced.

## Requirements checklist

- [ ] Node, Ruby, Bundler, CocoaPods, and relevant build-tool versions are pinned or otherwise reproducible.
- [ ] A clean checkout can install dependencies and build the shared macOS scheme in Release configuration.
- [ ] The Release app bundles production JavaScript and does not depend on Metro.
- [ ] The resulting app contains both `arm64` and `x86_64` slices for required native executables.
- [ ] TypeScript, Jest, selected integration/native checks, archive inspection, and failure diagnostics are part of the verification path.
- [ ] Generated archives, DerivedData, Pods, logs, and release outputs are ignored appropriately.

Parent Task: tasks/20260820-macos-desktop-distribution/000-main.md
Depends On: tasks/20260820-macos-desktop-distribution/020-production-identity-metadata-branding.md

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

- [ ] Pin and lock compatible Ruby/build dependencies.
- [ ] Define clean Node and CocoaPods installation commands.
- [ ] Add Release verification/build commands.
- [ ] Build a clean Release archive without production credentials.
- [ ] Inspect architectures, JavaScript bundle, metadata, privacy manifest, resources, and dependencies.
- [ ] Run desktop unit/component and selected native tests.
- [ ] Verify ignored/generated output policy.

### Requirement verification

- Rebuild from a clean dependency state and record the successful command.
- Verify the app launches without Metro and reports the approved identity.
- Verify required Mach-O files contain both target architectures or document an approved exception.
- Verify failed prerequisites produce actionable diagnostics.

### Additional implementation verification

- Run `lipo -archs` or `file` across the main executable and bundled native libraries.
- Run `otool -L` checks for unexpected absolute non-system dependency paths.