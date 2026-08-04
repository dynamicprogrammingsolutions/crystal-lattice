# Prepare iOS TestFlight Deployment With GitHub Actions And fastlane

Prepare the Crystal Lattice Control React Native iOS app for TestFlight registration, first upload, and repeatable continuous deployment through GitHub Actions plus fastlane.

## Task checklist

- [x] `tasks/20260614-ios-testflight-github-fastlane/010-preflight-audit.md`
- [x] `tasks/20260614-ios-testflight-github-fastlane/020-fix-mobile-verification.md`
  - PARTIALLY COMPLETED VIA `tasks/20260615-mobile-component-integration-tests/020-react-native-testing-library-setup.md`
  - COMPLETED VIA current checkout on 2026-07-05: `npm run tsc` and `npm test -- --runInBand` pass; `npm run lint` remains not applicable until ESLint config is added.
- [x] `tasks/20260614-ios-testflight-github-fastlane/030-ios-branding-assets.md`
- [x] `tasks/20260614-ios-testflight-github-fastlane/040-ios-identity-metadata.md`
- [ ] `tasks/20260614-ios-testflight-github-fastlane/050-privacy-landing-page-compliance.md`
- [ ] `tasks/20260614-ios-testflight-github-fastlane/060-app-store-connect-registration-package.md`
- [ ] `tasks/20260614-ios-testflight-github-fastlane/070-fastlane-ios-testflight.md`
- [ ] `tasks/20260614-ios-testflight-github-fastlane/080-github-actions-ios-cd.md`
- [ ] `tasks/20260614-ios-testflight-github-fastlane/085-app-review-local-runtime-and-testable-mode.md`
- [ ] `tasks/20260614-ios-testflight-github-fastlane/090-first-testflight-dry-run.md`
- [ ] `tasks/20260614-ios-testflight-github-fastlane/100-external-testflight-readiness.md`
- [ ] `tasks/20260614-ios-testflight-github-fastlane/110-deployment-runbook.md`

## Context

The target app is the React Native mobile app at `mobile/crystal-lattice-control-rn`. The chosen deployment approach is GitHub Actions plus fastlane, not Xcode Cloud, EAS, Codemagic, or Bitrise.

The app already has a native iOS project and workspace:

- Workspace: `mobile/crystal-lattice-control-rn/ios/CrystalLatticeControlRN.xcworkspace`
- Scheme observed via `xcodebuild -list`: `CrystalLatticeControlRN`
- Display name: `Crystal Lattice` in `mobile/crystal-lattice-control-rn/app.json` and `mobile/crystal-lattice-control-rn/ios/CrystalLatticeControlRN/Info.plist`
- Bundle ID: `com.dynamicprogrammingsolutions.crystallatticecontrolrn`
- Apple team ID currently in the Xcode project: `73Q43R2PD4`
- Marketing version/build currently observed: `0.9.0` / `1`
- iOS deployment target currently observed in the app target: `15.1`

Original audit gaps and current status:

- App icon PNG generation was completed from the shared SVG source in `tasks/20260614-ios-testflight-github-fastlane/030-ios-branding-assets.md`.
- Mobile TypeScript and Jest verification blockers were resolved in `tasks/20260614-ios-testflight-github-fastlane/020-fix-mobile-verification.md`.
- Stale `BonjourExampleRN` package/product naming and the empty location usage string were cleaned up in `tasks/20260614-ios-testflight-github-fastlane/040-ios-identity-metadata.md`.
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
9. Provide an immediately testable App Review/local runtime path.
10. Perform first internal TestFlight dry run.
11. Prepare/submit external TestFlight review if desired.
12. Document the release runbook.

## Reference Links

- Apple TestFlight overview: https://developer.apple.com/help/app-store-connect/test-a-beta-version/testflight-overview/
- Apple TestFlight test information: https://developer.apple.com/help/app-store-connect/test-a-beta-version/provide-test-information/
- Apple upload builds: https://developer.apple.com/help/app-store-connect/manage-builds/upload-builds/
- Apple app privacy: https://developer.apple.com/help/app-store-connect/manage-app-information/manage-app-privacy/
- Apple privacy manifests: https://developer.apple.com/documentation/bundleresources/privacy_manifest_files
- fastlane `pilot`: https://docs.fastlane.tools/actions/pilot/
- fastlane App Store Connect API key: https://docs.fastlane.tools/actions/app_store_connect_api_key/
- fastlane `match`: https://docs.fastlane.tools/actions/match/
