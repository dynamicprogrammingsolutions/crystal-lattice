# Clean Up iOS App Identity And Native Metadata

Align app identity, display name, product name, permissions, and versioning so TestFlight/App Store Connect no longer sees leftover sample-app metadata.

## Requirements checklist

- [ ] Replace deployment-facing `BonjourExampleRN` names with the approved Crystal Lattice Control identity where appropriate.
- [ ] Align `package.json`, `app.json`, Xcode `PRODUCT_NAME`, display name, README deployment references, and user-facing metadata.
- [ ] Preserve the existing bundle ID unless explicitly approved otherwise: `com.dynamicprogrammingsolutions.crystallatticecontrolrn`.
- [ ] Review all `Info.plist` permission strings for Apple review quality.
- [ ] Remove or fill `NSLocationWhenInUseUsageDescription` based on actual app behavior.
- [ ] Define the release version/build-number strategy for fastlane/GitHub Actions.

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
