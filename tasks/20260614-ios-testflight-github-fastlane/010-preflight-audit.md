# Preflight Audit And Deployment Readiness

Audit the iOS app, Apple account assumptions, public URLs, and repo readiness before changing deployment automation.

## Requirements checklist

- [x] Audit code-visible iOS/mobile metadata, signing settings, privacy manifest, icon assets, landing page routes, and deployment workflows.
- [ ] Confirm the Apple Developer Program team, legal entity/account owner, and whether team ID `73Q43R2PD4` is the intended production team.
- [ ] Confirm the final App Store Connect app name, SKU, primary language, category, and whether the first TestFlight release is internal-only or external too.
- [ ] Confirm that `com.dynamicprogrammingsolutions.crystallatticecontrolrn` is registered or ready to register in Certificates, Identifiers & Profiles/App Store Connect.
- [x] Locate the landing page and privacy policy route in code.
- [ ] Confirm the production landing page URL and production privacy policy URL are live/approved for App Store Connect.
- [x] Produce a readiness matrix with `ready`, `needs code change`, `needs Apple account action`, and `needs external asset/content` statuses.

Parent Task: tasks/20260614-ios-testflight-github-fastlane/000-main.md

## Known Starting State

Inspect only the relevant mobile app and deployment files unless new findings require broader search:

- `mobile/crystal-lattice-control-rn/app.json`
- `mobile/crystal-lattice-control-rn/package.json`
- `mobile/crystal-lattice-control-rn/README.md`
- `mobile/crystal-lattice-control-rn/ios/CrystalLatticeControlRN.xcworkspace`
- `mobile/crystal-lattice-control-rn/ios/CrystalLatticeControlRN.xcodeproj/project.pbxproj`
- `mobile/crystal-lattice-control-rn/ios/CrystalLatticeControlRN/Info.plist`
- `mobile/crystal-lattice-control-rn/ios/CrystalLatticeControlRN/PrivacyInfo.xcprivacy`
- Landing page source/deploy configuration, once located.

Previously observed facts:

- Bundle ID: `com.dynamicprogrammingsolutions.crystallatticecontrolrn`
- Team ID in Xcode project: `73Q43R2PD4`
- Scheme: `CrystalLatticeControlRN`
- Version/build: `MARKETING_VERSION = 1.0`, `CURRENT_PROJECT_VERSION = 1`
- App target deployment target: `IPHONEOS_DEPLOYMENT_TARGET = 16.6`
- Display name: `Crystal Lattice Control`

## Audit Notes To Capture

Capture the exact commands and findings, especially:

- `xcodebuild -list -workspace mobile/crystal-lattice-control-rn/ios/CrystalLatticeControlRN.xcworkspace`
- `xcodebuild -showBuildSettings -workspace mobile/crystal-lattice-control-rn/ios/CrystalLatticeControlRN.xcworkspace -scheme CrystalLatticeControlRN -configuration Release`
- `plutil -p mobile/crystal-lattice-control-rn/ios/CrystalLatticeControlRN/Info.plist`
- `plutil -p mobile/crystal-lattice-control-rn/ios/CrystalLatticeControlRN/PrivacyInfo.xcprivacy`

Do not assume App Store Connect state from local project files. Apple portal/account checks must be confirmed by someone with account access.

## Execution plan

Added during completion on 2026-06-17.

Approach: code-visible audit with an explicit question list for account/portal facts that cannot be proven from the repository.

1. Read this task, the parent task, and the explicitly referenced mobile component testing task for overlap context.
2. Inspect current mobile app package metadata, iOS build settings, `Info.plist`, privacy manifest, app icon asset set, and existing workflows.
3. Locate the landing page and privacy policy route, then verify which documented URLs are live.
4. Re-run lightweight mobile verification commands that affect readiness status.
5. Record findings, readiness matrix, and questions for the product/account owner.

## Audit Findings

Added during completion on 2026-06-17.

### Confirmed From Code

- App target path: `mobile/crystal-lattice-control-rn`.
- iOS workspace: `mobile/crystal-lattice-control-rn/ios/CrystalLatticeControlRN.xcworkspace`.
- iOS scheme: `CrystalLatticeControlRN`, confirmed with `xcodebuild -list`.
- Bundle ID: `com.dynamicprogrammingsolutions.crystallatticecontrolrn`, from Release build settings.
- Apple team ID in the Xcode project: `73Q43R2PD4`, from Release build settings.
- Release version/build in the Xcode project: `MARKETING_VERSION = 1.0`, `CURRENT_PROJECT_VERSION = 1`.
- Release iOS deployment target: `IPHONEOS_DEPLOYMENT_TARGET = 16.6`.
- App display name: `Crystal Lattice Control`, from `app.json` and `Info.plist`.
- Deep link scheme present: `crystal-lattice`, via `CFBundleURLTypes`.
- ATS allows local networking but not arbitrary loads.
- Bonjour service declaration exists for `_http._tcp`.
- Camera, photo library, photo-library-add, and local-network usage strings exist.
- `NSLocationWhenInUseUsageDescription` exists but is an empty string; this needs cleanup in task `040`.
- Privacy manifest exists and declares file timestamp, user defaults, and system boot time accessed API reasons; collected data types are empty and tracking is false.
- Landing site exists under `landing_page`.
- Privacy route exists as `landing_page/src/pages/privacy.astro` backed by `landing_page/src/content/markdown/privacy.md`.
- Mobile landing page exists as `/mobile`, backed by `landing_page/src/content/pages/mobile.yaml`.
- Production landing defaults are `https://crystallattice.dev` and `https://docs.crystallattice.dev`, but the production domain did not resolve from this environment on 2026-06-17.
- Test landing privacy URL `https://crystallattice.dev.dynamicprogrammingsolutions.com/privacy` returned HTTP 200 on 2026-06-17.
- Existing static-site deploy workflow exists: `.github/workflows/deploy-static-sites.yml`.
- No mobile iOS TestFlight GitHub Actions workflow was found.
- No `fastlane/`, `Fastfile`, `Appfile`, `Matchfile`, EAS, Codemagic, or Bitrise configuration was found under `mobile/crystal-lattice-control-rn`.
- App icon asset set is still missing PNG files. `AppIcon.appiconset` contains only `Contents.json`.
- Stale sample naming remains:
  - `mobile/crystal-lattice-control-rn/package.json` uses `"name": "BonjourExampleRN"`.
  - Xcode Release build settings use `PRODUCT_NAME = BonjourExampleRN`.
  - The mobile README still contains Bonjour sample wording.

### Verification Commands

Run from `mobile/crystal-lattice-control-rn` on 2026-06-17:

```bash
npm run tsc
npm test -- --runInBand
npm run lint
```

Results:

- `npm run tsc`: passed.
- `npm test -- --runInBand`: passed; 13 suites, 34 tests.
- `npm run lint`: not run successfully because ESLint could not find a configuration file. This is a tooling/config gap, not a lint-finding result.

Overlap note:

- `tasks/20260615-mobile-component-integration-tests/020-react-native-testing-library-setup.md` completed the Jest/native-module mock part of `tasks/20260614-ios-testflight-github-fastlane/020-fix-mobile-verification.md`.
- In the current checkout, the old splash/logo TypeScript issue is also resolved: `AnimatedSplashScreen` now calls `<AppLogo width={108} height={108} />`.

## Readiness Matrix

Added during completion on 2026-06-17.

| Area | Status | Evidence / Next action |
| --- | --- | --- |
| Native iOS project exists | ready | Workspace and scheme are present; `xcodebuild -list` finds `CrystalLatticeControlRN`. |
| Bundle identifier | ready pending Apple portal confirmation | Code uses `com.dynamicprogrammingsolutions.crystallatticecontrolrn`; confirm it exists or can be created in Apple Developer/App Store Connect. |
| Apple team | needs Apple account action | Code uses team ID `73Q43R2PD4`; confirm this is the intended production team/legal entity. |
| App name/display name | mostly ready | User-facing display name is `Crystal Lattice Control`; package/Xcode product name still need stale `BonjourExampleRN` cleanup. |
| Version/build | needs code/deployment decision | Current values are `1.0` / `1`; define build-number increment strategy for fastlane/GitHub Actions. |
| App icon | needs code change | iOS app icon asset set has only `Contents.json`; generate PNGs from the existing SVG icon. |
| Privacy manifest | ready pending compliance review | `PrivacyInfo.xcprivacy` exists; validate against final SDK/app behavior in task `050`. |
| Permission strings | needs code change | Empty `NSLocationWhenInUseUsageDescription`; remove or fill if actually needed. |
| Local verification | mostly ready | `tsc` and Jest pass; lint script is blocked by missing ESLint config. |
| Landing page source | ready | `landing_page` exists with `/mobile`, `/privacy`, and `/terms`. |
| Public privacy URL | needs external confirmation | Test privacy URL is live; production `crystallattice.dev` did not resolve from this environment. |
| Static-site deployment | ready for landing/docs path | `.github/workflows/deploy-static-sites.yml` exists. |
| Mobile TestFlight CI/CD | needs code change | No fastlane or mobile iOS GitHub Actions workflow yet. |
| App Store Connect registration | needs Apple account action | Cannot be confirmed from repo. |
| TestFlight release scope | needs product decision | Internal-only first vs external testers is not encoded in repo. |
| Reviewer/demo backend access | needs product/external environment decision | App requires local/bridge/cloud server access for meaningful review. |

## Questions For The User / Account Owner

Added during completion on 2026-06-17.

1. Is Apple team ID `73Q43R2PD4` the intended production Apple Developer Program team for this app?
2. What is the legal entity/account owner name that should appear in App Store Connect?
3. Is `com.dynamicprogrammingsolutions.crystallatticecontrolrn` already registered as an App ID / bundle ID in Apple Developer, or should the deployment work create/register it?
4. Has an App Store Connect app record already been created for this bundle ID?
5. Should the App Store Connect app name be exactly `Crystal Lattice Control`?
6. What SKU should be used in App Store Connect? A reasonable default would be something like `crystal-lattice-control-ios`, but this should be owner-approved.
7. What primary language should be used? Code suggests English, but App Store Connect needs an explicit choice.
8. What primary category should be used? Candidate categories might be Developer Tools, Productivity, or Utilities, but this is a product decision.
9. Should the first TestFlight milestone be internal testers only, or should external TestFlight review be prepared immediately?
10. Which URL should be used for App Store Connect privacy policy?
    - Test/staging candidate: `https://crystallattice.dev.dynamicprogrammingsolutions.com/privacy`
    - Intended production candidate from repo docs: `https://crystallattice.dev/privacy`
11. Should `https://crystallattice.dev` be made live before TestFlight registration, or is the test/staging domain acceptable for the first internal TestFlight?
12. What support URL should be used? Candidate options are the landing page, `/mobile`, GitHub Issues, or a dedicated support page.
13. What marketing URL should be used? Candidate options are `https://crystallattice.dev/mobile` or the main landing page.
14. Is there a public contact email for TestFlight feedback and App Review contact, or should feedback route through GitHub Issues?
15. For external TestFlight review, what demo backend/bridge/cloud connection should Apple reviewers use?
16. Should the App Store version start at `1.0`, or should it be a lower pre-release marketing version for early TestFlight?
17. Do we want to keep iOS deployment target `16.6`, or lower it to support older devices?

## Completion Notes

Added during completion on 2026-06-17.

The code-visible audit portion of this task is complete. The remaining unchecked items require answers from the Apple/account/product owner rather than more repository inspection. Keep this task open until those answers are provided, then update the checklist and mark the parent item complete.
