# Prepare Production macOS Identity, Metadata, And Branding

Replace template desktop metadata and assets with production Crystal Lattice
Control identity and align the native target for direct distribution.

## Requirements checklist

- [ ] The macOS app displays `Crystal Lattice Control` in Finder, the menu bar, About, Hide, Quit, and other user-visible native surfaces.
- [x] The production bundle ID is `com.dynamicprogrammingsolutions.crystallatticecontrol.macos` in all Release-relevant settings.
- [x] The Apple team, marketing version, build version source, and macOS deployment target are consistent.
- [ ] A complete macOS AppIcon set is generated reproducibly from the approved shared SVG source.
- [x] Hardened Runtime, privacy manifest inclusion, entitlements, sandbox posture, network access, and file access match the approved preflight decision.
- [x] Debug/test target identity changes do not break native UI tests or React Native module registration.

Parent Task: tasks/20260820-macos-desktop-distribution/000-main.md
Depends On: tasks/20260820-macos-desktop-distribution/010-release-contract-and-preflight.md

## Supersession — October 7, 2026

Disposition: superseded historical contract.

SUPERSEDED BY: tasks/20260928-universal-macos-desktop-fastlane-release.md

The user approved `Crystal Lattice Desktop` and reuse of the iOS icon input.
The replacement delivered that identity, rather than the original name and
SVG-source conditions above. Those two conditions remain unchecked and are
retired; they are not active work to restore the old brand. The unchanged
metadata/security/test outcomes are credited from the replacement task's
September build inspection and native checks.

The following starting state and Draft plan are retained as history. Active
builds use the replacement contract.

## Known starting state

- Product/display/menu values still include `CrystalLatticeControlDesktopRN`.
- Bundle ID resolves to `org.reactjs.native.CrystalLatticeControlDesktopRN`.
- AppIcon slots exist without PNG files.
- Info.plist versions are hard-coded while Xcode also has build-version settings.
- The entitlement file exists but is not connected through `CODE_SIGN_ENTITLEMENTS`.
- Podfile platform is macOS 14.0 while the app target reports macOS 12.4.

## Execution plan
Status: Draft

Update only production identity and metadata needed by the native macOS target,
preserving the internal React Native module name where changing it would be a
separate migration. Generate icons from the existing approved SVG with a
repeatable script or documented command. Align deployment/version settings and
wire the minimal approved entitlements. Verify resolved build settings and
user-visible strings in a built app.

### Implementation decisions and open questions

- Keep the React Native registration/module identifier unchanged unless it is user-visible or prevents production packaging.
- Use one authoritative source for marketing/build versions; do not maintain contradictory hard-coded values.
- Do not add broad hardened-runtime exceptions speculatively. Add only entitlements required by a verified Release build.
- Preserve native UI test bundle identity as a distinct test target.

### Documentation

- Update the desktop README only for current user-visible product naming or prerequisites.
- Record entitlement, deployment-target, icon-generation, and version-source maintenance details in desktop development documentation.

### Task checklist

- [ ] Update product, display, menu, and bundle identity.
- [ ] Align deployment target and version/build settings.
- [ ] Generate and validate every required macOS icon representation.
- [ ] Connect and minimize entitlements according to preflight.
- [ ] Confirm privacy manifest and bundled resources are present.
- [ ] Run desktop TypeScript/Jest checks and focused native launch/UI checks.
- [ ] Inspect the built app’s Info.plist, assets, entitlements, and visible menus.

### Requirement verification

- Verify Finder/application/menu surfaces show `Crystal Lattice Control`.
- Verify the built app reports the approved bundle ID, version, build number, team, deployment target, icon, privacy manifest, and entitlements.
- Verify existing desktop tests still target and launch the production application correctly.

### Additional implementation verification

- Use `assetutil`, `plutil`, `codesign -d --entitlements :-`, and Xcode build-setting inspection where applicable.
- Confirm no template bundle ID remains in Release-relevant app settings.