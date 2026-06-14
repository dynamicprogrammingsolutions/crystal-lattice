# Prepare iOS TestFlight Deployment With GitHub Actions And fastlane

Prepare the Crystal Lattice Control React Native iOS app for TestFlight registration, first upload, and repeatable continuous deployment through GitHub Actions plus fastlane.

## Task checklist

- [ ] `tasks/20260614-ios-testflight-github-fastlane/010-preflight-audit.md`
- [ ] `tasks/20260614-ios-testflight-github-fastlane/020-fix-mobile-verification.md`
- [ ] `tasks/20260614-ios-testflight-github-fastlane/030-ios-branding-assets.md`
- [ ] `tasks/20260614-ios-testflight-github-fastlane/040-ios-identity-metadata.md`
- [ ] `tasks/20260614-ios-testflight-github-fastlane/050-privacy-landing-page-compliance.md`
- [ ] `tasks/20260614-ios-testflight-github-fastlane/060-app-store-connect-registration-package.md`
- [ ] `tasks/20260614-ios-testflight-github-fastlane/070-fastlane-ios-testflight.md`
- [ ] `tasks/20260614-ios-testflight-github-fastlane/080-github-actions-ios-cd.md`
- [ ] `tasks/20260614-ios-testflight-github-fastlane/090-first-testflight-dry-run.md`
- [ ] `tasks/20260614-ios-testflight-github-fastlane/100-external-testflight-readiness.md`
- [ ] `tasks/20260614-ios-testflight-github-fastlane/110-deployment-runbook.md`

## Context

The target app is the React Native mobile app at `mobile/crystal-lattice-control-rn`. The chosen deployment approach is GitHub Actions plus fastlane, not Xcode Cloud, EAS, Codemagic, or Bitrise.

The app already has a native iOS project and workspace:

- Workspace: `mobile/crystal-lattice-control-rn/ios/CrystalLatticeControlRN.xcworkspace`
- Scheme observed via `xcodebuild -list`: `CrystalLatticeControlRN`
- Display name: `Crystal Lattice Control` in `mobile/crystal-lattice-control-rn/app.json` and `mobile/crystal-lattice-control-rn/ios/CrystalLatticeControlRN/Info.plist`
- Bundle ID: `com.dynamicprogrammingsolutions.crystallatticecontrolrn`
- Apple team ID currently in the Xcode project: `73Q43R2PD4`
- Marketing version/build currently observed: `1.0` / `1`
- iOS deployment target currently observed in the app target: `16.6`

Important known gaps from the deployment audit:

- `mobile/crystal-lattice-control-rn/ios/CrystalLatticeControlRN/Images.xcassets/AppIcon.appiconset` currently contains only `Contents.json`, with no icon PNG files. The app has an SVG icon used by the landing page and splash screen; generate iOS icon PNGs from that source asset rather than inventing new artwork.
- `npm run tsc` currently fails because `mobile/crystal-lattice-control-rn/src/components/AnimatedSplashScreen.tsx` passes `type="square"` to `AppLogo`, but `mobile/crystal-lattice-control-rn/src/components/AppLogo.tsx` does not define a `type` prop.
- `npm test -- --runInBand` currently passes 7 of 8 suites, but `__tests__/App.test.tsx` fails because `RNGestureHandlerModule` is not mocked/registered in Jest.
- `mobile/crystal-lattice-control-rn/package.json` still names the app package `BonjourExampleRN`.
- Xcode `PRODUCT_NAME` still appears as `BonjourExampleRN` in the iOS project build settings.
- `mobile/crystal-lattice-control-rn/README.md` still contains stale Bonjour sample wording and paths.
- `NSLocationWhenInUseUsageDescription` exists in `Info.plist` with an empty string; determine whether it should be removed or filled with a real user-facing reason.
- `mobile/crystal-lattice-control-rn/ios/CrystalLatticeControlRN/PrivacyInfo.xcprivacy` exists and declares accessed API reasons for file timestamps, user defaults, and system boot time, with no collected data types and tracking set to false. Revalidate this against current SDKs and app behavior.
- The user stated that the privacy policy is part of the landing page. Use the landing page/privacy URL as the public App Store Connect privacy policy URL once verified.

## Recommended dependency order

1. Complete preflight audit.
2. Fix local verification blockers.
3. Prepare app icon assets.
4. Clean app identity/native metadata.
5. Validate privacy/landing-page compliance.
6. Prepare App Store Connect registration and TestFlight metadata.
7. Add fastlane.
8. Add GitHub Actions CD.
9. Perform first internal TestFlight dry run.
10. Prepare/submit external TestFlight review if desired.
11. Document the release runbook.

## Reference Links

- Apple TestFlight overview: https://developer.apple.com/help/app-store-connect/test-a-beta-version/testflight-overview/
- Apple TestFlight test information: https://developer.apple.com/help/app-store-connect/test-a-beta-version/provide-test-information/
- Apple upload builds: https://developer.apple.com/help/app-store-connect/manage-builds/upload-builds/
- Apple app privacy: https://developer.apple.com/help/app-store-connect/manage-app-information/manage-app-privacy/
- Apple privacy manifests: https://developer.apple.com/documentation/bundleresources/privacy_manifest_files
- fastlane `pilot`: https://docs.fastlane.tools/actions/pilot/
- fastlane App Store Connect API key: https://docs.fastlane.tools/actions/app_store_connect_api_key/
- fastlane `match`: https://docs.fastlane.tools/actions/match/
