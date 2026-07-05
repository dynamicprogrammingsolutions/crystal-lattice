# Clean Up iOS App Identity And Native Metadata

Align app identity, display name, product name, permissions, and versioning so TestFlight/App Store Connect no longer sees leftover sample-app metadata.

## Requirements checklist

- [x] Replace deployment-facing `BonjourExampleRN` names with the approved Crystal Lattice identity where appropriate.
- [x] Align `package.json`, `app.json`, Xcode `PRODUCT_NAME`, display name, README deployment references, and user-facing metadata.
- [x] Preserve the existing bundle ID unless explicitly approved otherwise: `com.dynamicprogrammingsolutions.crystallatticecontrolrn`.
- [x] Review all `Info.plist` permission strings for Apple review quality.
- [x] Remove or fill `NSLocationWhenInUseUsageDescription` based on actual app behavior.
- [x] Define the release version/build-number strategy for fastlane/GitHub Actions.

Parent Task: tasks/20260614-ios-testflight-github-fastlane/000-main.md
Depends On: tasks/20260614-ios-testflight-github-fastlane/020-fix-mobile-verification.md
Depends On: tasks/20260614-ios-testflight-github-fastlane/030-ios-branding-assets.md

## Known Starting State

Branding and identity facts observed:

- `mobile/crystal-lattice-control-rn/app.json` has `"name": "CrystalLatticeControlRN"` and `"displayName": "Crystal Lattice Control"`.
- `mobile/crystal-lattice-control-rn/package.json` still has `"name": "BonjourExampleRN"`.
- Xcode build settings still include `PRODUCT_NAME = BonjourExampleRN` for Debug and Release.
- `mobile/crystal-lattice-control-rn/README.md` still starts with `Bonjour Service Discovery - React Native` and includes old sample paths/names.

Important `Info.plist` entries:

- `CFBundleDisplayName`: `Crystal Lattice Control`
- `NSAllowsLocalNetworking`: true
- `NSBonjourServices`: `_http._tcp`
- `NSLocalNetworkUsageDescription`: `This app discovers local Bonjour services on your network`
- `NSPhotoLibraryUsageDescription`: photo attachment explanation
- `NSPhotoLibraryAddUsageDescription`: save-to-photos explanation
- `NSCameraUsageDescription`: camera attachment explanation
- `NSLocationWhenInUseUsageDescription`: currently empty

## Acceptance Criteria

- No user/deployment-facing stale `BonjourExampleRN` branding remains unless intentionally kept as an internal technical identifier and documented.
- Permission strings are clear and non-empty where present.
- Version/build semantics are documented and ready for fastlane automation.
- Local verification from task `020` still passes after metadata changes.

## Completion Notes

Added during completion on 2026-07-05.

Completed app identity and native metadata cleanup.

- Preserved bundle ID: `com.dynamicprogrammingsolutions.crystallatticecontrolrn`.
- Kept React Native registered module name as `CrystalLatticeControlRN`; native iOS and Android launch the JS app by that module name.
- Changed user-facing display name to `Crystal Lattice`.
- Changed app package metadata from `BonjourExampleRN` to `crystal-lattice-control-rn`.
- Changed Xcode product output to `CrystalLattice.app`.
- Changed Xcode marketing version to `0.9.0`; build number remains `1` and should be incremented by fastlane/GitHub Actions later.
- Lowered app target `IPHONEOS_DEPLOYMENT_TARGET` from `16.6` to `15.1`, matching React Native 0.82's local minimum supported iOS version.
- Removed the empty `NSLocationWhenInUseUsageDescription`; no mobile app location API usage was found.
- Kept existing local-network, Bonjour, camera, photo-library, and photo-library-add usage strings.
- Cleaned targeted README deployment-facing stale names/paths.
- Removed deployment-facing `BonjourExampleRN` strings from the mobile app outside generated/dependency folders.
- Verification passed:

```bash
cd mobile/crystal-lattice-control-rn
npm run tsc
npm test -- --runInBand
```

Results:

- `npm run tsc`: passed.
- `npm test -- --runInBand`: passed, 17 suites and 54 tests.
- Debug iOS simulator build passed with `CrystalLattice.app`.

Remaining warnings from the iOS simulator build were CocoaPods/script-phase warnings unrelated to the identity changes.
