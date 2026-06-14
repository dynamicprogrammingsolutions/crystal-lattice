# Preflight Audit And Deployment Readiness

Audit the iOS app, Apple account assumptions, public URLs, and repo readiness before changing deployment automation.

## Requirements checklist

- [ ] Confirm the Apple Developer Program team, legal entity/account owner, and whether team ID `73Q43R2PD4` is the intended production team.
- [ ] Confirm the app name, bundle ID, SKU, primary language, category, and whether the first TestFlight release is internal-only or external too.
- [ ] Confirm that `com.dynamicprogrammingsolutions.crystallatticecontrolrn` is registered or ready to register in Certificates, Identifiers & Profiles/App Store Connect.
- [ ] Confirm the landing page URL and the privacy policy URL or anchor on that landing page.
- [ ] Produce a readiness matrix with `ready`, `needs code change`, `needs Apple account action`, and `needs external asset/content` statuses.

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
