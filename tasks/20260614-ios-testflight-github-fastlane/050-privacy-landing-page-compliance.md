# Validate Privacy, Landing Page, And Compliance Inputs

Confirm the public landing page and privacy policy are suitable for App Store Connect, and prepare privacy/compliance answers from actual app behavior.

## Requirements checklist

- [ ] Locate and verify the landing page source and public deployed URL.
- [ ] Verify the privacy policy is part of the landing page and has a stable URL or anchor suitable for App Store Connect.
- [ ] Audit actual app data flows and permissions against App Store privacy questions.
- [ ] Revalidate `PrivacyInfo.xcprivacy` against current app code, React Native SDKs, and native dependencies.
- [ ] Prepare a short privacy/compliance answer sheet for App Store Connect.

Parent Task: tasks/20260614-ios-testflight-github-fastlane/000-main.md
Depends On: tasks/20260614-ios-testflight-github-fastlane/010-preflight-audit.md
Depends On: tasks/20260614-ios-testflight-github-fastlane/040-ios-identity-metadata.md

## Known Starting State

The user stated:

- The app icon exists as SVG and is used by the landing page and splash screen.
- The privacy policy is part of the landing page.

The app currently includes capabilities and dependencies that should be considered in privacy answers:

- Local network discovery via Bonjour/mDNS (`react-native-zeroconf`, `_http._tcp`, local network permission).
- Manual server connection by host/port.
- Bridge and cloud connection flows, including pairing/token-like connection records.
- Saved connections through local storage/cache.
- Sessions/messages UI and cached messages.
- Camera/photo/document attachment flows.
- Photo saving/export/sharing flows.

The privacy manifest exists at:

- `mobile/crystal-lattice-control-rn/ios/CrystalLatticeControlRN/PrivacyInfo.xcprivacy`

Previously observed manifest entries:

- `NSPrivacyAccessedAPICategoryFileTimestamp` with reasons `C617.1` and `3B52.1`
- `NSPrivacyAccessedAPICategoryUserDefaults` with reason `CA92.1`
- `NSPrivacyAccessedAPICategorySystemBootTime` with reason `35F9.1`
- `NSPrivacyCollectedDataTypes` empty
- `NSPrivacyTracking` false

## Acceptance Criteria

- Public privacy policy URL is confirmed and usable in App Store Connect.
- App Store privacy answers are based on actual app behavior, not guesses.
- Any mismatch between `PrivacyInfo.xcprivacy`, SDK manifests, and app behavior is fixed or clearly documented.
- If the app collects/transmits user content to user-configured servers, bridge, or cloud endpoints, the App Store privacy notes explain this accurately.
